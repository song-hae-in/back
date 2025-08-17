# app/services/analysis_api.py
# -*- coding: utf-8 -*-
"""
면접 분석 통합 파일
- LLM 분석(항목별 analysis/score + 전체 summary + overall scores)
- DB 저장
- 프론트엔드가 바로 쓰는 응답 포맷(InterviewList, summary, scores)
- GET /api/interview/analysis?session_id=...  (JWT 필요)
"""

import os
import re
import json
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from openai import OpenAI

from app import db
from app.models import Interview

load_dotenv()

bp = Blueprint("analysis", __name__)

# -----------------------------
# 내부 유틸
# -----------------------------
def _strip_think(text: str) -> str:
    """일부 모델이 실수로 넣는 </think> 이전 텍스트를 제거"""
    if "</think>" in text:
        return text.split("</think>", 1)[-1]
    return text


def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(val)
    except Exception:
        return default


def _build_front_payload(interviews: List[Interview]) -> List[Dict[str, Any]]:
    """
    프론트가 바로 쓰는 InterviewList 아이템으로 변환
    - question
    - useranswer
    - "LLM gen answer"  (현 프론트 호환: 공백 포함 키 유지)
    - analysis
    - score
    - video (video 또는 video_url 중 있는 것)
    """
    out: List[Dict[str, Any]] = []
    for itv in interviews:
        out.append({
            "question": getattr(itv, "question", "") or "",
            "useranswer": getattr(itv, "useranswer", "") or "",
            "LLM gen answer": getattr(itv, "LLM_gen_answer", "") or "",
            "analysis": getattr(itv, "analysis", "") or "",
            "score": getattr(itv, "score", 0) or 0,
            "video": getattr(itv, "video", None) or getattr(itv, "video_url", None)
        })
    return out


