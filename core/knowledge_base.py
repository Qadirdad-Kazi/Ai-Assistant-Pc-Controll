import os
import shutil
from typing import List, Dict, Any
from PySide6.QtCore import QObject, Signal

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# Persistence directory for the vector DB
DB_DIR = os.path.join(os.getcwd(), "data", "grimoire_db")
os.makedirs(DB_DIR, exist_ok=True)

class KnowledgeBase(QObject):
    """
    Manages local RAG operations using ChromaDB and LangChain.
    """
    # Signals for async operations if needed in future
    operation_finished = Signal(str)
    error_occurred = Signal(str)
    def __init__(self):
        super().__init__()
        # Use nomic-embed-text for high quality local embeddings, or fall back to installed llama
        self.embedding_model_name = "nomic-embed-text" 
        self._db = None
        self._init_db()

    def _init_db(self):
        """Initialize the Vector Store."""
        try:
            print(f"[KnowledgeBase] Initializing OllamaEmbeddings with model: {self.embedding_model_name}...")
            self.embeddings = OllamaEmbeddings(
                base_url="http://localhost:11434",
                model=self.embedding_model_name
            )
            
            print(f"[KnowledgeBase] Initializing Chroma at: {DB_DIR}...")
            self._db = Chroma(
                persist_directory=DB_DIR,
                embedding_function=self.embeddings,
                collection_name="wolf_grimoire"
            )
            print("[KnowledgeBase] ✓ Vector DB initialized (Ollama).")
        except Exception as e:
            error_msg = f"[KnowledgeBase] Init Error: {e}"
            print(error_msg)
            try:
                with open("kb_error.log", "w") as f:
                    f.write(error_msg)
            except:
                pass
            self._db = None

    def ingest_document(self, file_path: str) -> str:
        """
        Load, split, and index a document.
        Returns a success message or raises error.
        """
        if not self._db:
            raise RuntimeError("Database not initialized.")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 1. Load
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext in [".md", ".markdown"]:
            loader = UnstructuredMarkdownLoader(file_path)
        elif ext in [".txt", ".py", ".js", ".json", ".log"]:
            loader = TextLoader(file_path, autodetect_encoding=True)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        documents = loader.load()

        # 2. Split
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        texts = text_splitter.split_documents(documents)

        # 3. Add to DB
        # Add metadata like source filename
        filename = os.path.basename(file_path)
        for doc in texts:
            doc.metadata["source"] = filename
            doc.metadata["path"] = file_path

        self._db.add_documents(texts)
        # self._db.persist() # Chroma 0.4+ persists automatically usually, but standard call doesn't hurt if old version
        
        return f"Successfully indexed {filename} ({len(texts)} fragments)"

    def query(self, query_text: str, k: int = 4) -> List[Dict]:
        """
        Search the knowledge base.
        """
        if not self._db:
            return []

        results = self._db.similarity_search_with_score(query_text, k=k)
        
        parsed_results = []
        for doc, score in results:
            parsed_results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "score": score
            })
            
        return parsed_results

    def get_stats(self) -> Dict:
        """Get database statistics."""
        if not self._db:
            return {"count": 0}
        
        # Chroma method to get count
        try:
            # Depending on chroma version, this might vary
            count = self._db._collection.count()
            return {"count": count}
        except:
            return {"count": 0}
            
    def get_all_sources(self) -> List[str]:
        """List all unique source files in the DB."""
        if not self._db:
            return []
            
        try:
            # We fetch detailed metadata to find unique sources
            # This can be slow for large DBs, optimization: default to empty or manage a separate registry
            data = self._db.get()
            metadatas = data['metadatas']
            sources = set()
            for m in metadatas:
                if m and "source" in m:
                    sources.add(m["source"])
            return list(sources)
        except:
            return []

    def clear(self):
        """Wipe the database."""
        if self._db:
            # self._db.delete_collection() # This deletes the collection logic
            # Simpler: Delete the directory
            self._db = None
            if os.path.exists(DB_DIR):
                shutil.rmtree(DB_DIR)
            os.makedirs(DB_DIR, exist_ok=True)
            self._init_db()

# Global instance
knowledge_base = KnowledgeBase()
