"""
Main LangGraph definition for CPSO-Protocol Multi-Agent System
Defines the state graph and flow between different nodes.
"""

from langgraph.graph import StateGraph, END
from .state.schema import GlobalState
from .nodes.cpso import intent_analysis, strategy_generation
from .nodes.scout import scout_node
from .nodes.auditor import adversarial_audit
from .nodes.tech import technical_review


def create_graph():
    """
    Create the main state graph for the CPSO protocol.
    
    The graph defines the flow between different nodes in the system:
    1. Intent Analysis (CPSO)
    2. Ingestion (Process input attachments)
    3. Scouting (Parallel)
    4. Intelligence Fusion (IO)
    5. Strategy Generation (CPSO)
    6. Adversarial Audit (Auditor)
    7. Technical Review (Technical Officer)
    8. END or loop back to Intelligence Fusion
    
    Returns:
        StateGraph: The compiled state graph
    """
    # Import nodes inside function to avoid circular imports
    from .nodes.io import process_input_attachments
    import importlib
    io_module = importlib.import_module(".nodes.io", package="cpsp_protocol")
    intelligence_fusion = getattr(io_module, "intelligence_fusion")
    
    # Create the state graph
    workflow = StateGraph(GlobalState)
    
    # Add nodes to the graph
    workflow.add_node("intent_analysis", intent_analysis)
    workflow.add_node("ingestion", process_input_attachments)
    workflow.add_node("scout", scout_node)
    workflow.add_node("intelligence_fusion", intelligence_fusion)
    workflow.add_node("strategy_generation", strategy_generation)
    workflow.add_node("adversarial_audit", adversarial_audit)
    workflow.add_node("technical_review", technical_review)
    
    # Add edges between nodes
    workflow.set_entry_point("intent_analysis")
    
    # Conditional routing based on input attachments
    def route_after_intent(state: GlobalState):
        """
        Route based on whether there are input attachments:
        - If there are attachments, go to ingestion
        - Otherwise, go directly to scout
        """
        if hasattr(state, 'input_attachments') and state.input_attachments:
            return "ingestion"
        else:
            return "scout"
    
    workflow.add_conditional_edges(
        "intent_analysis",
        route_after_intent,
        {
            "ingestion": "ingestion",
            "scout": "scout"
        }
    )
    
    # Connect ingestion to scout
    workflow.add_edge("ingestion", "scout")
    
    workflow.add_edge("scout", "intelligence_fusion")
    workflow.add_edge("intelligence_fusion", "strategy_generation")
    workflow.add_edge("strategy_generation", "adversarial_audit")
    
    # Conditional edges based on audit result
    def audit_router(state: GlobalState):
        """
        Route based on audit result:
        - If audit passed, go to END
        - If audit requires changes, go to technical review
        """
        if "Status: Reject" in state.audit_report or "Status: Conditional" in state.audit_report:
            return "technical_review"
        else:
            return "END"
    
    workflow.add_conditional_edges(
        "adversarial_audit",
        audit_router,
        {
            "technical_review": "technical_review",
            "END": END
        }
    )
    
    # Conditional edges based on technical review result
    def technical_router(state: GlobalState):
        """
        Route based on technical review result:
        - If we've reached max iterations, go to END
        - Otherwise, loop back to intelligence fusion
        """
        if state.iteration_count >= 3:
            return "END"
        else:
            return "intelligence_fusion"
    
    workflow.add_conditional_edges(
        "technical_review",
        technical_router,
        {
            "intelligence_fusion": "intelligence_fusion",
            "END": END
        }
    )
    
    # Add edge from intelligence fusion back to strategy generation (loop)
    workflow.add_edge("intelligence_fusion", "strategy_generation")
    
    # Compile the graph
    app = workflow.compile()
    
    return app