import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import shutil

def build_vector_store():

    if os.path.exists("faiss_index"):
        shutil.rmtree("faiss_index")

    all_docs = []

    for file in os.listdir("uploads"):

        if file.endswith(".pdf"):

            loader = PyPDFLoader(f"uploads/{file}")

            docs = loader.load()

            all_docs.extend(docs)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    split_docs = text_splitter.split_documents(all_docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.from_documents(
        split_docs,
        embeddings
    )

    vectorstore.save_local("faiss_index")

    print("Vector DB Updated")