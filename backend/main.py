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

os.makedirs("uploads", exist_ok=True)

if os.path.exists("uploads"):
    for file in os.listdir("uploads"):
        os.remove(os.path.join("uploads", file))

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

    os.makedirs("uploads", exist_ok=True)

    for old_file in os.listdir("uploads"):
        old_file_path = os.path.join("uploads", old_file)
        if os.path.isfile(old_file_path):
            os.remove(old_file_path)

    file_path = os.path.join("uploads", file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if os.path.exists("faiss_index"):
        shutil.rmtree("faiss_index")

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
        and os.path.exists("uploads")
        and len(os.listdir("uploads")) > 0
    ):
        retrieved = retrieve_docs(request.message)

        if retrieved and len(retrieved.strip()) > 50:
            context = retrieved

    print("\n========== RETRIEVED CONTEXT ==========\n")
    print(context)
    print("\n=======================================\n")

    uploaded_files = os.listdir("uploads") if os.path.exists("uploads") else []

    current_file = uploaded_files[0] if uploaded_files else "No file uploaded"

    system_prompt = """
You are an advanced AI University Support Assistant.

Your main goal is to give clean, readable, beautiful, well-formatted answers.

GENERAL FORMATTING RULES:
- Always use Markdown formatting.
- Use clear headings like:
  ## Answer
  ## Explanation
  ## Code
  ## Example
  ## Output
- Add proper spacing between sections.
- Avoid writing everything in one paragraph.
- Use bullet points for important points.
- Use numbered steps for processes.
- Keep paragraphs short and readable.
- Make the answer student-friendly and easy to understand.
- Never give messy inline code.

PDF RULES:
- Use PDF context only if it is relevant to the user's question.
- If PDF context is unrelated, ignore it completely.
- If relevant PDF information exists, prioritize it.
- Never mention whether information came from PDF or not.
- Do not create fake PDF information.

LANGUAGE RULES:
- Reply in the same language as the user.
- Support English, Hindi, and Hinglish naturally.
- Keep the tone natural, helpful, and friendly.

CODING ANSWER RULES:
- First give a short explanation.
- Then provide clean code inside a proper code block.
- Always use language name in code block, for example ```python.
- After code, give sample input and output if useful.
- Explain the code briefly only when needed.
- Do not write code in a single line unless it is actually required.

WHEN USER ASKS MULTIPLE QUESTIONS:
- Answer one by one.
- Use numbering.
- Keep each answer clearly separated.
- Use proper headings and code blocks.

SUMMARY RULES:
- For summaries, use headings and bullet points.
- Highlight important points clearly.
- Keep it structured and easy to revise.
"""

    user_prompt = f"""
CURRENT PDF:
{current_file}

PDF CONTEXT:
{context}

USER QUESTION:
{request.message}
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.4,
        max_tokens=1200
    )

    return {
        "response": completion.choices[0].message.content
    }