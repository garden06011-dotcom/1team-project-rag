@echo off
REM RAG 서버 실행 스크립트 (CMD용)
REM 이 스크립트를 실행하면 RAG 서버가 시작됩니다

echo ========================================
echo 🚀 RAG 서버 시작 중...
echo ========================================
echo.

REM 현재 디렉토리 확인
cd /d "%~dp0"
echo 현재 디렉토리: %CD%
echo.

REM 가상환경 경로 확인
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 오류: 가상환경을 찾을 수 없습니다.
    echo    현재 디렉토리: %CD%
    echo    올바른 디렉토리로 이동하세요: cd 1team-project-rag\backend
    pause
    exit /b 1
)

echo ✅ 가상환경 확인됨
echo.

REM 가상환경 활성화
echo 가상환경 활성화 중...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ❌ 가상환경 활성화 실패
    pause
    exit /b 1
)

echo ✅ 가상환경 활성화 완료
echo.

REM .env 파일 확인
if not exist ".env" (
    echo ⚠️  경고: .env 파일을 찾을 수 없습니다.
    echo    환경 변수가 제대로 설정되지 않을 수 있습니다.
    echo.
)

REM 서버 시작
echo ========================================
echo 🌐 RAG 서버 시작 (포트 8001)
echo ========================================
echo.
echo 서버 URL:
echo   - Health Check: http://localhost:8001/health
echo   - API 문서: http://localhost:8001/docs
echo   - 루트: http://localhost:8001/
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.

REM uvicorn 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8001

pause

