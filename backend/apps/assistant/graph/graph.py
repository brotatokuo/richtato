"""LangGraph ReAct agent graph definition."""

from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .tools import ALL_TOOLS


def _should_continue(state: AgentState) -> str:
    """Route to tools if the last message has tool calls, otherwise end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def build_graph():
    """Build and compile the ReAct agent graph.

    Returns a compiled StateGraph (without a checkpointer — the caller
    is responsible for attaching one at invocation time).
    """
    llm = ChatGoogleGenerativeAI(
        model=settings.ASSISTANT_MODEL,
        google_api_key=settings.GOOGLE_AI_API_KEY,
        temperature=0.3,
        convert_system_message_to_human=True,
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def call_model(state: AgentState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode(ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
