"""
RAG (Retrieval-Augmented Generation) reference implementation using ChromaDB.
"""

from typing import List, Optional, Union, Literal
from pathlib import Path
from .base import BaseReference
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class LocalRAGReference(BaseReference):
    """
    Local RAG reference using ChromaDB and embeddings.
    
    Supports multiple embedding models and provides vector similarity search
    over a collection of documents.
    """
    
    def __init__(
        self,
        collection_name: str,
        persist_directory: str,
        embedding_model: Literal["MiniLM", "BGE", "OpenAI"] = "MiniLM",
        embedding_api_key: Optional[str] = None,
        source_folder: Optional[str] = None,
        mode: Literal["overwrite", "append", "read_only"] = "read_only",
        top_k: int = 3,
        name: Optional[str] = None
    ):
        """
        Initialize RAG reference.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the vector database
            embedding_model: Embedding model to use ("MiniLM", "BGE", or "OpenAI")
            embedding_api_key: API key for OpenAI embeddings (if using OpenAI)
            source_folder: Folder containing source documents (for initialization)
            mode: Operation mode:
                - "overwrite": Delete existing collection and rebuild from source_folder
                - "append": Add documents from source_folder to existing collection
                - "read_only": Only query, don't modify collection
            top_k: Default number of results to return
            name: Optional name for this reference
        """
        super().__init__(name=name or f"RAG({embedding_model})")
        
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.embedding_model_name = embedding_model
        self.embedding_api_key = embedding_api_key
        self.source_folder = Path(source_folder) if source_folder else None
        self.mode = mode
        self.default_top_k = top_k
        
        # Lazy initialization
        self._embedding = None
        self._client = None
        self._collection = None
        
        # Initialize on first use
        self._initialize()
    
    def _get_embedding(self):
        """Get or create embedding model."""
        if self._embedding is None:
            from model_court.embeddings.minilm import MiniLMEmbedding
            from model_court.embeddings.bge import BGEEmbedding
            from model_court.embeddings.openai_embedding import OpenAIEmbedding
            
            if self.embedding_model_name == "MiniLM":
                self._embedding = MiniLMEmbedding()
            elif self.embedding_model_name == "BGE":
                self._embedding = BGEEmbedding()
            elif self.embedding_model_name == "OpenAI":
                if not self.embedding_api_key:
                    raise ValueError("API key required for OpenAI embeddings")
                self._embedding = OpenAIEmbedding(api_key=self.embedding_api_key)
            else:
                raise ValueError(f"Unknown embedding model: {self.embedding_model_name}")
        
        return self._embedding
    
    def _get_chroma_client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
            except ImportError:
                raise ImportError(
                    "chromadb not installed. Install with: pip install chromadb"
                )
            
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.persist_directory))
        
        return self._client
    
    def _initialize(self):
        """Initialize or load the collection based on mode."""
        try:
            from chromadb import EmbeddingFunction as ChromaEmbeddingFunction
            from chromadb.api.types import Documents, Embeddings
        except ImportError:
            raise ImportError("chromadb not installed. Install with: pip install chromadb")
        
        client = self._get_chroma_client()
        embedding = self._get_embedding()
        
        # Define embedding function wrapper for ChromaDB 0.5.x+
        class CustomEmbeddingFunction(ChromaEmbeddingFunction):
            """Custom embedding function compatible with ChromaDB 0.5.x+"""
            
            def __init__(self, embedding_model):
                self.embedding_model = embedding_model
            
            def __call__(self, input: Documents) -> Embeddings:
                """
                Embed documents using the underlying embedding model.
                
                Args:
                    input: List of texts to embed
                    
                Returns:
                    List of embedding vectors
                """
                embeddings = self.embedding_model.embed(input)
                
                # Ensure proper format
                if hasattr(embeddings, 'tolist'):
                    result = embeddings.tolist()
                elif hasattr(embeddings, 'numpy'):
                    result = embeddings.numpy().tolist()
                else:
                    result = embeddings
                
                # ChromaDB expects list of lists
                if result and not isinstance(result[0], list):
                    result = [result]
                
                return result
        
        embedding_fn = CustomEmbeddingFunction(embedding)
        
        # Handle different modes
        if self.mode == "overwrite":
            # Delete existing collection
            try:
                client.delete_collection(self.collection_name)
            except:
                pass
            
            # Create new collection
            self._collection = client.create_collection(
                name=self.collection_name,
                embedding_function=embedding_fn
            )
            
            # Load documents if source folder provided
            if self.source_folder and self.source_folder.exists():
                self._load_documents()
        
        elif self.mode == "append":
            # Get or create collection
            try:
                self._collection = client.get_collection(
                    name=self.collection_name,
                    embedding_function=embedding_fn
                )
            except Exception as e:
                # Handle incompatible collection (e.g., from older ChromaDB version)
                try:
                    print(f"Warning: Failed to load existing collection ({str(e)}). Attempting to recreate...")
                    client.delete_collection(name=self.collection_name)
                    print(f"Deleted incompatible collection '{self.collection_name}'")
                except Exception:
                    pass  # Collection might not exist
                
                self._collection = client.create_collection(
                    name=self.collection_name,
                    embedding_function=embedding_fn
                )
                print(f"Created new collection '{self.collection_name}'")
            
            # Append documents if source folder provided
            if self.source_folder and self.source_folder.exists():
                self._load_documents()
        
        else:  # read_only
            # Just get existing collection
            try:
                self._collection = client.get_collection(
                    name=self.collection_name,
                    embedding_function=embedding_fn
                )
            except Exception as e:
                # Try to recover from incompatible collection
                try:
                    print(f"Warning: Failed to load existing collection ({str(e)}). Collection may be incompatible.")
                    print(f"Consider using mode='overwrite' or mode='append' to rebuild the collection.")
                except Exception:
                    pass
                raise RuntimeError(
                    f"Collection '{self.collection_name}' not found or incompatible. Error: {str(e)}"
                )
    
    def _load_documents(self):
        """Load documents from source folder."""
        if not self.source_folder or not self.source_folder.exists():
            return
        
        documents = []
        metadatas = []
        ids = []
        
        # Supported text file extensions
        text_extensions = {'.txt', '.md', '.markdown', '.text'}
        
        # Iterate through files in source folder
        for file_path in self.source_folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in text_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Skip empty files
                    if not content.strip():
                        continue
                    
                    documents.append(content)
                    metadatas.append({
                        "source": str(file_path.relative_to(self.source_folder)),
                        "filename": file_path.name
                    })
                    ids.append(str(file_path.relative_to(self.source_folder)))
                
                except Exception as e:
                    print(f"Warning: Failed to load {file_path}: {e}")
        
        # Add documents to collection
        if documents:
            # Check if documents already exist (for append mode)
            if self.mode == "append":
                # Filter out existing documents
                existing = self._collection.get(ids=ids)
                existing_ids = set(existing['ids'])
                
                new_documents = []
                new_metadatas = []
                new_ids = []
                
                for doc, meta, doc_id in zip(documents, metadatas, ids):
                    if doc_id not in existing_ids:
                        new_documents.append(doc)
                        new_metadatas.append(meta)
                        new_ids.append(doc_id)
                
                documents = new_documents
                metadatas = new_metadatas
                ids = new_ids
            
            if documents:
                self._collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"Loaded {len(documents)} documents into collection '{self.collection_name}'")
    
    async def retrieve(self, query: str, top_k: int = None) -> List[str]:
        """
        Retrieve relevant documents using vector similarity search.
        
        Args:
            query: Search query
            top_k: Number of results to return (uses default if None)
        
        Returns:
            List of relevant document texts
        """
        if top_k is None:
            top_k = self.default_top_k
        
        try:
            # Query the collection
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Extract documents
            documents = results['documents'][0] if results['documents'] else []
            return documents
        
        except Exception as e:
            raise RuntimeError(f"RAG retrieval failed: {str(e)}")
    
    async def retrieve_with_scores(self, query: str, top_k: int = None) -> List[tuple[str, float]]:
        """
        Retrieve relevant documents with similarity scores.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of (text, similarity_score) tuples
        """
        if top_k is None:
            top_k = self.default_top_k
        
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            documents = results['documents'][0] if results['documents'] else []
            distances = results['distances'][0] if results['distances'] else []
            
            # Convert distances to similarity scores (smaller distance = higher similarity)
            # ChromaDB uses L2 distance by default
            scores = [1.0 / (1.0 + dist) for dist in distances]
            
            return list(zip(documents, scores))
        
        except Exception as e:
            raise RuntimeError(f"RAG retrieval failed: {str(e)}")
    
    def add_document(self, text: str, metadata: Optional[dict] = None, doc_id: Optional[str] = None) -> None:
        """
        Add a single document to the collection.
        
        Args:
            text: Document text
            metadata: Optional metadata
            doc_id: Optional document ID (generated if not provided)
        """
        if self.mode == "read_only":
            raise RuntimeError("Cannot add documents in read_only mode")
        
        import uuid
        doc_id = doc_id or str(uuid.uuid4())
        
        self._collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )

