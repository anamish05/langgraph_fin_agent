import os
from dotenv import load_dotenv

# Load local .env if it exists
load_dotenv()

def get_secret(key_name: str) -> str:
    # 1. Check local environment variable
    val = os.getenv(key_name)
    if val:
        return val
    # 2. Check Streamlit cloud secrets (if running in Streamlit)
    try:
        import streamlit as st
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return ""

OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY")
TAVILY_API_KEY = get_secret("TAVILY_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Set Tavily in os.environ because the tool expects it there
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY