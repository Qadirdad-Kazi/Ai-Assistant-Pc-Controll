import sys
import traceback

def log(msg):
    with open("debug_log.txt", "a") as f:
        f.write(msg + "\n")
    print(msg)

try:
    log("Attempting imports...")
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    log("Imports successful.")
except Exception as e:
    log(f"Import Error: {traceback.format_exc()}")
    sys.exit(1)

try:
    log("Initializing Embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    log("Embeddings initialized.")
except Exception as e:
    log(f"Embeddings Init Error: {traceback.format_exc()}")

try:
    log("Initializing Chroma...")
    import os
    db_dir = os.path.join(os.getcwd(), "data", "grimoire_db")
    db = Chroma(persist_directory=db_dir, embedding_function=embeddings, collection_name="wolf_grimoire")
    log("Chroma initialized.")
except Exception as e:
    log(f"Chroma Init Error: {traceback.format_exc()}")
