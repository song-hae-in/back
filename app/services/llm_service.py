from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def generate_question():
    client = OpenAI(
        # base_url="https://api.aimlapi.com/v1",
        # api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    response = client.chat.completions.create(
        # model="Qwen/Qwen3-235B-A22B-fp8-tput",
        model="qwen-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 간호사 면접 준비를 도와주는 AI야. "
                    "사용자가 입력한 주제에 대해 실제 면접에서 나올 수 있는 간호사 면접 질문을 3개 생성하고, "
                    "각 질문에 대한 모범적인 서술형 답변도 함께 생성해줘. "
                    "출력 형식은 다음과 같이 해:\n\n"
                    "면접 질문 1: (첫 번째 질문)\n"
                    "생성한 답 1: (첫 번째 질문에 대한 서술형 답변)\n\n"
                    "면접 질문 2: (두 번째 질문)\n"
                    "생성한 답 2: (두 번째 질문에 대한 서술형 답변)\n\n"
                    "면접 질문 3: (세 번째 질문)\n"
                    "생성한 답 3: (세 번째 질문에 대한 서술형 답변)\n\n"
                    "**<think> 같은 내부 지시는 절대 출력하지 말고**, "
                    "전부 한국어로 출력해."
                )
            },
            {
                "role": "user",
                "content": "주제: 성인간호학"
            }
        ],
        temperature=0.7,
        top_p=0.7,
        frequency_penalty=1,
        max_tokens=2048
    )

    message = response.choices[0].message.content
 
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
