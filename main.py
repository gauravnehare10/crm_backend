from fastapi import FastAPI
from routes.user_data import user
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.include_router(user)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust the frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)