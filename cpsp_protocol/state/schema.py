"""
Global State Schema for CPSO-Protocol Multi-Agent System
"""

from typing import List, Dict, Optional, Literal, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class GlobalStateStatus(str, Enum):
    SCOUTING = "scouting"
    DRAFTING = "drafting"
    AUDITING = "auditing"
    AWAITING_USER = "awaiting_user"
    REFINING = "refining"
    COMPLETED = "completed"


class AuditConfiguration(BaseModel):
    """Configuration for audit policies."""
    strictness: str = "standard"
    enable_market_data_freshness: bool = True
    enable_competitor_analysis: bool = True
    enable_technical_feasibility: bool = True
    enable_financial_realism: bool = True
    enable_visualization: bool = True
    dimensions: List[str] = []


class UserFeedback(BaseModel):
    role: Literal["user"]
    type: Literal["strategic", "technical"]
    content: str
    timestamp: float


class ScoutInstruction(BaseModel):
    id: str
    role: Literal["market", "tech", "competitor"]
    topic: str
    status: Literal["pending", "done"]


class RawIntelligence(BaseModel):
    source_scout_id: str
    content_summary: str
    artifact_ref_id: str


class InputAttachment(BaseModel):
    file_name: str
    file_type: Literal["markdown", "pdf", "docx"]
    content_summary: str
    full_content_ref: str
    raw_text_snippet: str


class GlobalState(BaseModel):
    # 1. 元数据
    request_id: str
    status: GlobalStateStatus
    iteration_count: int  # 防止死锁，最大允许 3 次大循环

    # 2. 输入数据
    user_intent: str  # 原始需求
    user_feedback_history: List[UserFeedback]

    # 3. 中间产物 (Artifacts)
    scout_instructions: List[ScoutInstruction]
    raw_intelligence: List[RawIntelligence]

    # 4. 核心资产
    consolidated_briefing: str  # Markdown, 情报官产出
    technical_correction: Optional[str]  # 技术官产出，用于修正情报
    strategy_draft: str  # Markdown, CPSO产出
    audit_report: str  # Markdown, Auditor产出
    
    # 5. 审计配置
    audit_config: Optional[AuditConfiguration] = None
    
    # 6. 附件数据 (协议补丁 v12.5.1)
    input_attachments: List[InputAttachment]