"""
Technical Officer Node for CPSO-Protocol Multi-Agent System
Reviews strategies from a technical perspective and provides corrections.
"""

import logging
from typing import Dict, Any
from ..state.schema import GlobalState, GlobalStateStatus
from ..utils.llm_router import get_llm


# Set up logger
logger = logging.getLogger(__name__)


def technical_review(state: GlobalState) -> GlobalState:
    """
    Perform technical review of the strategy draft and provide corrections.
    
    This node acts as a Technical Officer, reviewing the strategy draft from 
    a technical perspective and generating corrections that will be used to
    refine the intelligence briefing and ultimately the strategy.
    
    Args:
        state (GlobalState): Current global state containing the strategy draft and audit report
        
    Returns:
        GlobalState: Updated state with technical corrections
    """
    try:
        # Check if we've exceeded maximum iterations
        if state.iteration_count >= 3:
            # Generate fallback report and end the loop
            state.technical_correction = "技术修正已达到最大迭代次数(3次)。建议人工介入处理剩余问题。"
            state.status = GlobalStateStatus.AWAITING_USER
            return state
        
        # Get the appropriate LLM for Technical Officer (uses high-level model like CPSO)
        llm = get_llm("tech")
        
        # Create prompt for technical review
        prompt = f"""
You are the Technical Officer for the CPSO-Protocol Multi-Agent System.
Your role is to provide technical expertise and corrections to strategic documents.

Audit Report:
{state.audit_report}

User Feedback History:
{state.user_feedback_history}

Strategy Draft:
{state.strategy_draft}

Consolidated Intelligence Briefing:
{state.consolidated_briefing}

Task:
1. Analyze the audit report and user feedback for technical issues
2. Identify specific technical inaccuracies or areas for improvement
3. Generate a technical correction that addresses these issues
4. Ensure the correction is actionable by the Intelligence Officer

Requirements:
- Focus only on technical aspects, not strategic or business elements
- Provide specific, actionable corrections
- Reference relevant sections of the strategy draft
- Format your response as a clear technical correction document
""".strip()
        
        # Generate technical correction using LLM
        response = llm.invoke(prompt)
        technical_correction = str(response.content)
        
        # Update state with technical correction
        state.technical_correction = technical_correction
        state.status = GlobalStateStatus.REFINING
        
        # Increment iteration counter to prevent infinite loops
        state.iteration_count += 1
        
        return state
    except Exception as e:
        logger.error(f"Error in technical_review: {str(e)}", exc_info=True)
        # Set error status in state
        state.status = GlobalStateStatus.AWAITING_USER
        # Add error info to state if there's a field for it, or re-raise
        raise