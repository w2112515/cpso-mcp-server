"""
Global State Management for CPSO-Protocol Multi-Agent System
"""

import uuid
import json
import os
import redis
import logging
from typing import List, Dict, Optional, Literal, Union, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from .state.schema import (
    GlobalState, GlobalStateStatus, UserFeedback, 
    ScoutInstruction, RawIntelligence, InputAttachment
)
from .config import Config


# Set up logger
logger = logging.getLogger(__name__)

__all__ = ['StateManager', 'GlobalState', 'GlobalStateStatus', 'UserFeedback', 
           'ScoutInstruction', 'RawIntelligence', 'InputAttachment']


class StateManager:
    """
    Manages the global state of the CPSO-Protocol system.
    
    This class handles:
    1. Initializing the global state
    2. Updating state values
    3. Managing state transitions
    4. Handling persistence (in future implementations)
    """
    
    def __init__(self, request_id: Optional[str] = None):
        """
        Initialize the StateManager with a new or existing request.
        
        Args:
            request_id: Optional request ID. If not provided, a new one will be generated.
        """
        # 尝试初始化 Redis 客户端，如果失败则设置为 None（优雅降级）
        self.redis_client = None
        try:
            redis_url = Config.REDIS_URL
            # 如果 REDIS_URL 为 None，跳过 Redis 初始化
            if redis_url is None:
                logger.info("REDIS_URL not configured. State persistence will be disabled.")
            else:
                # 检查是否在 serverless 环境（Vercel）中且 URL 指向 localhost
                is_vercel = os.getenv("VERCEL") == "1"
                if is_vercel and ("localhost" in redis_url or "127.0.0.1" in redis_url):
                    logger.warning("Redis URL points to localhost in Vercel environment. Redis features will be disabled.")
                else:
                    self.redis_client = redis.from_url(redis_url)
                    # 测试连接
                    self.redis_client.ping()
                    logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {str(e)}. State persistence will be disabled.")
            self.redis_client = None
        
        self.state = self._initialize_state(request_id)
    
    def _initialize_state(self, request_id: Optional[str] = None) -> GlobalState:
        """
        Initialize a new global state object.
        
        Args:
            request_id: Optional request ID
            
        Returns:
            GlobalState: Initialized state object
        """
        # Try to restore state from Redis if request_id is provided
        if request_id:
            restored_state = self.restore_state(request_id)
            if restored_state:
                logger.info(f"Restored state for request_id: {request_id}")
                return restored_state
        
        # Otherwise initialize a new state
        if request_id is None:
            request_id = str(uuid.uuid4())
            
        logger.info(f"Initialized new state with request_id: {request_id}")
        return GlobalState(
            request_id=request_id,
            status=GlobalStateStatus.SCOUTING,
            iteration_count=0,
            user_intent="",
            user_feedback_history=[],
            scout_instructions=[],
            raw_intelligence=[],
            consolidated_briefing="",
            technical_correction=None,
            strategy_draft="",
            audit_report="",
            input_attachments=[]
        )
    
    def update_state(self, **kwargs) -> None:
        """
        Update state fields with provided values.
        
        Args:
            **kwargs: Field-value pairs to update
        """
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
    
    def add_user_feedback(self, feedback_type: Literal["strategic", "technical"], content: str) -> None:
        """
        Add user feedback to the state.
        
        Args:
            feedback_type: Type of feedback (strategic or technical)
            content: Feedback content
        """
        feedback = UserFeedback(
            role="user",
            type=feedback_type,
            content=content,
            timestamp=datetime.now().timestamp()
        )
        self.state.user_feedback_history.append(feedback)
        
        # Increment iteration count when feedback is added
        self.state.iteration_count += 1
    
    def add_scout_instruction(self, role: Literal["market", "tech", "competitor"], topic: str) -> str:
        """
        Add a scout instruction to the state.
        
        Args:
            role: Role of the scout
            topic: Topic for the scout to investigate
            
        Returns:
            str: ID of the created instruction
        """
        instruction_id = str(uuid.uuid4())
        instruction = ScoutInstruction(
            id=instruction_id,
            role=role,
            topic=topic,
            status="pending"
        )
        self.state.scout_instructions.append(instruction)
        return instruction_id
    
    def update_scout_status(self, instruction_id: str, status: Literal["pending", "done"]) -> bool:
        """
        Update the status of a scout instruction.
        
        Args:
            instruction_id: ID of the instruction to update
            status: New status
            
        Returns:
            bool: True if instruction was found and updated, False otherwise
        """
        for instruction in self.state.scout_instructions:
            if instruction.id == instruction_id:
                instruction.status = status
                return True
        return False
    
    def add_raw_intelligence(self, source_scout_id: str, content_summary: str, artifact_ref_id: str) -> None:
        """
        Add raw intelligence to the state.
        
        Args:
            source_scout_id: ID of the scout that generated this intelligence
            content_summary: Summary of the intelligence
            artifact_ref_id: Reference ID to the full artifact
        """
        intelligence = RawIntelligence(
            source_scout_id=source_scout_id,
            content_summary=content_summary,
            artifact_ref_id=artifact_ref_id
        )
        self.state.raw_intelligence.append(intelligence)
    
    def add_input_attachment(self, file_name: str, file_type: Literal["markdown", "pdf", "docx"], 
                           content_summary: str, full_content_ref: str, raw_text_snippet: str) -> None:
        """
        Add an input attachment to the state.
        
        Args:
            file_name: Name of the file
            file_type: Type of the file (must be one of "markdown", "pdf", "docx")
            content_summary: Summary of the content
            full_content_ref: Reference to the full content
            raw_text_snippet: Snippet of the raw text
        """
        attachment = InputAttachment(
            file_name=file_name,
            file_type=file_type,
            content_summary=content_summary,
            full_content_ref=full_content_ref,
            raw_text_snippet=raw_text_snippet
        )
        self.state.input_attachments.append(attachment)
    
    def get_state(self) -> GlobalState:
        """
        Get the current state.
        
        Returns:
            GlobalState: Current state object
        """
        return self.state
    
    def transition_to(self, status: GlobalStateStatus) -> None:
        """
        Transition the state to a new status.
        
        Args:
            status: New status
        """
        self.state.status = status
    
    def save_checkpoint(self) -> None:
        """
        Save the current state as a checkpoint in Redis.
        If Redis is not available, this method will silently skip persistence.
        """
        if self.redis_client is None:
            logger.debug("Redis not available, skipping checkpoint save")
            return
        
        try:
            state_json = self.state.json()
            self.redis_client.set(f"cpso_state:{self.state.request_id}", state_json)
            # Also save a timestamp for the checkpoint
            self.redis_client.set(f"cpso_state_timestamp:{self.state.request_id}", datetime.now().isoformat())
            logger.info(f"Saved checkpoint for request_id: {self.state.request_id}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint for request_id {self.state.request_id}: {str(e)}", exc_info=True)
            # 不抛出异常，允许系统在没有 Redis 的情况下继续运行
    
    def restore_state(self, request_id: str) -> Optional[GlobalState]:
        """
        Restore state from Redis.
        If Redis is not available, returns None (will create new state).
        
        Args:
            request_id: Request ID to restore state for
            
        Returns:
            GlobalState: Restored state object or None if not found or Redis unavailable
        """
        if self.redis_client is None:
            logger.debug("Redis not available, cannot restore state")
            return None
        
        try:
            state_json = self.redis_client.get(f"cpso_state:{request_id}")
            if state_json:
                # Decode bytes to string if needed
                if isinstance(state_json, bytes):
                    state_json = state_json.decode('utf-8')
                state_dict = json.loads(state_json)
                # Convert dict to GlobalState object
                return GlobalState(**state_dict)
            return None
        except Exception as e:
            logger.error(f"Failed to restore state for request_id {request_id}: {str(e)}", exc_info=True)
            return None
    
    def reset_state(self) -> None:
        """
        Reset the state to initial values, keeping the same request_id.
        """
        request_id = self.state.request_id
        self.state = GlobalState(
            request_id=request_id,
            status=GlobalStateStatus.SCOUTING,
            iteration_count=0,
            user_intent="",
            user_feedback_history=[],
            scout_instructions=[],
            raw_intelligence=[],
            consolidated_briefing="",
            technical_correction=None,
            strategy_draft="",
            audit_report="",
            input_attachments=[]
        )
        logger.info(f"Reset state for request_id: {request_id}")