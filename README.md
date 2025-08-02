# LLM Interview Service

간호사 면접 준비를 위한 AI 기반 면접 연습 서비스

### ✨ TEAM MEMBER
<table>
  <tbody>
    <tr>
      <td align="center"><a href="https://github.com/"><img src="https://avatars.githubusercontent.com/gtend" width="100px"; alt=""/><br /><sub><b>PM/BE | 유채민</b></sub></a><br /></td>
      <td align="center"><a href="https://github.com/jeonghyeonmin1"><img src="https://avatars.githubusercontent.com/jeonghyeonmin1" width="100px;" alt=""/><br /><sub><b>FE | 정현민</b></sub></a><br /></td>
      <td align="center"><a href="https://github.com/song-hae-in"><img src="https://avatars.githubusercontent.com/song-hae-in" width="100px;" alt=""/><br /><sub><b>BE | 송해인</b></sub></a><br /></td>
      <td align="center"><a href="https://github.com/SPIDEY1876"><img src="https://avatars.githubusercontent.com/SPIDEY1876" width="100px;" alt=""/><br /><sub><b>FE | 김동언</b></sub></a><br /></td>
  </tbody>
</table>
<br>

### ⚙️ STACK
![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white) ![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)

## 🚀 시작하기

### 환경변수 설정
1. `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.
```bash
cp .env.example .env
```

2. `.env` 파일에서 다음 값들을 설정하세요:
- `JWT_SECRET_KEY`: JWT 토큰 서명용 시크릿 키
- `KAKAO_CLIENT_ID`: 카카오 개발자 콘솔에서 발급받은 앱 키
- `KAKAO_CLIENT_SECRET`: 카카오 개발자 콘솔에서 발급받은 시크릿 키
- `OPENAI_API_KEY`: AIMLAPI에서 발급받은 API 키

### 서버 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python run.py
```

서버는 기본적으로 `http://localhost:8080`에서 실행됩니다.

## 📝 산출물

### 1. [API 명세서](https://www.notion.so/API-23b1b52e7b3e8072a611c0ba3bce8d96?source=copy_link)
