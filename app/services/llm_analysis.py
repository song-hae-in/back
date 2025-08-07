from openai import OpenAI
import re
import os
from dotenv import load_dotenv
import random
from datetime import datetime
from app import db
from app.models import Interview

load_dotenv()

def analysisByLLM(user_id):
    print("[Analysis Start] analyzing...")
    """
    1) 해당 유저의 모든 Interview 레코드 조회
    2) LLM에 한번에 보내 분석
    3) 질문별 analysis, score를 각각의 Interview 객체에 저장
    4) 전체 summary는 가장 첫 레코드(summary 필드가 있다면) 혹은 별도 처리
    """
    # 1) OpenAI 클라이언트 초기화
    client = OpenAI(
        base_url="https://api.aimlapi.com/v1",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # 2) 모든 인터뷰 불러오기(시간순)
    interviews = (Interview.query
                       .filter_by(user_id=user_id)
                       .order_by(Interview.timestamp)
                       .all())
    if not interviews:
        return None

    # 3) 프롬프트 생성 (질문/유저답변/LLM답변)
    prompt_parts = []
    for idx, itv in enumerate(interviews, start=1):
        prompt_parts.append(
            f"---\n"
            f"질문 {idx}: {itv.question}\n"
            f"사용자 답변: {itv.useranswer}\n"
            f"LLM 이전 답변: {itv.LLM_gen_answer}\n"
        )
    combined = "\n".join(prompt_parts)

    system_prompt = (
        "너는 간호사 면접 준비를 도와주는 AI야. "
        "아래는 사용자가 진행한 모든 면접 질문과 답변이야:\n\n"
        f"{combined}\n\n"
        "각 질문별로 다음 형식으로 분석 결과를 출력해줘:\n"
        "{analysis} : (질문별 분석 내용)\n"
        "{score} : (0~100 사이 점수)\n"
        "그리고 마지막에 전체 면접에 대한 {summary}를 작성해줘.\n"
        "**<think> 같은 내부 지시는 절대 출력하지 말고**, 전부 한국어로 작성해."
    )

    # 4) Chat Completion 호출
    response = client.chat.completions.create(
        model="Qwen/Qwen3-235B-A22B-fp8-tput",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": "전체 인터뷰 분석해주세요."}
        ],
        temperature=0.7,
        top_p=0.7,
        frequency_penalty=1,
        max_tokens=2048
    )
    
    message = response.choices[0].message.content
    # <think> 태그 제거
    if "</think>" in message:
        message = message.split("</think>", 1)[1]
    # 줄 단위로 분리하고 공백 줄 제거
    print("[LLM Response]", message)
    
    # 4) 정규식으로 {analysis} 와 {score} 값 모두 뽑아내기
    #    (?s) DOTALL: 줄바꿈 포함 매칭
    analysis_pattern = re.compile(r"\{analysis\}\s*:\s*(.+?)(?=\{score\}|\Z)", re.IGNORECASE | re.DOTALL)
    score_pattern    = re.compile(r"\{score\}\s*:\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
    summary_pattern  = re.compile(r"\{summary\}\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)

    analyses = analysis_pattern.findall(message)
    scores   = score_pattern.findall(message)
    summary_matches = summary_pattern.findall(message)
    summary = summary_matches[-1].strip() if summary_matches else ""

    # 5) DB에 저장
    for itv, anal, sc in zip(interviews, analyses, scores):
        itv.analysis = anal.strip()
        try:
            itv.score = float(sc)
        except ValueError:
            itv.score = None

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