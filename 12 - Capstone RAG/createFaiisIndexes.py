from dotenv import load_dotenv
load_dotenv()
import os
import faiss
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import openai

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
def index_documents(data_folder: str, faiss_index_path: str):
    embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
    all_docs = []
    pdf_files = ["azure-well-architected.pdf", "wellarchitected-framework.pdf", "gcp-wellarchitected-framework.pdf"]
    for pdf_file in pdf_files:
        loader = PyPDFLoader(os.path.join(data_folder, pdf_file))
        pdf_docs = loader.load_and_split()
        for d in pdf_docs:
            d.metadata["source_file"] = pdf_file
        all_docs.extend(pdf_docs)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splitted_docs = splitter.split_documents(all_docs)
    vectorstore = FAISS.from_documents(splitted_docs, embeddings)
    vectorstore.save_local(faiss_index_path)
if __name__ == "__main__":
    data_folder = "data"
    faiss_index_path = "faiss_index"
    index_documents(data_folder, faiss_index_path)
    print("Completed")