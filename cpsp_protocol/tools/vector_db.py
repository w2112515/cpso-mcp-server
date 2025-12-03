"""
Vector Database Tool for CPSO-Protocol
Handles storage and retrieval of artifacts in ChromaDB vector database.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
from ..config import Config
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from functools import lru_cache
import hashlib


class VectorDB:
    """
    Wrapper around ChromaDB for storing and retrieving artifacts.
    """
    
    def __init__(self):
        """
        Initialize the VectorDB connection.
        """
        self.client = chromadb.PersistentClient(
            path=Config.CHROMADB_PATH
        )
        self.collection = self.client.get_or_create_collection("artifacts")
        # Initialize embedding model - moved to lazy initialization for better performance
        self._embeddings = None
    
    @property
    def embeddings(self):
        """
        Lazy initialization of the embedding model.
        Only initialize when first needed.
        """
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return self._embeddings
    
    def store_artifact(self, artifact_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Store an artifact in the vector database.
        
        Args:
            artifact_id: Unique identifier for the artifact
            content: Content of the artifact
            metadata: Optional metadata about the artifact
        """
        # Split content into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        texts = text_splitter.split_text(content)
        
        # Handle case where content produces no chunks
        if not texts:
            # Create a minimal chunk to avoid empty embeddings error
            texts = [""]
        
        # Generate embeddings for chunks
        embeddings = self.embeddings.embed_documents(texts)
        
        # Create metadata for each chunk
        metadatas = []
        ids = []
        for i, text in enumerate(texts):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata['artifact_id'] = artifact_id
            chunk_metadata['chunk_index'] = i
            metadatas.append(chunk_metadata)
            ids.append(f"{artifact_id}_chunk_{i}")
        
        # Store chunks with embeddings
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=[embedding for embedding in embeddings]
        )
    
    def retrieve_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an artifact from the vector database.
        
        Args:
            artifact_id: ID of the artifact to retrieve
            
        Returns:
            Dictionary containing the artifact data, or None if not found
        """
        result = self.collection.get(ids=[artifact_id])
        if result and result['ids']:
            return {
                'id': result['ids'][0],
                'content': result['documents'][0] if result['documents'] else '',
                'metadata': result['metadatas'][0] if result['metadatas'] else {}
            }
        return None
    
    @lru_cache(maxsize=128)
    def _cached_embedding(self, query_hash: str, query: str) -> list:
        """
        Cache embeddings for queries to improve performance.
        
        Args:
            query_hash: MD5 hash of the query text
            query: Query text to embed
            
        Returns:
            Embedding vector for the query
        """
        return self.embeddings.embed_query(query)
    
    def _get_query_hash(self, query: str) -> str:
        """
        Generate MD5 hash for a query string.
        
        Args:
            query: Query string to hash
            
        Returns:
            MD5 hash of the query string
        """
        return hashlib.md5(query.encode()).hexdigest()
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for artifacts similar to the query.
        
        Args:
            query: Query text to search for
            n_results: Number of results to return
            
        Returns:
            List of similar artifacts
        """
        # Generate embedding for query with caching
        query_hash = self._get_query_hash(query)
        query_embedding = self._cached_embedding(query_hash, query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        artifacts = []
        if results and results['ids']:
            for i in range(len(results['ids'][0])):
                artifacts.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i] if results['documents'] else '',
                    'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0][i] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
        
        return artifacts
    
    def search_similar_batch(self, queries: List[str], n_results: int = 5) -> List[List[Dict[str, Any]]]:
        """
        Batch search for artifacts similar to multiple queries.
        
        Args:
            queries: List of query texts to search for
            n_results: Number of results to return per query
            
        Returns:
            List of lists of similar artifacts for each query
        """
        # Generate embeddings for all queries with caching
        query_embeddings = []
        for query in queries:
            query_hash = self._get_query_hash(query)
            query_embedding = self._cached_embedding(query_hash, query)
            query_embeddings.append(query_embedding)
        
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results
        )
        
        batch_artifacts = []
        if results and results['ids']:
            for i in range(len(results['ids'])):
                artifacts = []
                for j in range(len(results['ids'][i])):
                    artifacts.append({
                        'id': results['ids'][i][j],
                        'content': results['documents'][i][j] if results['documents'] else '',
                        'metadata': results['metadatas'][i][j] if results['metadatas'] and results['metadatas'][i][j] else {},
                        'distance': results['distances'][i][j] if results['distances'] else None
                    })
                batch_artifacts.append(artifacts)
        
        return batch_artifacts