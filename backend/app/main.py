from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routes import apis, auth, dashboard, logs, mock, permissions, responses

Base.metadata.create_all(bind=engine)  # Replace with Alembic migrations in production.
app = FastAPI(title="Mock API Platform", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api")
app.include_router(apis.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(permissions.router, prefix="/api")
app.include_router(responses.router, prefix="/api")
app.include_router(mock.router)

@app.get("/health")
def health(): return {"status": "ok"}
