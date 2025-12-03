"""
Scout Node for CPSO-Protocol Multi-Agent System
Handles parallel scouting tasks to gather intelligence from web and other sources.
"""

import asyncio
import logging
from typing import List, Dict, Any, Union, Tuple
from ..state.schema import GlobalState, ScoutInstruction, RawIntelligence, GlobalStateStatus
from ..tools.web_search import web_search
from ..utils.artifact import ArtifactManager
from ..utils.llm_router import get_llm


# Set up logger
logger = logging.getLogger(__name__)


async def scout_instruction_async(instruction: ScoutInstruction) -> Union[Tuple[ScoutInstruction, RawIntelligence, str], Exception]:
    """
    Asynchronously execute a single scout instruction.
    
    Args:
        instruction (ScoutInstruction): The scout instruction to execute
        
    Returns:
        Union[Tuple[ScoutInstruction, RawIntelligence, str], Exception]: Either a tuple of results or an exception
    """
    # Initialize artifact manager
    artifact_manager = ArtifactManager()
    
    try:
        # Perform web search based on the instruction topic
        search_results = web_search(instruction.topic, num_results=3)
        
        # Handle case where search returns no results
        if not search_results:
            # Create fallback content when search fails
            combined_content = f"No search results found for topic: {instruction.topic}"
        else:
            # Combine search results into a single content string
            combined_content = "\n\n".join([
                f"Title: {result['title']}\nURL: {result['link']}\nSnippet: {result['snippet']}"
                for result in search_results
            ])
    except Exception as e:
        # Handle any exceptions during web search
        logger.error(f"Web search failed for topic '{instruction.topic}': {str(e)}", exc_info=True)
        combined_content = f"Failed to perform web search for topic: {instruction.topic}. Error: {str(e)}"
    
    try:
        # Create artifact from the combined content
        artifact_id = artifact_manager.create_artifact(
            content=combined_content,
            source=f"web_search:{instruction.topic}",
            metadata={
                "scout_id": instruction.id,
                "scout_role": instruction.role,
                "topic": instruction.topic
            }
        )
        
        # Generate content summary
        content_summary = artifact_manager.generate_summary(combined_content, max_length=500)
        
        # Create raw intelligence record
        raw_intelligence = RawIntelligence(
            source_scout_id=instruction.id,
            content_summary=content_summary,
            artifact_ref_id=artifact_id
        )
        
        # Update instruction status
        instruction.status = "done"
        
        return instruction, raw_intelligence, artifact_id
        
    except Exception as e:
        # Even if artifact creation fails, mark instruction as done to prevent hanging
        logger.error(f"Artifact creation failed for topic '{instruction.topic}': {str(e)}", exc_info=True)
        instruction.status = "done"
        raw_intelligence = RawIntelligence(
            source_scout_id=instruction.id,
            content_summary=f"Failed to process content for topic: {instruction.topic}. Error: {str(e)}",
            artifact_ref_id=""
        )
        artifact_id = ""
        
        return instruction, raw_intelligence, artifact_id


def scout_node(state: GlobalState) -> GlobalState:
    """
    Execute scouting tasks in parallel to gather intelligence.
    
    This node executes pending scout instructions in parallel, 
    gathering information from web searches and other sources.
    
    Args:
        state (GlobalState): Current global state containing scout instructions
        
    Returns:
        GlobalState: Updated state with raw intelligence from scouts
    """
    try:
        # Filter pending scout instructions
        pending_instructions = [
            instruction for instruction in state.scout_instructions 
            if instruction.status == "pending"
        ]
        
        # Create async tasks for each pending instruction
        async def process_instructions():
            tasks = [scout_instruction_async(instruction) for instruction in pending_instructions]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        # Run async tasks
        results = asyncio.run(process_instructions())
        
        # Process results
        for i, result in enumerate(results):
            # Handle exceptions that occurred during task execution
            if isinstance(result, Exception):
                # Log the exception but continue processing other results
                logger.error(f"Exception occurred during scout task: {result}", exc_info=True)
                # Create fallback data for failed task
                # We need to find which instruction failed - it's in the same order as pending_instructions
                if i < len(pending_instructions):
                    failed_instruction = pending_instructions[i]
                    failed_instruction.status = "done"  # Mark as done to prevent hanging
                    
                    # Create fallback intelligence
                    fallback_intelligence = RawIntelligence(
                        source_scout_id=failed_instruction.id,
                        content_summary=f"Failed to execute scout task for topic: {failed_instruction.topic}",
                        artifact_ref_id=""
                    )
                    state.raw_intelligence.append(fallback_intelligence)
                continue
                
            # Unpack successful result
            if isinstance(result, tuple) and len(result) == 3:
                instruction, raw_intelligence, artifact_id = result
            
                # Add to state's raw intelligence regardless of success/failure
                state.raw_intelligence.append(raw_intelligence)
                
                # Update instruction status in the state
                for inst in state.scout_instructions:
                    if inst.id == instruction.id:
                        inst.status = "done"
                        break
        
        return state
    except Exception as e:
        logger.error(f"Error in scout_node: {str(e)}", exc_info=True)
        # Set error status in state
        state.status = GlobalStateStatus.AWAITING_USER
        # Add error info to state if there's a field for it, or re-raise
        raise