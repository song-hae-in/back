import random

def score_answer(answer):
    return round(random.uniform(60, 100), 2)

def analysisByLLM(answer):
    data = {"LLM_gen_answer": "This is a generated answer based on the user's input.",
            "analysis": "The answer is well-structured and addresses the question effectively."}
    return data