"""
Advanced Audit Node for CPSO-Protocol Multi-Agent System
Extends the basic audit functionality with configurable policies and enhanced checking dimensions.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel
from ..state.schema import GlobalState, GlobalStateStatus
from ..utils.llm_router import get_llm


# Set up logger
logger = logging.getLogger(__name__)


class AuditDimension(BaseModel):
    """Configuration for a single audit dimension."""
    name: str
    enabled: bool
    weight: float  # 0.0 to 1.0
    description: str


class AuditConfiguration(BaseModel):
    """Configuration for audit policies."""
    strictness: str = "standard"
    dimensions: List[AuditDimension]
    enable_visualization: bool = True


class AuditFinding(BaseModel):
    """Represents a single finding from the audit process."""
    dimension: str
    severity: str
    description: str
    recommendation: str
    location: Optional[str] = None


class StructuredAuditReport(BaseModel):
    """Structured representation of the audit report."""
    overall_status: str
    findings: List[AuditFinding]
    score: float  # 0.0 to 100.0
    generated_at: datetime
    summary: str


# Default audit configuration
DEFAULT_DIMENSIONS = [
    AuditDimension(
        name="compliance_check",
        enabled=True,
        weight=0.2,
        description="Check that all claims are properly cited with [Source: ID] references"
    ),
    AuditDimension(
        name="logical_consistency",
        enabled=True,
        weight=0.2,
        description="Review the strategy draft for logical consistency"
    ),
    AuditDimension(
        name="risk_assessment",
        enabled=True,
        weight=0.15,
        description="Identify potential compliance issues or risks"
    ),
    AuditDimension(
        name="market_data_freshness",
        enabled=True,
        weight=0.15,
        description="Check freshness of market data and statistics"
    ),
    AuditDimension(
        name="competitor_analysis",
        enabled=True,
        weight=0.1,
        description="Ensure competitor analysis is comprehensive"
    ),
    AuditDimension(
        name="technical_feasibility",
        enabled=True,
        weight=0.1,
        description="Evaluate technical feasibility of proposed solutions"
    ),
    AuditDimension(
        name="financial_realism",
        enabled=True,
        weight=0.1,
        description="Verify financial projections are realistic"
    )
]

DEFAULT_AUDIT_CONFIG = AuditConfiguration(dimensions=[])


def advanced_adversarial_audit(state: GlobalState) -> GlobalState:
    """
    Perform advanced adversarial audit of the strategy draft with configurable policies.
    
    This node acts as an advanced Auditor, performing a critical review of the strategy
    document with enhanced checking dimensions and configurable policies.
    
    Args:
        state (GlobalState): Current global state containing the strategy draft
        
    Returns:
        GlobalState: Updated state with structured audit report
    """
    try:
        # Get audit configuration from state or use default
        audit_config = state.audit_config if state.audit_config is not None else DEFAULT_AUDIT_CONFIG
        
        # Get the appropriate LLM for Auditor (uses high-level model like CPSO)
        llm = get_llm("auditor")
        
        # Build prompt based on enabled dimensions
        enabled_dimensions = [dim for dim in DEFAULT_DIMENSIONS if getattr(audit_config, f'enable_{dim.name}', True)]
        dimensions_description = "\n".join([
            f"{i+1}. {dim.name}: {dim.description}" 
            for i, dim in enumerate(enabled_dimensions)
        ])
        
        # Create prompt for advanced adversarial audit
        prompt = f"""
You are the Advanced Auditor for the CPSO-Protocol Multi-Agent System.
Your role is to perform a critical review of strategic documents with enhanced checking capabilities.

Strategy Draft for Review:
{state.strategy_draft}

Consolidated Intelligence Briefing:
{state.consolidated_briefing}

Audit Configuration:
- Strictness Level: {audit_config.strictness}
- Enabled Checking Dimensions:
{dimensions_description}

Task:
Perform a comprehensive audit of the strategy draft based on the enabled dimensions above.
For each dimension, evaluate the strategy and identify specific issues with:
1. Severity (high/medium/low)
2. Detailed description of the issue
3. Specific recommendation for improvement
4. Location/section reference in the strategy draft (if applicable)

Requirements:
- Every identified issue must reference a specific section of the strategy draft
- Provide a clear risk rating for each issue (High/Medium/Low)
- Suggest concrete improvements or corrections
- Evaluate the overall quality and assign a score from 0-100
- Determine an overall status (pass/conditional/reject) based on findings

Output Format:
Respond with a JSON object that conforms to this structure:
{{
  "overall_status": "pass|conditional|reject",
  "findings": [
    {{
      "dimension": "name_of_dimension",
      "severity": "high|medium|low",
      "description": "detailed description of the issue",
      "recommendation": "specific recommendation for improvement",
      "location": "optional section reference"
    }}
  ],
  "score": 0-100,
  "summary": "brief summary of the audit results"
}}
""".strip()
        
        # Generate audit report using LLM
        response = llm.invoke(prompt)
        audit_result_json = str(response.content)
        
        # Parse the JSON response
        try:
            audit_result = json.loads(audit_result_json)
            structured_report = StructuredAuditReport(
                overall_status=audit_result["overall_status"],
                findings=[AuditFinding(**finding) for finding in audit_result["findings"]],
                score=audit_result["score"],
                generated_at=datetime.now(),
                summary=audit_result["summary"]
            )
            
            # Update state with structured audit report (serialized as JSON)
            state.audit_report = structured_report.json()
            
            # If audit report contains "reject" or "conditional", set status to awaiting_user
            # Otherwise, mark as completed
            if structured_report.overall_status == "reject" or structured_report.overall_status == "conditional":
                state.status = GlobalStateStatus.AWAITING_USER
            else:
                state.status = GlobalStateStatus.COMPLETED
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse audit result JSON: {str(e)}")
            # Fall back to basic audit if JSON parsing fails
            state.audit_report = audit_result_json
            # Since we couldn't parse the result, conservatively set status to awaiting_user
            state.status = GlobalStateStatus.AWAITING_USER
        
        return state
    except Exception as e:
        logger.error(f"Error in advanced_adversarial_audit: {str(e)}", exc_info=True)
        # Set error status in state
        state.status = GlobalStateStatus.AWAITING_USER
        # Add error info to state if there's a field for it, or re-raise
        raise