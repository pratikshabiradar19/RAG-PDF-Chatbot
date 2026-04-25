import streamlit as st
import tempfile
from rag_engine import ingest_pdf, query_pdf

st.set_page_config(page_title="RAG PDF Chatbot")
st.title("📄 RAG PDF Chatbot")

# Session state to track processing
if "processed" not in st.session_state:
    st.session_state.processed = False

# Upload PDF
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        pdf_path = tmp_file.name

    st.success("PDF uploaded successfully!")

    # Process PDF
    if st.button("Process PDF"):
        with st.spinner("Processing PDF..."):
            num_chunks = ingest_pdf(pdf_path)
            st.session_state.processed = True
            st.success(f"PDF processed into {num_chunks} chunks!")

# Ask question ONLY after processing
if st.session_state.processed:
    question = st.text_input("Ask a question from the PDF")

    if st.button("Get Answer"):
        if question:
            answer, docs = query_pdf(question)

            st.write("### Answer:")
            st.write(answer)

            st.write("### Sources:")
            for doc in docs:
                st.write(doc.page_content[:200])