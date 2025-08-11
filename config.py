from dotenv import load_dotenv
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database', 'interview.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    KAKAO_CLIENT_ID = os.getenv('KAKAO_CLIENT_ID')
    KAKAO_CLIENT_SECRET = os.getenv('KAKAO_CLIENT_SECRET')
    KAKAO_REDIRECT_URI = os.getenv('KAKAO_REDIRECT_URI')
    print(KAKAO_REDIRECT_URI)
