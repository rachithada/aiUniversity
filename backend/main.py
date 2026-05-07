import os
import shutil

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from rag.build_vector_store import build_vector_store
from rag.rag_pipeline import retrieve_docs

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

app = FastAPI()

if os.path.exists("uploads"):

    for file in os.listdir("uploads"):
        os.remove(f"uploads/{file}")

if os.path.exists("faiss_index"):
    shutil.rmtree("faiss_index")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {
        "message": "Backend running"
    }

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    file_path = f"uploads/{file.filename}"

    if os.path.exists("uploads"):

        for old_file in os.listdir("uploads"):
            os.remove(f"uploads/{old_file}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    build_vector_store()

    return {
        "message": "PDF uploaded and vector DB updated"
    }

@app.post("/chat")
def chat(request: ChatRequest):

    if not request.message.strip():
        return {
            "response": "Please enter a question."
        }

    context = ""

    if (
        os.path.exists("faiss_index")
        and len(os.listdir("uploads")) > 0
    ):

        retrieved = retrieve_docs(request.message)

        if retrieved and len(retrieved.strip()) > 50:
            context = retrieved

    print("\n========== RETRIEVED CONTEXT ==========\n")
    print(context)
    print("\n=======================================\n")

    uploaded_files = os.listdir("uploads")

    current_file = (
        uploaded_files[0]
        if uploaded_files
        else "No file uploaded"
    )

    prompt = f"""
You are an advanced AI University Support Assistant.

Rules:
- Use PDF context ONLY if it is relevant to the user's question.
- If PDF context is unrelated, completely ignore it.
- If relevant PDF information exists, prioritize it.
- If question is general, answer naturally using academic knowledge.
- Never mention whether information came from PDF or not.
- Reply in same language as user.
- Support English, Hindi, and Hinglish naturally.
- Keep responses concise, smart, and student-friendly.
- For summaries, provide structured summaries.
- For coding questions, explain clearly with examples if needed.
- Maintain natural conversational tone.
- Avoid hallucinating fake PDF information.

CURRENT PDF:
{current_file}

PDF CONTEXT:
{context}

QUESTION:
{request.message}
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return {
        "response": completion.choices[0].message.content
    }