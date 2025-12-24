import streamlit as st
import subprocess
import os
import sys

# Add root to path
sys.path.append(os.path.dirname(__file__))

# Workaround for Streamlit + Google GenAI (gRPC) threading issue
import asyncio
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Sidebar - Configuration (BYOK)
st.sidebar.header("🔑 API Configuration")
st.sidebar.info("Enter your own API keys to use the app.")

# 1. Check for Keys in Environment (local dev) or Session State (user input)
env_google_key = os.getenv("GOOGLE_API_KEY")
env_mongo_uri = os.getenv("MONGO_URI")

# 2. Input Fields (Pre-fill if env var exists, masking partially could be good but let's keep simple)
user_google_key = st.sidebar.text_input("Google API Key", value=env_google_key if env_google_key else "", type="password")
user_mongo_uri = st.sidebar.text_input("MongoDB URI", value=env_mongo_uri if env_mongo_uri else "", type="password")

# 3. Validation Gate
if not user_google_key or not user_mongo_uri:
    st.warning("⚠️ Please enter both your **Google API Key** and **MongoDB URI** in the sidebar to proceed.")
    st.markdown("Don't have keys? [Get Google Key](https://aistudio.google.com/) | [Get MongoDB Atlas](https://www.mongodb.com/cloud/atlas)")
    st.stop() # Stop execution until keys are present

# 4. Set Environment Variables for the session
os.environ["GOOGLE_API_KEY"] = user_google_key
os.environ["MONGO_URI"] = user_mongo_uri

# Force reload settings if they were already imported (hacky but needed for Streamlit's execution model)
from config import settings
import importlib
importlib.reload(settings)
if settings.GOOGLE_API_KEY != user_google_key:
    settings.GOOGLE_API_KEY = user_google_key
if settings.MONGO_URI != user_mongo_uri:
    settings.MONGO_URI = user_mongo_uri

# Now safe to import logic that depends on settings
from agent.graph import app_graph

st.set_page_config(page_title="Nexus AI", layout="wide")

st.title("🌌 Nexus: Enterprise Multi-Agent RAG")

# Sidebar - Ingestion
st.sidebar.header("📥 Data Ingestion")
source_type = st.sidebar.selectbox("Source Type", ["resume", "video", "web"])

url_input = ""
uploaded_file = None

if source_type == "resume":
    uploaded_file = st.sidebar.file_uploader("Upload Resume (PDF)", type=["pdf"])
else:
    url_input = st.sidebar.text_input("URL")

import tempfile

if st.sidebar.button("Ingest Data"):
    if source_type == "resume" and uploaded_file:
        with st.sidebar.status("Ingesting uploaded file...") as status:
            try:
                # Save uploaded file safely using tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    temp_path = tmp_file.name
                
                cmd = [sys.executable, "-m", "data_pipeline.ingestion", "--type", source_type, "--url", temp_path]
                
                # Use absolute path for CWD to avoid empty string error
                current_dir = os.path.dirname(os.path.abspath(__file__))
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=current_dir)
                
                # Cleanup
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path) # unlink is better for temp files
                    except:
                        pass # Ignore cleanup errors

                if result.returncode == 0:
                    status.update(label="Ingestion Complete!", state="complete", expanded=True)
                    st.sidebar.success(result.stdout)
                else:
                    status.update(label="Ingestion Failed", state="error", expanded=True)
                    st.sidebar.error(result.stderr)
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

    elif source_type != "resume" and url_input:
        with st.sidebar.status(f"Ingesting from {source_type}...") as status:
            try:
                cmd = [sys.executable, "-m", "data_pipeline.ingestion", "--type", source_type, "--url", url_input]
                
                current_dir = os.path.dirname(os.path.abspath(__file__))
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=current_dir)
                
                if result.returncode == 0:
                    status.update(label="Ingestion Complete!", state="complete", expanded=True)
                    st.sidebar.success(result.stdout)
                else:
                    status.update(label="Ingestion Failed", state="error", expanded=True)
                    st.sidebar.error(result.stderr)
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("Please provide a URL or upload a file.")

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "thought_process" in message:
            with st.expander("🧠 Thought Process"):
                st.write(f"**Route Selected:** {message['thought_process']}")

query = st.chat_input("Ask something about the knowledge base...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Run Agent
                initial_state = {"query": query, "messages": []}
                result = app_graph.invoke(initial_state)
                
                response = result.get("generation", "I couldn't generate a response.")
                decision = result.get("decision", "unknown")
                
                st.markdown(response)
                with st.expander("🧠 Thought Process"):
                    st.write(f"**Route Selected:** {decision}")
                    
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "thought_process": decision
                })
            except Exception as e:
                st.error(f"An error occurred: {e}")

