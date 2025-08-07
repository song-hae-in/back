from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def generate_question():
    client = OpenAI(
        base_url="https://api.aimlapi.com/v1",
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    response = client.chat.completions.create(
        model="Qwen/Qwen3-235B-A22B-fp8-tput",
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 간호사 면접 준비를 도와주는 AI야. "
                    "사용자가 입력한 주제에 대해 실제 면접에서 나올 수 있는 간호사 면접 질문을 생성하고, "
                    "그 질문에 대한 모범적인 서술형 답변도 함께 생성해줘. "
                    "출력 형식은 다음과 같이 해:\n\n"
                    "면접 질문: (생성된 질문)\n"
                    "생성한 답: (해당 질문에 대한 서술형 답변)\n\n"
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
        question = ""
        answer = ""
        
        for line in lines:
            if line.startswith("면접 질문:"):
                question = line.replace("면접 질문:", "").strip()
            elif line.startswith("생성한 답:"):
                answer = line.replace("생성한 답:", "").strip()

        questionList = [
            {   # "interviewID": 0,
                "question": question,
                "answer": answer,
                "type": "간호사"
            }
        ]
        
    except Exception as e:
        print(f"파싱 오류: {e}")
        questionList = [
            {   # "interviewID": 0,
                "question": "Parsing failed",
                "answer": "Parsing failed",
                "type": "None"
            }
        ]

    print(f"Parsed Question List: {questionList}")
    return questionList
