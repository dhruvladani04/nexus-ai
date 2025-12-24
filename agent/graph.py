from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import router_node, resume_node, video_node, web_node, planner_node

# Define initialization
graph = StateGraph(AgentState)

# Add Nodes
graph.add_node("router", router_node)
graph.add_node("resume", resume_node)
graph.add_node("video", video_node)
graph.add_node("web", web_node)
graph.add_node("planner", planner_node)

# Set Entry Point
graph.set_entry_point("router")

# Define Conditional Edges
def route_decision(state: AgentState):
    return state["decision"]

graph.add_conditional_edges(
    "router",
    route_decision,
    {
        "resume": "resume",
        "video": "video",
        "web": "web",
        "planner": "planner"
    }
)

# Set Finish Points
# All worker nodes end the turn
graph.add_edge("resume", END)
graph.add_edge("video", END)
graph.add_edge("web", END)
graph.add_edge("planner", END)

# Compile Graph
app_graph = graph.compile()
