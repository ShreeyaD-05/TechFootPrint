from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gateway.routes import (
    auth, users, platforms, analytics, portfolio,
    mentoring, management, admin, dashboard,
    discussions, submissions, suggestions
)
from gateway.routes import faculty_students
from gateway.routes import college
from gateway.routes import chat

app = FastAPI(
    title="Developer Analytics Platform",
    description="Aggregate coding statistics from multiple platforms with college mentoring",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router,        prefix="/auth",       tags=["Authentication"])
app.include_router(users.router,       prefix="/users",      tags=["Users"])
app.include_router(platforms.router,   prefix="/platforms",  tags=["Platforms"])
app.include_router(analytics.router,   prefix="/analytics",  tags=["Analytics"])
app.include_router(portfolio.router,   prefix="/portfolio",  tags=["Portfolio"])
app.include_router(mentoring.router,   prefix="/mentoring",  tags=["Mentoring"])
app.include_router(management.router,  prefix="/management", tags=["Management"])
app.include_router(admin.router,       prefix="/admin",      tags=["Admin"])
app.include_router(dashboard.router,   prefix="/dashboard",  tags=["Dashboard"])
app.include_router(discussions.router, prefix="/api",        tags=["Discussions"])
app.include_router(submissions.router, prefix="/api",        tags=["Submissions"])
app.include_router(suggestions.router, prefix="/api",        tags=["Suggestions"])
app.include_router(faculty_students.router, prefix="/faculty", tags=["Faculty Student Management"])
app.include_router(college.router,          prefix="/college",  tags=["My College"])
app.include_router(chat.router,             prefix="/chat",     tags=["Chat"])


@app.get("/")
async def root():
    return {"message": "Developer Analytics Platform API", "version": "2.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
