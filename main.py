from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.quotes import router as QuotesRouter
from controllers.clients import router as ClientsRouter
from models.base import Base
from database import engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Quote Management API",
    description="A quote management system API built with FastAPI",
    version="1.0.0"
)

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register routers
app.include_router(QuotesRouter, prefix="/api", tags=["Quotes"])
app.include_router(ClientsRouter, prefix="/api", tags=["Clients"])

@app.get('/')
def home():
    return {'message': 'Welcome to Quote Management API! Visit /docs for API documentation.'}