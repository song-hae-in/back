import random

def generate_question():
    questions = [
        "기본간호학에서 가장 중요한 개념은 무엇인가요?",
        "환자와의 의사소통에서 주의할 점은?",
        "감염 예방을 위한 간호사의 역할은?",
        "환자의 안전을 보장하기 위한 기본 간호 기술은 무엇인가요?"
    ]
    return random.choice(questions)
