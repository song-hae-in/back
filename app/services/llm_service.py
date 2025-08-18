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
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content":
             """
너는 서울대학교병원 수간호사 면접관이야. 나는 신규 간호사의 뛰어난 문제 해결 능력과 간호사로써 가져야하는 질병에대한 이해 응급상황대처 능력을 중요하게 생각해.\n\n

간호사 채용을 위해 다음 세 가지 유형의 질문을 섞어 총 3개의 질문을 해 줘.\n
1.  **전문지식/상황 대처 능력 평가 질문:** 중환자실에서 실제로 발생할 수 있는 응급 상황에 대한 지식과 대처 능력을 평가하는 질문. **단 구술하듯이 질문하가**\n
2.  **인성/대인관계 능력 평가 질문:** 환자나 보호자와의 갈등, 또는 동료와의 협력에 대한 지원자의 태도를 묻는 질문.\n
3.  **지원 동기/가치관 평가 질문:** 병원 명을 언급하지는 말고 직무에 대한 이해도, 그리고 간호사로서의 가치관을 확인하는 질문.\n\n

각 질문에 대한 너가 생각하는 모범 답안을 함께 작성해. 모범 답안은 다음과 같은 원칙을 따라야 해:\n
- **전문지식 질문에 대한 답:** 관련 의학 지식, 간호 프로토콜 및 구체적인 행동 계획이 포함되어야 해.\n
- **인성/상황 질문에 대한 답:** 상황, 과제, 행동, 결과를 활용하여 구체적인 경험을 바탕으로 지원자가 구술 하듯 설명하고, 지원자의 책임감과 윤리 의식이 드러나도록 작성해 줘.\n

출력 형식은 다음과 같아야 해:"""
             "면접 질문 1: ...\n모범 답 1: ...\n\n면접 질문 2: ...\n모범 답 2: ...\n\n면접 질문 3: ...\n모범 답 3: ...\n\n"
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
            elif line.startswith("모범 답"):
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
