"""
CPSO Node for CPSO-Protocol Multi-Agent System
Handles intent analysis and strategy generation.
"""

import logging
from typing import Dict, Any
from ..state.schema import GlobalState, GlobalStateStatus
from ..utils.llm_router import get_llm


# Set up logger
logger = logging.getLogger(__name__)


def intent_analysis(state: GlobalState) -> GlobalState:
    """
    Analyze user intent and generate scout instructions.
    
    This node acts as the Chief Planning & Strategy Officer,
    analyzing the user's intent and breaking it down into
    specific scouting tasks.
    
    Args:
        state (GlobalState): Current global state containing user intent
        
    Returns:
        GlobalState: Updated state with scout instructions
    """
    try:
        # Get the appropriate LLM for CPSO
        llm = get_llm("cpso")
        
        # Create prompt for intent analysis
        prompt = f"""
You are the Chief Planning & Strategy Officer (CPSO).
User Intent: {state.user_intent}

Task: Generate a list of scout instructions to gather intelligence.
Each instruction must follow this schema:
{{
  "id": "scout_1",
  "role": "market" | "tech" | "competitor",
  "topic": "具体要调查的主题",
  "status": "pending"
}}

Based on the user intent, generate 3-5 specific scouting tasks that will help gather
the necessary intelligence to create a comprehensive strategy.

Output ONLY valid JSON array.
""".strip()
        
        # Generate scout instructions using LLM
        response = llm.invoke(prompt)
        scout_instructions_text = response.content
        
        # In a full implementation, we would parse the JSON response
        # and update the state with the scout instructions
        # For now, we'll add placeholder instructions
        
        # Update state status
        state.status = GlobalStateStatus.SCOUTING
        
        return state
    except Exception as e:
        logger.error(f"Error in intent_analysis: {str(e)}", exc_info=True)
        # Set error status in state
        state.status = GlobalStateStatus.AWAITING_USER
        # Add error info to state if there's a field for it, or re-raise
        raise


def strategy_generation(state: GlobalState) -> GlobalState:
    """
    Generate strategic plan document based on consolidated briefing.
    
    This node acts as the Chief Planning & Strategy Officer,
    generating a comprehensive strategy document based on the
    consolidated intelligence briefing.
    
    Args:
        state (GlobalState): Current global state containing consolidated briefing
        
    Returns:
        GlobalState: Updated state with strategy draft
    """
    try:
        # Get the appropriate LLM for CPSO
        llm = get_llm("cpso")
        
        # Create prompt for strategy generation
        prompt = f"""
You are the Chief Planning & Strategy Officer (CPSO).
Consolidated Intelligence Briefing:
{state.consolidated_briefing}

Task: Generate a strategic plan document.

Requirements:
- Every claim must cite [Source: ID] from the briefing
- If no source exists, state "Data Missing"
- Use Markdown format with clear sections
- Focus on actionable insights and concrete recommendations
""".strip()
        
        # Generate strategy draft using LLM
        response = llm.invoke(prompt)
        strategy_draft = str(response.content)
        
        # Update state with strategy draft
        state.strategy_draft = strategy_draft
        state.status = GlobalStateStatus.AUDITING
        
        return state
    except Exception as e:
        logger.error(f"Error in strategy_generation: {str(e)}", exc_info=True)
        # Set error status in state
        state.status = GlobalStateStatus.AWAITING_USER
        # Add error info to state if there's a field for it, or re-raise
        raise