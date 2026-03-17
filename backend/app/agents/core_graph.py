"""
core_graph.py — LangGraph StateGraph definition and AsyncPostgresSaver checkpointer.
This is the wiring file — it registers nodes and edges but contains no business logic.
All logic lives in the individual node files.

Sprint 1: graph is built but not connected to the chat endpoint.
Sprint 3: chat.py imports build_graph() and streams it.
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.agents.state import AgentState
from app.agents.nodes.supervisor import supervisor_node
from app.agents.nodes.profiler import profiler_node
from app.agents.nodes.filter_node import filter_node
from app.agents.nodes.scoring_node import scoring_node
from app.agents.nodes.explanation_node import explanation_node
from app.agents.nodes.answer_node import answer_node


def route_by_intent(state: AgentState) -> str:
    """
    Conditional edge function — reads last_intent from state and routes accordingly.
    Called after SupervisorNode on every turn.
    """
    intent = state["last_intent"]

    if intent == "get_recommendation":
        # If profiling not complete, send to profiler regardless
        if not state.get("profiling_complete", False):
            return "profiler"
        return "filter_node"

    elif intent == "profile_update":
        return "profiler"

    elif intent in ("fee_query", "market_query", "follow_up", "clarification"):
        return "answer_node"

    else:  # out_of_scope
        return "answer_node"


def build_graph(checkpointer: AsyncPostgresSaver) -> StateGraph:
    """
    Build and compile the LangGraph StateGraph.
    Called once at app startup. Checkpointer persists AgentState to PostgreSQL.
    """
    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("supervisor",       supervisor_node)
    graph.add_node("profiler",         profiler_node)
    graph.add_node("filter_node",      filter_node)
    graph.add_node("scoring_node",     scoring_node)
    graph.add_node("explanation_node", explanation_node)
    graph.add_node("answer_node",      answer_node)

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor routes to all other nodes
    graph.add_conditional_edges("supervisor", route_by_intent, {
        "profiler":         "profiler",
        "filter_node":      "filter_node",
        "answer_node":      "answer_node",
    })

    # Recommendation pipeline: Filter → Score → Explain → END
    graph.add_edge("filter_node",      "scoring_node")
    graph.add_edge("scoring_node",     "explanation_node")
    graph.add_edge("explanation_node", END)

    # Other nodes → END
    graph.add_edge("profiler",    END)
    graph.add_edge("answer_node", END)

    return graph.compile(checkpointer=checkpointer)
