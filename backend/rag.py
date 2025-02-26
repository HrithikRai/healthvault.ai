import shutil
import os
import tomli
import warnings
import asyncio
import json
import websockets
from warnings import simplefilter
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader

def update_rag_chain():
    with open("../parameters.toml", "rb") as params:
            config = tomli.load(params)

    vector_store_path = config["rag"]["vector_store_path"]

    from chromadb import PersistentClient
    persistent_client = PersistentClient(path=vector_store_path)
    # modifiable according to session
    collection_name = "patient1"

    from langchain_community.document_loaders import TextLoader
    loader = TextLoader(f"../uploads/{collection_name}/{collection_name}_analysis.txt")
    docs = loader.load()

    from langchain_text_splitters.character import CharacterTextSplitter
    # # to avoid ending them abruptly use . and chunk overlap
    char_splitter = CharacterTextSplitter(separator=".",chunk_size=400,chunk_overlap=50)
    pages_markdown_char_split = char_splitter.split_documents(docs)

    for i in pages_markdown_char_split:
        i.page_content = ' '.join(i.page_content.split())

    from langchain_cohere import CohereEmbeddings

    embeddings = CohereEmbeddings(
        cohere_api_key="cZWxyHPX5B72hYVgeLK45bTrwiM05v8lQ5dHGIXS",
        model="embed-english-v3.0",

    )

    vector_store_from_client = Chroma(
            client=persistent_client,
            collection_name=collection_name,
            embedding_function=embeddings,
        )

    vector_store_from_client.add_documents(documents=pages_markdown_char_split)
