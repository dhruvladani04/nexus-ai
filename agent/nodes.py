from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_google_genai import GoogleGenerativeAIEmbeddings

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from database.mongo import mongo_handler
from agent.prompts import ROUTER_SYSTEM_PROMPT, RESUME_QA_PROMPT, LEARNING_QA_PROMPT, PLANNER_PROMPT
from agent.state import AgentState

# Initialize LLM
llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, google_api_key=settings.GOOGLE_API_KEY)

# Initialize Vector Store (Re-using logic, but cleaner to have a helper)
embeddings = GoogleGenerativeAIEmbeddings(
     model=settings.EMBEDDING_MODEL,
     google_api_key=settings.GOOGLE_API_KEY
)

vector_store = MongoDBAtlasVectorSearch(
    collection=mongo_handler.get_collection(),
    embedding=embeddings,
    index_name=settings.INDEX_NAME,
    relevance_score_fn=settings.VECTOR_SEARCH_METRIC
)

def retrieve_documents(query: str, source_type: str) -> str:
    # Filter by source_type
    filter_query = {"source_type": source_type}
    try:
        results = vector_store.similarity_search(query, k=5, pre_filter=filter_query)
        return "\n\n".join([f"Source: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content}" for doc in results])
    except Exception as e:
        print(f"Retrieval Error: {e}")
        return ""

def router_node(state: AgentState):
    """
    Classifies the user's query.
    """
    messages = [
        SystemMessage(content=ROUTER_SYSTEM_PROMPT),
        HumanMessage(content=state["query"])
    ]
    response = llm.invoke(messages)
    decision = response.content.strip().lower()
    
    # Fallback/Safety
    if decision not in ["resume", "video", "web", "planner"]:
        decision = "web" # default
    
    return {"decision": decision}

def resume_node(state: AgentState):
    """
    Handles Resume specific queries.
    """
    query = state["query"]
    context = retrieve_documents(query, "resume")
    
    prompt = RESUME_QA_PROMPT.format(context=context, question=query)
    response = llm.invoke(prompt)
    
    return {"generation": response.content, "documents": [context]}

def video_node(state: AgentState):
    """
    Handles Video learning queries.
    """
    query = state["query"]
    context = retrieve_documents(query, "video")
    
    prompt = LEARNING_QA_PROMPT.format(context=context, question=query)
    response = llm.invoke(prompt)
    
    return {"generation": response.content, "documents": [context]}

def web_node(state: AgentState):
    """
    Handles Web learning queries.
    """
    query = state["query"]
    context = retrieve_documents(query, "web")
    
    prompt = LEARNING_QA_PROMPT.format(context=context, question=query)
    response = llm.invoke(prompt)
    
    return {"generation": response.content, "documents": [context]}

def planner_node(state: AgentState):
    """
    Handles complex planning queries.
    """
    query = state["query"]
    prompt = PLANNER_PROMPT.format(question=query)
    response = llm.invoke(prompt)
    
    return {"generation": response.content}
