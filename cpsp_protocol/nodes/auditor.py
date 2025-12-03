"""
Audit Node for CPSO-Protocol Multi-Agent System
Performs adversarial audit of strategic plans to ensure compliance and logical consistency.
"""

import logging
from typing import Dict, Any
from ..state.schema import GlobalState, GlobalStateStatus
from ..utils.llm_router import get_llm


# Set up logger
logger = logging.getLogger(__name__)


def adversarial_audit(state: GlobalState) -> GlobalState:
    """
    Perform adversarial audit of the strategy draft.
    
    This node acts as an Auditor, performing a critical review of the strategy
    document to identify logical flaws, compliance issues, and potential risks.
    
    Args:
        state (GlobalState): Current global state containing the strategy draft
        
    Returns:
        GlobalState: Updated state with audit report
    """
    try:
        # Get the appropriate LLM for Auditor (uses high-level model like CPSO)
        llm = get_llm("auditor")
        
        # Create prompt for adversarial audit
        prompt = f"""
You are the Auditor for the CPSO-Protocol Multi-Agent System.
Your role is to perform a critical review of strategic documents to ensure
compliance, logical consistency, and identify potential risks.

Strategy Draft for Review:
{state.strategy_draft}

Consolidated Intelligence Briefing:
{state.consolidated_briefing}

Task:
1. Review the strategy draft for logical consistency
2. Check that all claims are properly cited with [Source: ID] references
3. Identify any potential compliance issues or risks
4. Evaluate if the strategy aligns with the intelligence briefing
5. Provide specific recommendations for improvement

Requirements:
- Every identified issue must reference a specific section of the strategy draft
- Provide a clear risk rating for each issue (High/Medium/Low)
- Suggest concrete improvements or corrections
- Format your response as a detailed Markdown audit report with clear sections

Audit Report Format:
# Audit Report

## Overall Status
[Pass/Conditional/Reject]

## Compliance Check
- [List compliance checks performed and results]

## Logical Consistency Review
- [List any logical inconsistencies found]

## Risk Assessment
- [List identified risks with severity ratings]

## Recommendations
- [List specific recommendations for improvement]

## Citation Integrity Check
- [Verify that all claims are properly cited]
""".strip()
        
        # Generate audit report using LLM
        response = llm.invoke(prompt)
        audit_report = str(response.content)
        
        # Update state with audit report
        state.audit_report = audit_report
        
        # If audit report contains "Status: Reject", set status to awaiting_user
        # Otherwise, mark as completed
        if "Status: Reject" in audit_report or "Status: Conditional" in audit_report:
            state.status = GlobalStateStatus.AWAITING_USER
        else:
            state.status = GlobalStateStatus.COMPLETED
        
        return state
    except Exception as e:
        logger.error(f"Error in adversarial_audit: {str(e)}", exc_info=True)
        # Set error status in state
        state.status = GlobalStateStatus.AWAITING_USER
        # Add error info to state if there's a field for it, or re-raise
        raise