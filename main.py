import os
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils import run_conversation, save_file
app = FastAPI()


class ChatResponse(BaseModel):
    conversation_id: str
    response: str


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health-check")
async def health_check():
    return {"ping": "pong"}


@app.post("/query", response_model=ChatResponse)
def query(
    conversation_id: Optional[str] = Form(default=None),
    query: Optional[str] = Form(default=None),
    image: Optional[UploadFile] = File(default=None),
):
    if query is None and image is None:
        raise HTTPException(
            status_code=400, detail="Either query or image must be provided."
        )
    image_path = None
    if image:
        image_path = save_file(image) if image else None
    if query is None:
        query = ""
    response = run_conversation(query, image_path, conversation_id)
    if image:
        os.remove(image_path)
    return response