# -----------------------------
# 핵심 로직
# -----------------------------
def analysisByLLM(user_id: int, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    1) 특정 세션 또는 전체 인터뷰 로드
    2) LLM 호출 (JSON 스키마 강제)
    3) 항목별 analysis/score 저장, summary/overall_scores 반환
    4) 프론트 포맷으로 딕셔너리 반환: { InterviewList, summary, scores }
    """
    print(f"[Analysis Start] analyzing user_id={user_id}, session_id={session_id}")

    # 1) 인터뷰 로드
    if session_id:
        interviews = (
            Interview.query
            .filter_by(user_id=user_id, session_id=session_id)
            .order_by(Interview.question_order)
            .all()
        )
        print(f"[Analysis] Found {len(interviews)} interviews for session {session_id}")
    else:
        interviews = (
            Interview.query
            .filter_by(user_id=user_id)
            .order_by(Interview.timestamp)
            .all()
        )
        print(f"[Analysis] Found {len(interviews)} total interviews")

    if not interviews:
        return {
            "InterviewList": [],
            "summary": "분석할 인터뷰 데이터가 없습니다.",
            "scores": {
                "구체성": 0, "논리성": 0, "적합성": 0, "표현력": 0, "전문성": 0
            }
        }

    # 2) LLM 프롬프트 구성 (JSON 스키마 강제)
    payload_items = []
    for idx, itv in enumerate(interviews, start=1):
        payload_items.append({
            "index": idx,
            "question": getattr(itv, "question", "") or "",
            "useranswer": getattr(itv, "useranswer", "") or "",
            "llm_gen_answer": getattr(itv, "LLM_gen_answer", "") or ""
        })

    system_prompt = (
        "너는 면접 분석가야. 아래의 질문/사용자답변/이전 LLM답변을 바탕으로 각 항목의 분석과 점수를 작성해."
        " 반드시 **유효한 JSON만** 출력해. JSON 외 텍스트 절대 금지."
    )

    format_instructions = {
        "type": "object",
        "required": ["items", "summary", "overall_scores"],
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "index", "question", "useranswer", "llm_gen_answer", "analysis", "score"
                    ],
                    "properties": {
                        "index": {"type": "integer"},
                        "question": {"type": "string"},
                        "useranswer": {"type": "string"},
                        "llm_gen_answer": {"type": "string"},
                        "analysis": {"type": "string"},
                        "score": {"type": "number", "minimum": 0, "maximum": 100}
                    }
                }
            },
            "summary": {"type": "string"},
            "overall_scores": {
                "type": "object",
                "required": ["구체성", "논리성", "적합성", "표현력", "전문성"],
                "properties": {
                    "구체성": {"type": "number", "minimum": 0, "maximum": 100},
                    "논리성": {"type": "number", "minimum": 0, "maximum": 100},
                    "적합성": {"type": "number", "minimum": 0, "maximum": 100},
                    "표현력": {"type": "number", "minimum": 0, "maximum": 100},
                    "전문성": {"type": "number", "minimum": 0, "maximum": 100}
                }
            }
        }
    }

    user_prompt = (
        "입력 데이터:\n"
        + json.dumps({"items": payload_items}, ensure_ascii=False, indent=2)
        + "\n\n"
        "요구사항:\n"
        "- 각 항목에 대해 'analysis'(한국어)와 'score'(0~100)를 작성.\n"
        "- 전체 총평은 'summary'에 작성.\n"
        "- 전반 평가를 5개 지표(구체성/논리성/적합성/표현력/전문성)로 0~100 점수화하여 'overall_scores'에 넣을 것.\n"
        "- 출력은 아래 JSON 스키마를 반드시 따를 것. 다른 텍스트 금지.\n"
        + json.dumps(format_instructions, ensure_ascii=False)
    )

    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.getenv("GEMINI_API_KEY"),
    )

    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=0.4,
        top_p=0.95,
    )

    raw = response.choices[0].message.content or ""
    cleaned = _strip_think(raw).strip()

    # 3) JSON 파싱
    parsed = None
    try:
        parsed = json.loads(cleaned)
    except Exception:
        # ```json ... ``` 형태일 경우
        codeblock = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL | re.IGNORECASE)
        if codeblock:
            try:
                parsed = json.loads(codeblock.group(1))
            except Exception:
                parsed = None

    if parsed is None:
        # ---------- 레거시 백업(정규식) ----------
        print("[Warn] JSON 파싱 실패 → 레거시 정규식 파싱 시도")
        analysis_pattern = re.compile(
            r"(?:\{analysis\}|analysis)\s*:\s*(.+?)(?=(?:\{score\}|score)\s*:|$)",
            re.IGNORECASE | re.DOTALL
        )
        score_pattern = re.compile(
            r"(?:\{score\}|score)\s*:\s*([0-9]+(?:\.[0-9]+)?)",
            re.IGNORECASE
        )
        summary_pattern = re.compile(
            r"(?:\{summary\}|summary)\s*:\s*(.+?)(?=\n\n|\Z)",
            re.IGNORECASE | re.DOTALL
        )

        analyses = [a.strip() for a in analysis_pattern.findall(cleaned)]
        scores = [s.strip() for s in score_pattern.findall(cleaned)]
        summary_matches = summary_pattern.findall(cleaned)
        summary_text = summary_matches[-1].strip() if summary_matches else ""

        use_n = min(len(interviews), len(analyses), len(scores))
        print(f"[Legacy Parsing] analyses={len(analyses)}, scores={len(scores)}, use={use_n}")

        for i in range(use_n):
            itv = interviews[i]
            itv.analysis = analyses[i]
            itv.score = _safe_float(scores[i], 0.0)

        for i in range(use_n, len(interviews)):
            interviews[i].analysis = "분석 결과 없음 (기본값)"
            interviews[i].score = 0.0

        db.session.commit()

        # overall_scores 대체값(평균점수로 채움)
        avg = 0.0
        if interviews:
            vals = [_safe_float(getattr(itv, "score", 0), 0.0) for itv in interviews]
            avg = sum(vals) / max(1, len(vals))

        fallback_scores = {
            "구체성": round(avg, 1),
            "논리성": round(avg, 1),
            "적합성": round(avg, 1),
            "표현력": round(avg, 1),
            "전문성": round(avg, 1)
        }

        return {
            "InterviewList": _build_front_payload(interviews),
            "summary": summary_text,
            "scores": fallback_scores
        }

    # ---------- JSON 파싱 성공 ----------
    items = parsed.get("items", [])
    summary_text = parsed.get("summary", "")
    overall_scores = parsed.get("overall_scores", {})

    save_n = min(len(interviews), len(items))
    print(f"[JSON Parsed] items={len(items)}, interviews={len(interviews)}, save_count={save_n}")

    for i in range(save_n):
        itv = interviews[i]
        item = items[i]
        itv.analysis = (item.get("analysis") or "").strip()
        itv.score = _safe_float(item.get("score", 0), 0.0)

    for i in range(save_n, len(interviews)):
        interviews[i].analysis = "분석 결과 없음 (기본값)"
        interviews[i].score = 0.0

    # summary를 DB 칼럼에 저장하고 싶다면 여기서 처리 (모델에 summary 필드가 있을 때만)
    # if hasattr(interviews[0], "summary"):
    #     interviews[0].summary = summary_text

    db.session.commit()

    return {
        "InterviewList": _build_front_payload(interviews[:len(items)]),
        "summary": summary_text,
        "scores": {
            # 키가 없거나 숫자가 아니어도 안전하게 0 처리
            "구체성": _safe_float(overall_scores.get("구체성", 0), 0.0),
            "논리성": _safe_float(overall_scores.get("논리성", 0), 0.0),
            "적합성": _safe_float(overall_scores.get("적합성", 0), 0.0),
            "표현력": _safe_float(overall_scores.get("표현력", 0), 0.0),
            "전문성": _safe_float(overall_scores.get("전문성", 0), 0.0),
        }
    }


# -----------------------------
# API 엔드포인트
# -----------------------------
@bp.route("/api/interview/analysis", methods=["GET"])
@jwt_required()
def api_interview_analysis():
    """
    프런트 호출 포인트
    - Query: session_id (옵션)
    - Response:
      {
        "success": true,
        "data": {
          "InterviewList": [...],
          "summary": "...",
          "scores": {
              "구체성": 80, "논리성": 65, "적합성": 75}
        }
      }
    """
    user_id = get_jwt_identity()
    session_id = request.args.get("session_id") or request.args.get("sessionId")

    try:
        data = analysisByLLM(user_id=user_id, session_id=session_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print("[ERROR] analysis failed:", e)
        return jsonify({"success": False, "message": str(e)}), 500
