# FastAPI 서버 메인 파일
# RAG 기반 챗봇 서버

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
import os
import json

# RAG 모듈 import
from rag.rag_chain import RAGChain
from rag.retriever import Retriever

# ============================================
# 환경 변수 로드
# ============================================
load_dotenv()

# ============================================
# RAG 시스템 초기화 (Lazy Loading)
# ============================================
rag_chain = None

def get_rag_chain():
    """RAG 체인 인스턴스 반환 (Lazy Loading)"""
    global rag_chain
    if rag_chain is None:
        print("🚀 RAG 시스템 초기화 중... (첫 요청, 10~20초 소요)")
        
        # Retriever 초기화 (환경 변수 사용)
        retriever = Retriever(
            top_k=int(os.getenv("RAG_TOP_K", "3")),
            score_threshold=float(os.getenv("RAG_SCORE_THRESHOLD", "0.65"))
        )
        
        # RAG Chain 초기화
        rag_chain = RAGChain(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            retriever=retriever,
            model_name=os.getenv("RAG_MODEL_NAME", "gpt-4o-mini"),
            temperature=float(os.getenv("RAG_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("RAG_MAX_TOKENS", "1000"))
        )
        print("✅ RAG 시스템 준비 완료!")
    return rag_chain

# ============================================
# FastAPI 앱 생성
# ============================================
app = FastAPI(
    title="1team RAG Chatbot API",
    description="RAG 기반 상권 분석 챗봇 백엔드",
    version="1.0.0"
)

# ============================================
# CORS 설정
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js 프론트엔드
        "http://localhost:8000",  # Node.js 백엔드
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Pydantic 모델 (데이터 검증)
# ============================================
class ChatRequest(BaseModel):
    """
    클라이언트에서 보내는 요청 형식
    """
    message: str  # 사용자 메시지
    conversation_history: Optional[List[Dict[str, str]]] = None  # 대화 히스토리 (선택적)

# ============================================
# 엔드포인트: 서버 상태 체크
# ============================================
@app.get("/")
async def root():
    return {
        "message": "1team RAG Chatbot API",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ============================================
# RAG 챗봇 스트리밍 엔드포인트
# ============================================

async def stream_rag_response(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 3
):
    """
    RAG 응답을 SSE 스트리밍으로 전송
    """
    try:
        # RAG 체인 가져오기
        rag = get_rag_chain()

        # 스트리밍 실행
        for chunk in rag.stream_run(
            query=query,
            conversation_history=conversation_history,
            top_k=top_k
        ):
            # SSE 형식으로 데이터 전송
            chunk_type = chunk.get("type")
            content = chunk.get("content")

            if chunk_type == "sources":
                # 참고 문서 정보 전송
                yield f"data: {json.dumps({'event': 'sources', 'sources': content}, ensure_ascii=False)}\n\n"
            elif chunk_type == "answer":
                # 답변 청크 전송
                yield f"data: {json.dumps({'event': 'answer', 'content': content}, ensure_ascii=False)}\n\n"
            elif chunk_type == "error":
                # 에러 전송
                yield f"data: {json.dumps({'event': 'error', 'message': content}, ensure_ascii=False)}\n\n"

        # 스트리밍 완료
        yield f"data: {json.dumps({'event': 'done'}, ensure_ascii=False)}\n\n"

    except Exception as e:
        error_msg = json.dumps({
            "event": "error",
            "message": f"RAG 스트리밍 오류: {str(e)}"
        }, ensure_ascii=False)
        yield f"data: {error_msg}\n\n"


@app.post("/api/rag-chat-stream")
async def rag_chat_stream(request: ChatRequest):
    """
    RAG 챗봇 스트리밍 엔드포인트 (SSE)

    작동 방식:
    1. 사용자 질문 받기
    2. 벡터 DB에서 관련 문서 검색
    3. 검색된 문서를 컨텍스트로 OpenAI API 스트리밍 호출
    4. 실시간 답변 + 참고 문서 반환
    """
    print("\n" + "="*50)
    print("📥 [RAG Stream] 받은 요청:")
    print(f"  - query: {request.message[:50]}...")
    print(f"  - history: {len(request.conversation_history) if request.conversation_history else 0}개")
    print("="*50 + "\n")

    return StreamingResponse(
        stream_rag_response(
            query=request.message,
            conversation_history=request.conversation_history,
            top_k=int(os.getenv("RAG_TOP_K", "3"))
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

