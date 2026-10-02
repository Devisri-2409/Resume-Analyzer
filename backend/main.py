from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
import models
from routes.auth import router as auth_router
from routes.admin import router as admin_router
from routes.resume import router as resume_router
from routes.profile import router as profile_router
from routes.courses import router as courses_router
from routes.lessons import router as lessons_router
from routes.quizzes import router as quizzes_router
from routes.learning import router as learning_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist on startup without blocking module imports
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database connection note: {e}")
    yield


app = FastAPI(
    title="AI Resume Analyzer & Career Learning Platform",
    description="AI-powered resume analysis, job matching, profile management, and career learning dashboard",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "AI Resume Analyzer & Career Learning API is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(resume_router)
app.include_router(profile_router)
app.include_router(courses_router)
app.include_router(lessons_router)
app.include_router(quizzes_router)
app.include_router(learning_router)

