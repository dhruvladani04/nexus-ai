from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    The state of the agent graph.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    query: str
    documents: List[str]
    generation: str
    decision: str  # To track which path was taken for UI
