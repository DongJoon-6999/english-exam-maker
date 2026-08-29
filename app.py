import os
import requests
from fastapi import FastAPI, HTTPException, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from llm_service import generate_with_gemini, generate_with_openai, generate_with_claude, generate_mock_candidates

app = FastAPI(title="English Summary Problem Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    passage: str = Field(..., description="English reading passage")
    target_grammar: Optional[str] = Field("", description="Target grammar structure")
    target_vocab: Optional[str] = Field("", description="Target vocabulary")
    provider: str = Field("gemini", description="AI provider: gemini | openai | mock")
    api_key: Optional[str] = Field("", description="User API Key")
    model_name: Optional[str] = Field("gemini-3.6-flash", description="Model identifier")
    candidate_count: Optional[int] = Field(3, description="Number of problem candidates")
    difficulty: Optional[str] = Field("basic", description="Difficulty level: intro | basic | advanced | killer")

class TestKeyRequest(BaseModel):
    provider: str
    api_key: str
    model_name: Optional[str] = "gemini-3.6-flash"

SAMPLE_PASSAGES = [
    {
        "id": "purifying-soil",
        "title": "[능률(김) 4과] Purifying Polluted Soil (토양 정화와 버드나무)",
        "grammar_hint": "관계대명사 that, 분사구문, 5형식 enable",
        "vocab_hint": "eco-friendly, restore, extract, absorb, promising",
        "passage": """Mining and other industries are causing soil pollution across the globe. Although polluted soil can be dug up and transported to a landfill, this process is expensive. Moreover, it only moves the problem to another area and does not really solve it.
Fortunately, there is an eco-friendly and cost-effective way to restore polluted soil - planting willow trees. These amazing trees have extensive and well-developed root systems. As a result, they naturally extract a wide range of harmful materials from the soil. They can also grow quickly, even in soil with a high acidity level or a lot of heavy metals in it.
Research on the effectiveness of using willow trees for this purpose is in development. Scientists have found that some species of willow trees are able to absorb harmful materials better than others. Therefore, this promising area should be further explored to find out which trees are the most effective. In time, we may be able to clean up our land with willow trees."""
    },
    {
        "id": "greenwashing",
        "title": "[고3 모의고사] Greenwashing and Deceptive Marketing",
        "grammar_hint": "주격 관계대명사 that, 5형식 allow + to-V, while 분사구문",
        "vocab_hint": "deceptive, allow, present, false, mislead",
        "passage": """Greenwashing is the practice of making an unsubstantiated or misleading claim about the environmental benefits of a product, service, technology or company practice. In other words, greenwashing is making a company appear to be more environmentally friendly than it actually is.
Greenwashing can range from simple exaggeration to outright deception. Companies engage in greenwashing to capitalize on the growing demand for environmentally sound products. They use vague terms, suggestive imagery, or unverified eco-labels to give consumers a false sense of environmental responsibility. While such marketing strategies may boost short-term sales, they ultimately undermine consumer trust and divert attention away from genuine eco-friendly practices that truly benefit our planet."""
    },
    {
        "id": "habit-loop",
        "title": "[고2 학평] The Habit Loop and Cue-Routine-Reward",
        "grammar_hint": "가주어-진주어 구문, not only A but also B, 분사구문",
        "vocab_hint": "automatic, identify, replace, trigger, conscious",
        "passage": """Habits are formed through a neurological loop consisting of three parts: a cue, a routine, and a reward. The cue is a trigger that tells your brain to go into automatic mode and which habit to use. Then there is the routine, which can be physical, mental, or emotional. Finally, there is a reward, which helps your brain figure out if this particular loop is worth remembering for the future.
Over time, this loop becomes more and more automatic until the cue and reward become intertwined with a powerful sense of craving. Therefore, to change an unwanted habit, it is crucial not to eliminate the cue entirely, but to consciously replace the old routine with a healthier alternative while maintaining the same reward."""
    }
]

DEFAULT_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

@app.get("/api/sample-passages")
@app.get("/sample-passages")
@app.get("/api/index.py/api/sample-passages")
@app.get("/api/index.py/sample-passages")
def get_sample_passages():
    return {"samples": SAMPLE_PASSAGES}

@app.get("/api/config-status")
@app.get("/config-status")
@app.get("/api/index.py/api/config-status")
@app.get("/api/index.py/config-status")
def get_config_status():
    gemini_key = os.getenv("GEMINI_API_KEY", "") or DEFAULT_GEMINI_KEY
    claude_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    return {
        "server_keys": {
            "gemini": bool(gemini_key),
            "claude": bool(claude_key),
            "openai": bool(openai_key)
        }
    }

@app.post("/api/test-key")
@app.post("/test-key")
@app.post("/api/index.py/api/test-key")
@app.post("/api/index.py/test-key")
def test_key(req: TestKeyRequest):
    provider = req.provider.lower()
    if provider == "mock":
        return {"success": True, "message": "모의(Mock) 모드는 API 키가 필요하지 않습니다."}

    api_key = (req.api_key or "").strip()
    if not api_key:
        if provider == "gemini":
            api_key = DEFAULT_GEMINI_KEY
        elif provider == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(status_code=400, detail="API Key가 입력되지 않았습니다.")
    try:
        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{req.model_name or 'gemini-3.6-flash'}:generateContent?key={api_key}"
            resp = requests.post(
                url,
                json={
                    "contents": [{"role": "user", "parts": [{"text": "Hi"}]}],
                    "generationConfig": {"maxOutputTokens": 5}
                },
                timeout=30
            )
            if resp.status_code == 200:
                return {"success": True, "message": "Gemini API 연결에 성공했습니다!"}
            else:
                err_msg = resp.text
                try:
                    err_msg = resp.json().get("error", {}).get("message", resp.text)
                except Exception:
                    pass
                raise HTTPException(status_code=400, detail=f"Gemini API 인증 실패: {err_msg}")

        elif provider == "claude":
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            resp = requests.post(
                url,
                headers=headers,
                json={
                    "model": req.model_name or "claude-3-5-haiku-20241022",
                    "max_tokens": 5,
                    "messages": [{"role": "user", "content": "Hi"}]
                },
                timeout=30
            )
            if resp.status_code == 200:
                return {"success": True, "message": "Claude (Anthropic) API 연결에 성공했습니다!"}
            else:
                err_msg = resp.text
                try:
                    err_msg = resp.json().get("error", {}).get("message", resp.text)
                except Exception:
                    pass
                raise HTTPException(status_code=400, detail=f"Claude API 인증 실패: {err_msg}")

        elif provider == "openai":
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                return {"success": True, "message": "OpenAI API 연결에 성공했습니다!"}
            else:
                err_msg = resp.text
                try:
                    err_msg = resp.json().get("error", {}).get("message", resp.text)
                except Exception:
                    pass
                raise HTTPException(status_code=400, detail=f"OpenAI API 인증 실패: {err_msg}")
        else:
            return {"success": True, "message": "모의(Mock) 모드는 API 키가 필요하지 않습니다."}
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="API 서버 응답 시간 초과(Timeout): 네트워크 연결이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
@app.post("/generate")
@app.post("/api/index.py/api/generate")
@app.post("/api/index.py/generate")
def generate_problems(req: GenerateRequest):
    if not req.passage or len(req.passage.strip()) < 20:
        raise HTTPException(status_code=400, detail="영어 지문을 최소 20자 이상 입력해 주세요.")

    provider = req.provider.lower()
    api_key = (req.api_key or "").strip()

    # Fallback to system environment variables or default key if API key is not passed in request
    if not api_key:
        if provider == "gemini":
            api_key = DEFAULT_GEMINI_KEY
        elif provider == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "").strip()

    difficulty = req.difficulty or "basic"

    # If still no API key provided or provider is mock, fallback to smart mock generator
    if not api_key or provider == "mock":
        try:
            result = generate_mock_candidates(req.passage, req.target_grammar, req.target_vocab, candidate_count=req.candidate_count or 3, difficulty=difficulty)
            return {"success": True, "provider": "mock", "data": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Mock 생성 오류: {str(e)}")

    try:
        if provider == "gemini":
            model = req.model_name or "gemini-3.6-flash"
            result = generate_with_gemini(
                api_key=api_key,
                passage=req.passage,
                target_grammar=req.target_grammar or "",
                target_vocab=req.target_vocab or "",
                model_name=model,
                candidate_count=req.candidate_count or 3,
                difficulty=difficulty
            )
            return {"success": True, "provider": "gemini", "data": result}

        elif provider == "claude":
            model = req.model_name or "claude-3-7-sonnet-20250219"
            result = generate_with_claude(
                api_key=api_key,
                passage=req.passage,
                target_grammar=req.target_grammar or "",
                target_vocab=req.target_vocab or "",
                model_name=model,
                candidate_count=req.candidate_count or 3,
                difficulty=difficulty
            )
            return {"success": True, "provider": "claude", "data": result}

        elif provider == "openai":
            model = req.model_name or "gpt-4o-mini"
            result = generate_with_openai(
                api_key=api_key,
                passage=req.passage,
                target_grammar=req.target_grammar or "",
                target_vocab=req.target_vocab or "",
                model_name=model,
                candidate_count=req.candidate_count or 3,
                difficulty=difficulty
            )
            return {"success": True, "provider": "openai", "data": result}
        else:
            result = generate_mock_candidates(req.passage, req.target_grammar, req.target_vocab, candidate_count=req.candidate_count or 3, difficulty=difficulty)
            return {"success": True, "provider": "mock", "data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제 생성 실패: {str(e)}")

# Mount static files
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
public_dir = os.path.join(base_dir, "public")

if os.path.exists(public_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(public_dir, "static") if os.path.exists(os.path.join(public_dir, "static")) else static_dir), name="static")
elif os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(public_dir, "index.html")
    if not os.path.exists(index_path):
        index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "Server is running. index.html not found."})

@app.api_route("/{full_path:path}", methods=["GET", "POST", "OPTIONS"])
async def universal_route_handler(request: Request, full_path: str):
    route_param = request.query_params.get("_route", "")
    clean_path = f"{full_path} {route_param} {request.url.path}".lower()
    
    if "sample-passages" in clean_path:
        return get_sample_passages()
    
    elif "config-status" in clean_path:
        return get_config_status()
        
    elif "test-key" in clean_path:
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass
        return test_key(TestKeyRequest(**body))
        
    elif "generate" in clean_path:
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass
        return generate_problems(GenerateRequest(**body))
        
    return JSONResponse({"detail": f"Path '{request.url.path}' not handled"}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
