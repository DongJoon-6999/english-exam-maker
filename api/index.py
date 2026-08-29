import os
import sys
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

class VercelPathMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if "/index.py" in path:
            # Strip out /api/index.py or /index.py prefix
            parts = path.split("/index.py", 1)
            new_path = parts[1] if len(parts) > 1 and parts[1] else "/"
            if not new_path.startswith("/api") and new_path != "/" and not new_path.startswith("/static"):
                new_path = "/api" + new_path
            request.scope["path"] = new_path
        return await call_next(request)

app.add_middleware(VercelPathMiddleware)
