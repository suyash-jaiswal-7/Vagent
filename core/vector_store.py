import os
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embeddings():
    print("Loading embedding model...")

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"}
    )


def get_vector_store_path(meeting_id: str) -> str:
    return os.path.join(CHROMA_DIR, meeting_id)


def build_vector_store(transcript: str, meeting_id: str) -> Chroma:
    vector_store_path = get_vector_store_path(meeting_id)

    if os.path.exists(vector_store_path):
        print(
            f"Existing vector store found for meeting "
            f"{meeting_id}. Reusing it."
        )
        return load_vector_store(meeting_id)

    print(
        f"Building vector store for meeting {meeting_id}..."
    )

    os.makedirs(vector_store_path, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_text(transcript)

    docs = [
        Document(
            page_content=chunk,
            metadata={
                "chunk_index": i,
                "meeting_id": meeting_id
            }
        )
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()

    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=vector_store_path
    )

    print(
        f"Vector store created with "
        f"{len(docs)} chunks."
    )

    return vector_store


def load_vector_store(meeting_id: str) -> Chroma:
    vector_store_path = get_vector_store_path(meeting_id)

    if not os.path.exists(vector_store_path):
        raise FileNotFoundError(
            f"Vector store not found for meeting: {meeting_id}"
        )

    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=vector_store_path
    )

    return vector_store


def get_retriever(
    vector_store: Chroma,
    k: int = 4
):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )