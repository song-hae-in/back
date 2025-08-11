from openai import OpenAI
import re
import os
from dotenv import load_dotenv
import random
from datetime import datetime
from app import db
from app.models import Interview

load_dotenv()

def analysisByLLM(user_id, session_id=None):
    print(f"[Analysis Start] analyzing user_id: {user_id}, session_id: {session_id}")
    """
    1) 해당 유저의 특정 세션 또는 모든 Interview 레코드 조회
    2) LLM에 한번에 보내 분석
    3) 질문별 analysis, score를 각각의 Interview 객체에 저장
    4) 전체 summary 반환
    """
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.getenv("GEMINI_API_KEY"),
    )

    # 2) 인터뷰 불러오기 (세션별 또는 전체)
    if session_id:
        interviews = (Interview.query
                           .filter_by(user_id=user_id, session_id=session_id)
                           .order_by(Interview.question_order)
                           .all())
        print(f"[Analysis] Found {len(interviews)} interviews for session {session_id}")
    else:
        interviews = (Interview.query
                           .filter_by(user_id=user_id)
                           .order_by(Interview.timestamp)
                           .all())
        print(f"[Analysis] Found {len(interviews)} total interviews")
    
    if not interviews:
        return "분석할 인터뷰 데이터가 없습니다."

    # 3) 프롬프트 생성 (질문/유저답변/LLM답변)
    prompt_parts = []
    for idx, itv in enumerate(interviews, start=1):
        prompt_parts.append(
            f"---\n"
            f"질문 {idx}: {itv.question}\n"
            # f"사용자 답변: {itv.useranswer}\n"
            f"사용자 답변: {itv.LLM_gen_answer}\n"
            f"LLM 이전 답변: {itv.LLM_gen_answer}\n"
        )
    combined = "\n".join(prompt_parts)

    system_prompt = (
        "너는 analyst야. "
        "아래는 면접자가 받은 질문과 그에 대한 답변이야.:\n\n"
        f"{combined}\n\n"
        "각 답변에 대해 다음과 같은 형식으로 분석 결과를 제공해줘:\n"
    """question": "최근 사용한 기술 스택은?",
    "useranswer": "최근에는 React와 Flask를 이용해서 예약 시스템을 개발했습니다. 프론트엔드는 React로 구성했고, Flask로 API 서버를 구축했습니다. MongoDB를 데이터베이스로 사용했습니다.",
    "LLM gen answer": "기술 스택에 대한 설명은 명확하나, 기술을 선택한 이유나 해결한 문제에 대한 언급이 없어 실무 역량이 충분히 드러나지 않습니다.",
    "analysis": "분석내용: 말은 또렷하고 전달력은 좋았음. 다만 내용은 나열식으로 기술되어 면접관의 관심을 끌기엔 부족했음.\n미흡한점: 단순한 기술 나열. 해당 기술이 사용된 배경과 결과가 빠짐.\n개선점: 기술 선택 이유와 구현 성과 또는 문제 해결 경험을 추가.\n수정된 답변: 최근에는 React와 Flask를 사용해 병원 예약 시스템을 개발했습니다. 프론트엔드는 사용자 친화적인 UI를 구현하기 위해 React를, 백엔드는 빠른 REST API 개발을 위해 Flask를 사용했습니다. 인증은 JWT를, DB는 MongoDB로 구성해 빠른 검색이 가능하도록 최적화했습니다.",
    "score": 78"""
        "그리고 마지막에 전체 면접에 대한 {summary}를 작성해줘.\n"
        "**<think> 같은 내부 지시는 절대 출력하지 말고**, 전부 한국어로 작성해."
    )

    # 4) Chat Completion 호출
    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": "전체 인터뷰 분석해주세요."}
        ],
        temperature=0.7,
        top_p=0.9,
    )
    
    message = response.choices[0].message.content
    # <think> 태그 제거
    if "</think>" in message:
        message = message.split("</think>", 1)[1]
    # 줄 단위로 분리하고 공백 줄 제거
    print("[LLM Response]", message)
    
    # 4) 정규식으로 {analysis} 와 {score} 값 모두 뽑아내기
    #    (?s) DOTALL: 줄바꿈 포함 매칭
    #    두 가지 패턴 모두 지원: {analysis} : 내용 또는 analysis : 내용
    analysis_pattern = re.compile(r"(?:\{analysis\}|analysis)\s*:\s*(.+?)(?=(?:\{score\}|score)\s*:|$)", re.IGNORECASE | re.DOTALL)
    score_pattern    = re.compile(r"(?:\{score\}|score)\s*:\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
    summary_pattern  = re.compile(r"(?:\{summary\}|summary)\s*:\s*(.+?)(?=\n\n|\Z)", re.IGNORECASE | re.DOTALL)

    analyses = analysis_pattern.findall(message)
    scores   = score_pattern.findall(message)
    summary_matches = summary_pattern.findall(message)
    summary = summary_matches[-1].strip() if summary_matches else ""
    
    print(f"[Parsing Results] Found {len(analyses)} analyses, {len(scores)} scores")
    print(f"[Analyses] {analyses}")
    print(f"[Scores] {scores}")
    print(f"[Summary] {summary}")

    # 5) DB에 저장 - 길이 맞춤을 위한 안전 처리
    min_length = min(len(interviews), len(analyses), len(scores))
    print(f"[DB Save] Processing {min_length} interviews")
    
    for i in range(min_length):
        itv = interviews[i]
        anal = analyses[i] if i < len(analyses) else "분석 결과 없음"
        sc = scores[i] if i < len(scores) else "0"
        
        itv.analysis = anal.strip()
        try:
            itv.score = float(sc)
        except ValueError:
            itv.score = 0.0
            print(f"[Warning] Invalid score format for interview {i}: {sc}")
    
    # 분석되지 않은 인터뷰들에 대한 기본값 설정
    for i in range(min_length, len(interviews)):
        interviews[i].analysis = "분석 결과 없음 (기본값)"
        interviews[i].score = 0.0

    # summary 필드가 모델에 있다면 첫 레코드에 저장
    if hasattr(interviews[0], 'summary'):
        interviews[0].summary = summary

    db.session.commit()
    return summary

# def score_answer(answer):
#     return round(random.uniform(60, 100), 2)

# def test_analysisByLLM(answer):
#     data = {"LLM_gen_answer": "This is a generated answer based on the user's input.",
#             "analysis": "The answer is well-structured and addresses the question effectively."}
#     return data