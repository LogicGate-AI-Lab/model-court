"""
SQLite-based court code implementation with vector search.
"""

import sqlite3
import json
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base import BaseCourtCode
from model_court.core.models import CourtCodeEntry, Precedent


class SqliteCourtCode(BaseCourtCode):
    """
    SQLite-based court code with hybrid SQL + vector search.
    
    Uses SQLite for structured data storage and ChromaDB for vector similarity search.
    """
    
    def __init__(
        self,
        db_path: str,
        embedding_model: str = "MiniLM",
        embedding_api_key: Optional[str] = None,
        default_validity_period: Optional[timedelta] = None,
        enable_vector_search: bool = True
    ):
        """
        Initialize SQLite court code.
        
        Args:
            db_path: Path to SQLite database file
            embedding_model: Embedding model to use ("MiniLM", "BGE", or "OpenAI")
            embedding_api_key: API key for OpenAI embeddings (if using OpenAI)
            default_validity_period: Default validity period for new entries
            enable_vector_search: Whether to enable vector search (requires ChromaDB)
        """
        super().__init__(db_path)
        
        self.embedding_model_name = embedding_model
        self.embedding_api_key = embedding_api_key
        self.default_validity_period = default_validity_period
        self.enable_vector_search = enable_vector_search
        
        # Lazy initialization
        self._embedding = None
        self._chroma_client = None
        self._chroma_collection = None
        
        # Initialize database
        self._init_database()
        
        # Initialize vector store if enabled
        if self.enable_vector_search:
            self._init_vector_store()
    
    def _get_embedding(self):
        """Get or create embedding model."""
        if self._embedding is None:
            from embeddings.minilm import MiniLMEmbedding
            from embeddings.bge import BGEEmbedding
            from embeddings.openai_embedding import OpenAIEmbedding
            
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
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create court_code table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS court_code (
                entry_id TEXT PRIMARY KEY,
                claim TEXT NOT NULL,
                verdict TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                domain TEXT DEFAULT 'general',
                case_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                valid_from TEXT,
                valid_until TEXT,
                jury_votes_count INTEGER DEFAULT 0,
                objection_count INTEGER DEFAULT 0,
                objection_ratio REAL DEFAULT 0.0,
                metadata TEXT
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_claim ON court_code(claim)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_domain ON court_code(domain)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON court_code(timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def _init_vector_store(self):
        """Initialize ChromaDB vector store."""
        try:
            import chromadb
            from chromadb import EmbeddingFunction as ChromaEmbeddingFunction
            from chromadb.api.types import Documents, Embeddings
        except ImportError:
            raise ImportError(
                "chromadb not installed. Install with: pip install chromadb"
            )
        
        # Create vector store directory
        vector_store_path = Path(self.db_path).parent / "vector_store"
        vector_store_path.mkdir(parents=True, exist_ok=True)
        
        self._chroma_client = chromadb.PersistentClient(path=str(vector_store_path))
        
        # Create embedding function wrapper for ChromaDB 0.5.x+
        embedding = self._get_embedding()
        
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
        
        # Get or create collection
        collection_name = "court_code_claims"
        try:
            self._chroma_collection = self._chroma_client.get_collection(
                name=collection_name,
                embedding_function=embedding_fn
            )
        except Exception as e:
            # Handle incompatible collection (e.g., from older ChromaDB version)
            # Try to delete the old collection and create a new one
            try:
                print(f"Warning: Failed to load existing collection ({str(e)}). Attempting to recreate...")
                self._chroma_client.delete_collection(name=collection_name)
                print(f"Deleted incompatible collection '{collection_name}'")
            except Exception:
                pass  # Collection might not exist
            
            # Create new collection
            self._chroma_collection = self._chroma_client.create_collection(
                name=collection_name,
                embedding_function=embedding_fn
            )
            print(f"Created new collection '{collection_name}'")
    
    async def search_exact(self, claim: str) -> Optional[CourtCodeEntry]:
        """
        Search for an exact match of the claim.
        
        Args:
            claim: The claim text to search for
        
        Returns:
            Exact matching entry if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT entry_id, claim, verdict, reasoning, domain, case_id,
                   timestamp, valid_from, valid_until,
                   jury_votes_count, objection_count, objection_ratio, metadata
            FROM court_code
            WHERE claim = ?
        """, (claim,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Parse the row into CourtCodeEntry
        entry = self._row_to_entry(row)
        return entry
    
    async def search_similar(
        self,
        claim: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Precedent]:
        """
        Search for similar claims using vector similarity.
        
        Args:
            claim: The claim text to search for
            top_k: Maximum number of results to return
            threshold: Minimum similarity score (0-1)
        
        Returns:
            List of similar precedents sorted by similarity
        """
        if not self.enable_vector_search:
            return []
        
        try:
            # Query vector store
            results = self._chroma_collection.query(
                query_texts=[claim],
                n_results=top_k * 2  # Get more candidates for filtering
            )
            
            entry_ids = results['ids'][0] if results['ids'] else []
            distances = results['distances'][0] if results['distances'] else []
            
            # Convert distances to similarity scores
            similarities = [1.0 / (1.0 + dist) for dist in distances]
            
            # Fetch full entries from SQLite
            precedents = []
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for entry_id, similarity in zip(entry_ids, similarities):
                if similarity < threshold:
                    continue
                
                cursor.execute("""
                    SELECT entry_id, claim, verdict, reasoning, domain, case_id,
                           timestamp, valid_from, valid_until,
                           jury_votes_count, objection_count, objection_ratio, metadata
                    FROM court_code
                    WHERE entry_id = ?
                """, (entry_id,))
                
                row = cursor.fetchone()
                if row:
                    entry = self._row_to_entry(row)
                    precedent = Precedent(
                        precedent_id=entry.entry_id,
                        claim=entry.claim,
                        verdict=entry.verdict,
                        reasoning=entry.reasoning,
                        similarity_score=similarity,
                        timestamp=entry.timestamp,
                        valid_from=entry.valid_from,
                        valid_until=entry.valid_until
                    )
                    precedents.append(precedent)
            
            conn.close()
            
            # Sort by similarity and limit
            precedents.sort(key=lambda p: p.similarity_score, reverse=True)
            return precedents[:top_k]
        
        except Exception as e:
            print(f"Warning: Vector search failed: {e}")
            return []
    
    async def add_entry(self, entry: CourtCodeEntry) -> str:
        """
        Add a new entry to the court code.
        
        Args:
            entry: The court code entry to add
        
        Returns:
            ID of the added entry
        """
        # Set validity period if not specified
        if entry.valid_from is None and self.default_validity_period:
            entry.valid_from = entry.timestamp
            entry.valid_until = entry.timestamp + self.default_validity_period
        
        # Insert into SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO court_code (
                entry_id, claim, verdict, reasoning, domain, case_id,
                timestamp, valid_from, valid_until,
                jury_votes_count, objection_count, objection_ratio, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.entry_id,
            entry.claim,
            entry.verdict,
            entry.reasoning,
            entry.domain,
            entry.case_id,
            entry.timestamp.isoformat(),
            entry.valid_from.isoformat() if entry.valid_from else None,
            entry.valid_until.isoformat() if entry.valid_until else None,
            entry.jury_votes_count,
            entry.objection_count,
            entry.objection_ratio,
            json.dumps(entry.metadata)
        ))
        
        conn.commit()
        conn.close()
        
        # Add to vector store
        if self.enable_vector_search:
            try:
                self._chroma_collection.add(
                    documents=[entry.claim],
                    ids=[entry.entry_id],
                    metadatas=[{
                        "verdict": entry.verdict,
                        "domain": entry.domain,
                        "case_id": entry.case_id
                    }]
                )
            except Exception as e:
                print(f"Warning: Failed to add to vector store: {e}")
        
        return entry.entry_id
    
    async def update_entry(self, entry_id: str, **updates) -> bool:
        """
        Update an existing entry in the court code.
        
        Args:
            entry_id: ID of the entry to update
            **updates: Fields to update
        
        Returns:
            True if update was successful, False otherwise
        """
        if not updates:
            return False
        
        # Build update query
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ['timestamp', 'valid_from', 'valid_until'] and isinstance(value, datetime):
                value = value.isoformat()
            elif key == 'metadata':
                value = json.dumps(value)
            
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(entry_id)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = f"UPDATE court_code SET {', '.join(set_clauses)} WHERE entry_id = ?"
        cursor.execute(query, values)
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        # Update vector store if claim was updated
        if 'claim' in updates and self.enable_vector_search:
            try:
                self._chroma_collection.update(
                    ids=[entry_id],
                    documents=[updates['claim']]
                )
            except Exception as e:
                print(f"Warning: Failed to update vector store: {e}")
        
        return affected > 0
    
    async def get_entry(self, entry_id: str) -> Optional[CourtCodeEntry]:
        """
        Retrieve a specific entry by ID.
        
        Args:
            entry_id: ID of the entry to retrieve
        
        Returns:
            The entry if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT entry_id, claim, verdict, reasoning, domain, case_id,
                   timestamp, valid_from, valid_until,
                   jury_votes_count, objection_count, objection_ratio, metadata
            FROM court_code
            WHERE entry_id = ?
        """, (entry_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_entry(row)
    
    async def delete_entry(self, entry_id: str) -> bool:
        """
        Delete an entry from the court code.
        
        Args:
            entry_id: ID of the entry to delete
        
        Returns:
            True if deletion was successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM court_code WHERE entry_id = ?", (entry_id,))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        # Delete from vector store
        if self.enable_vector_search:
            try:
                self._chroma_collection.delete(ids=[entry_id])
            except Exception as e:
                print(f"Warning: Failed to delete from vector store: {e}")
        
        return affected > 0
    
    def _row_to_entry(self, row: tuple) -> CourtCodeEntry:
        """Convert database row to CourtCodeEntry."""
        return CourtCodeEntry(
            entry_id=row[0],
            claim=row[1],
            verdict=row[2],
            reasoning=row[3],
            domain=row[4],
            case_id=row[5],
            timestamp=datetime.fromisoformat(row[6]),
            valid_from=datetime.fromisoformat(row[7]) if row[7] else None,
            valid_until=datetime.fromisoformat(row[8]) if row[8] else None,
            jury_votes_count=row[9],
            objection_count=row[10],
            objection_ratio=row[11],
            metadata=json.loads(row[12]) if row[12] else {}
        )

