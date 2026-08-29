@echo off
chcp 65001 > nul
title 모의고사 영어 서술형 요약 문제 생성기

echo ========================================================
echo   모의고사 영어 서술형 요약 문제 생성기 (English Summary)
echo ========================================================
echo.
echo [1/2] 필수 패키지 설치 확인 중...
python -m pip install -r requirements.txt > nul 2>&1

echo [2/2] 웹 애플리케이션 서버 실행 중...
echo 브라우저에서 아래 주소로 접속하세요:
echo http://127.0.0.1:8000
echo.

start http://127.0.0.1:8000
python app.py

pause
