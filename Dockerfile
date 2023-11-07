FROM python:3.11.4  # x는 사용하려는 파이썬 버전

# SQLite 업그레이드
RUN apt-get update && apt-get install -y sqlite3

# 필요한 패키지 설치
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit 앱 실행
CMD ["streamlit", "run", "app_minju.py"]
