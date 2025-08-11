from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def generate_question():
    client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.getenv("GEMINI_API_KEY"),
    )

    resp = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role": "system", "content":
             "너는 간호사 면접관이야. 간호사 채용을 위해 전문지식과 인성을 평가할 수 질문을 섞어서 총 3개를 해 , "
             "각 질문에 대한 너가 생각하는 답을 함께 작성해. 출력 형식은 다음과 같아야 해:\n\n"
             "면접 질문 1: ...\n생성한 답 1: ...\n\n면접 질문 2: ...\n생성한 답 2: ...\n\n면접 질문 3: ...\n생성한 답 3: ...\n\n"
             "<think> 같은 내부 지시는 절대 출력하지 말고 전부 한국어로 출력해."},
            {"role": "user", "content": "주제: .. "}
        ],
        temperature=0.7, top_p=0.9,
    )

    message = resp.choices[0].message.content
 
    message = message.split("</think>")[1] if "</think>" in message else message

    try:
        lines = message.strip().split('\n')
        questions = []
        answers = []
        
        # 3개의 질문과 답변을 파싱
        for line in lines:
            # 면접 질문 1, 2, 3 패턴 매칭
            if line.startswith("면접 질문"):
                question = line.split(":", 1)[1].strip() if ":" in line else ""
                questions.append(question)
            # 생성한 답 1, 2, 3 패턴 매칭
            elif line.startswith("생성한 답"):
                answer = line.split(":", 1)[1].strip() if ":" in line else ""
                answers.append(answer)

        # 질문과 답변이 3개씩 있는지 확인하고 questionList 생성
        questionList = []
        for i in range(min(len(questions), len(answers), 3)):  # 최대 3개까지만
            questionList.append({
                "question": questions[i],
                "answer": answers[i],
                "type": "간호사"
            })
        
        # 만약 3개 미만이면 기본값으로 채우기
        while len(questionList) < 3:
            questionList.append({
                "question": f"질문 {len(questionList) + 1} 생성 실패",
                "answer": "답변 생성 실패",
                "type": "간호사"
            })
        
    except Exception as e:
        print(f"파싱 오류: {e}")
        questionList = []
        for i in range(3):
            questionList.append({
                "question": f"Parsing failed - Question {i + 1}",
                "answer": f"Parsing failed - Answer {i + 1}",
                "type": "None"
            })

    print(f"Parsed Question List: {questionList}")
    return questionList
