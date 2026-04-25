import os
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# ---------------------------
# CONFIG
# ---------------------------
CHROMA_PATH = "chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---------------------------
# EMBEDDINGS
# ---------------------------
def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# ---------------------------
# LLM
# ---------------------------
def get_llm():
    return ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0
    )
# ---------------------------
# INGEST PDF 
# ---------------------------
def ingest_pdf(pdf_path):
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=300
    )

    docs = text_splitter.split_documents(documents)

    embeddings = get_embeddings()

    # ✅ clear old DB (prevents stale data issues)
    if os.path.exists(CHROMA_PATH):
        import shutil
        shutil.rmtree(CHROMA_PATH)

    vectorstore = Chroma.from_documents(
        docs,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )

    vectorstore.persist()

    return len(docs)

# ---------------------------
# QUERY PDF
# ---------------------------
def query_pdf(query):
    embeddings = get_embeddings()

    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

    # 🔥 retrieval
    docs = vectorstore.similarity_search(query, k=5)

    # ✅ force include first chunk (name)
    first_doc = vectorstore.similarity_search("", k=1)[0]
    if first_doc not in docs:
    	docs.append(first_doc)

    # combine context
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""
You are answering questions from a resume.

IMPORTANT:
- If the candidate's name exists ANYWHERE in the context, return it.
- Do NOT say "not mentioned" unless absolutely missing.

Context:
{context}

Question:
{query}
"""

    llm = get_llm()
    response = llm.invoke(prompt)

    return str(response.content), docs