from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from typing import List

def setup_cors_middleware(app: FastAPI, origins: List[str]) -> None:
    """Setup CORS middleware for the application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
