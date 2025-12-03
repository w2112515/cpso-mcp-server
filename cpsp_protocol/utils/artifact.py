"""
Artifact Manager for CPSO-Protocol Multi-Agent System
Handles the creation, storage, and retrieval of artifacts from various sources.
"""

from typing import List, Dict, Optional, Literal, Union, Any
import uuid
import hashlib
from datetime import datetime
from ..tools.vector_db import VectorDB


class ArtifactManager:
    """
    Manages artifacts in the CPSO-Protocol system.
    
    This class handles:
    1. Creating artifacts from various inputs (web content, documents, etc.)
    2. Storing artifacts in vector database
    3. Generating summaries for large artifacts
    4. Providing references to artifacts for inter-agent communication
    """
    
    def __init__(self):
        self.vector_db = VectorDB()
    
    def create_artifact(self, content: str, source: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create an artifact from content and return its ID.
        
        Args:
            content: The content to store as an artifact
            source: Source of the content (URL, file path, etc.)
            metadata: Additional metadata about the artifact
            
        Returns:
            str: Unique ID of the created artifact
        """
        # Generate unique ID for the artifact
        artifact_id = str(uuid.uuid4())
        
        # Calculate content hash for deduplication
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Create artifact record
        artifact_metadata = {
            'id': artifact_id,
            'content_hash': content_hash,
            'source': source,
            'created_at': datetime.now().isoformat(),
        }
        
        # Add user metadata if provided
        if metadata:
            artifact_metadata.update(metadata)
        
        # Store artifact in vector database
        self.vector_db.store_artifact(artifact_id, content, artifact_metadata)
        
        return artifact_id
    
    def get_artifact(self, artifact_id: str) -> Optional[Dict]:
        """
        Retrieve an artifact by its ID.
        
        Args:
            artifact_id: The ID of the artifact to retrieve
            
        Returns:
            Dict: The artifact data, or None if not found
        """
        return self.vector_db.retrieve_artifact(artifact_id)
    
    def generate_summary(self, content: str, max_length: int = 500) -> str:
        """
        Generate a summary of the content.
        
        Args:
            content: The content to summarize
            max_length: Maximum length of the summary
            
        Returns:
            str: Generated summary
        """
        # In a real implementation, this would use an LLM to generate a summary
        # For now, we'll just truncate the content
        if len(content) <= max_length:
            return content
        
        # Simple truncation with ellipsis
        return content[:max_length-3] + "..."
    
    def create_attachment_artifact(self, file_name: str, content: str, file_type: str) -> Dict:
        """
        Create an artifact specifically for file attachments according to protocol v12.5.1.
        
        Args:
            file_name: Name of the file
            content: Content of the file
            file_type: Type of the file (markdown, pdf, docx)
            
        Returns:
            Dict: Artifact reference information
        """
        # Create the artifact
        artifact_id = self.create_artifact(content, source=f"attachment:{file_name}")
        
        # Generate summary if content is large (> 5k tokens ~ 2500 words)
        # Using character count as approximation
        if len(content) > 2500:
            content_summary = self.generate_summary(content, 500)
        else:
            content_summary = content
            
        # Get snippet for quick preview
        raw_text_snippet = content[:2000] if len(content) > 2000 else content
        
        return {
            "file_name": file_name,
            "file_type": file_type,
            "content_summary": content_summary,
            "full_content_ref": artifact_id,
            "raw_text_snippet": raw_text_snippet
        }