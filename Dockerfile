# 베이스 이미지로 Python 3.11.4 이미지 사용
FROM python:3.11.4

# 현재 디렉토리의 모든 파일을 이미지 내부의 /app 폴더로 복사
COPY . /app

# SQLite 업그레이드를 위한 패키지 설치
RUN apt-get update && apt-get install -y sqlite3

# 필요한 라이브러리 설치
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install tiktoken
RUN pip install "openai<1.0.0"

# Streamlit 앱 실행 명령어 설정
CMD ["streamlit", "run", "/app/app_minju.py"]
