import os
import json
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
import pandas as pd
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from src.config import OPENROUTER_API_KEY, BASE_URL
from src.schemas import CompanyProfile, SearchPlan



if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is missing! "
        "Please add it to Streamlit App Settings -> Secrets or your local .env file."
    )

class FinancialAgentState(TypedDict):
    input_file: str
    task_description: str

    # Extracted input companies
    companies: List[str]

    # Research plan and results
    search_queries: List[str]
    company_profiles: List[Dict[str, Any]]

    # Results
    output_path: str
    status_summary: str

# model for calcs
heavy_llm = ChatOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=BASE_URL,
    model="gpt-4o",
    temperature=0.1
)
# Alternative: claude-3-7-sonnet-20250219 or o3-mini

# 2. Fast/economic model: Query planning & keyword generation
fast_llm = ChatOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=BASE_URL,
    model="openai/gpt-4o-mini" ,
    temperature=0.3
)

search_tool = TavilySearchResults(max_results=3)

def parse_input_node(state: FinancialAgentState) -> Dict[str, Any]:
    """Reads company names or tickers from the Excel input file."""
    print("🔹 [1/4] Reading company list from Excel...")
    df = pd.read_excel(state["input_file"])
    
    # Extract values from the first column or column named 'Company'/'Ticker'
    col = df.columns[0]
    for candidate in ["Company", "company", "Ticker", "ticker", "Name", "name"]:
        if candidate in df.columns:
            col = candidate
            break

    company_list = df[col].dropna().astype(str).tolist()
    return {"companies": company_list}


def plan_research_node(state: FinancialAgentState) -> Dict[str, Any]:
    """Generates targeted search queries for each company."""
    print("🔹 [2/4] Planning qualitative search queries...")
    all_queries = []
    
    structured_planner = fast_llm.with_structured_output(SearchPlan)
    for company in state["companies"]:
        prompt = f"""
        Company/Ticker: "{company}"
        Task: "{state['task_description']}"
        
        Generate 3 search queries to find:
        1. Primary SIC code, NAICS code, and headquarters
        2. Stock exchange, ticker, and current CEO
        3. Core business model, current financial performance, and recent investment outlook
        """
        plan = structured_planner.invoke(prompt)
        all_queries.extend(plan.queries)

    return {"search_queries": all_queries}


def web_research_node(state: FinancialAgentState) -> Dict[str, Any]:
    """Runs web searches and extracts structured qualitative profiles."""
    print("🔹 [3/4] Searching web for qualitative profiles and performance...")
    profiles = []

    structured_profiler = heavy_llm.with_structured_output(CompanyProfile)

    # Process search per company
    queries_per_company = len(state["search_queries"]) // max(len(state["companies"]), 1)
    
    for idx, company in enumerate(state["companies"]):
        comp_queries = state["search_queries"][idx * queries_per_company : (idx + 1) * queries_per_company]
        search_results = []
        for q in comp_queries:
            try:
                res = search_tool.invoke({"query": q})
                search_results.extend([r.get("content", "") for r in res])
            except Exception as e:
                search_results.append(f"Search error for '{q}': {str(e)}")

        combined_text = "\n---\n".join(search_results[:6])

        profile = structured_profiler.invoke(f"""
        Analyze the search results for company/ticker: "{company}".
        
        Search Results:
        {combined_text}

        Extract:
        - Exact company name
        - Stock exchange & ticker
        - Industry sector & Primary SIC / NAICS codes
        - Current CEO & Headquarters location
        - 2 sentences summary of business model
        - 2 sentences summary of how the company is performing now and whether it is worth considering for investment
        """)
        profiles.append(profile.model_dump())

    return {"company_profiles": profiles}


def enrich_and_export_node(state: FinancialAgentState) -> Dict[str, Any]:
    """Appends qualitative data to the original Excel file and saves as _enriched.xlsx."""
    print("🔹 [4/4] Writing enriched qualitative data to Excel...")

    df_original = pd.read_excel(state["input_file"])
    df_enriched = pd.DataFrame(state["company_profiles"])

    output_filename = state["input_file"].replace(".xlsx", "_enriched.xlsx")
    if output_filename == state["input_file"]:
        output_filename = "companies_enriched.xlsx"

    with pd.ExcelWriter(output_filename, engine="openpyxl") as writer:
        df_original.to_excel(writer, sheet_name="Original_Input", index=False)
        df_enriched.to_excel(writer, sheet_name="Company_Intelligence", index=False)

    return {
        "output_path": output_filename,
        "status_summary": f"Successfully created {output_filename} with 'Original_Input' and 'Company_Intelligence' sheets."
    }

def build_financial_workflow():
    workflow = StateGraph(FinancialAgentState)
    
    workflow.add_node("parse_input", parse_input_node)
    workflow.add_node("plan_research", plan_research_node)
    workflow.add_node("web_research", web_research_node)
    workflow.add_node("enrich_and_export", enrich_and_export_node)

    workflow.add_edge(START, "parse_input")
    workflow.add_edge("parse_input", "plan_research")
    workflow.add_edge("plan_research", "web_research")
    workflow.add_edge("web_research", "enrich_and_export")
    workflow.add_edge("enrich_and_export", END)
    
    return workflow.compile()
