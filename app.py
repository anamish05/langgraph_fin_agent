import streamlit as st
import pandas as pd
from src.graph import build_financial_workflow

st.set_page_config(page_title="Financial Intelligence Agent", layout="wide")

# ==============================================================================
# PAGE 1: AGENT RUNNER
# ==============================================================================
def run_agent_page():
    st.title("📊 Financial Intelligence Screener")
    st.caption("AI-powered qualitative research agent using LangGraph & Tavily")

    # Sidebar: Target Companies
    st.sidebar.header("1. Target Companies (Max 5)")
    raw_input = st.sidebar.text_area(
        "Enter companies/tickers (comma or line separated):",
        value="Tesla, Apple, CrowdStrike",
        placeholder="e.g. NVDA, MSFT, Amazon",
        height=90
    )
    
    parsed = [item.strip() for item in raw_input.replace("\n", ",").split(",") if item.strip()] if raw_input else []
    selected_companies = parsed[:5]
    if len(parsed) > 5:
        st.sidebar.warning(f"Capped at first 5 companies (received {len(parsed)}).")
    st.sidebar.caption(f"Queue ({len(selected_companies)}/5): {', '.join(selected_companies)}")

    # Sidebar: Task Prompt
    st.sidebar.header("2. Agent Task")
    task_preset = st.sidebar.selectbox(
        "Choose task template:",
        [
            "Standard Due Diligence",
            "Risk & Headwinds Focus",
            "Market Identity Only",
            "Custom"
        ]
    )

    preset_map = {
        "Standard Due Diligence": "Identify industry SIC/NAICS codes, primary exchange/ticker, CEO/HQ, business model breakdown, and recent performance outlook.",
        "Risk & Headwinds Focus": "Identify primary business model, recent regulatory or supply chain risks, competitive moat, and whether headwinds make it risky for investment.",
        "Market Identity Only": "Find official company name, primary SIC code, primary NAICS code, primary listing exchange, and a 1-paragraph summary of revenue generation.",
        "Custom": "Identify SIC/NAICS codes, exchange/ticker, CEO/HQ, business model, and recent performance outlook."
    }

    task_description = st.sidebar.text_area("Task Instructions:", value=preset_map[task_preset], height=200)

    # Main Execution Area
    st.info(f"**Active Task:** {task_description}")

    if st.button("🚀 Run Agent Analysis", type="primary", use_container_width=False):
        if not selected_companies:
            st.error("Please enter at least one company or ticker.")
        else:
            with st.status("Agent Pipeline Execution", expanded=True) as status:
                st.write("📋 Parsing inputs and creating work batch...")
                temp_file = "temp_input.xlsx"
                pd.DataFrame({"Company": selected_companies}).to_excel(temp_file, index=False)

                st.write("🔍 Running LangGraph queries and gathering web intelligence...")
                app = build_financial_workflow()
                res = app.invoke({
                    "input_file": temp_file,
                    "task_description": task_description,
                    "output_path": ""
                })
                status.update(label="Complete!", state="complete", expanded=False)

            enriched_file = res["output_path"]
            df_out = pd.read_excel(enriched_file, sheet_name="Company_Intelligence")

            st.markdown("---")
            st.header("📈 Screening Results")

            # Individual Company Cards
            company_names = df_out["company_name"].tolist() if "company_name" in df_out.columns else [f"Company {i+1}" for i in range(len(df_out))]
            tabs = st.tabs(company_names)

            for tab, (_, row) in zip(tabs, df_out.iterrows()):
                with tab:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Ticker & Exchange", str(row.get("ticker_and_exchange", "N/A")))
                    c2.metric("Industry / Sector", str(row.get("industry_sector", "N/A")))
                    c3.metric("SIC / NAICS Code", str(row.get("sic_naics_code", "N/A")))

                    st.write(f"**CEO & Headquarters:** {row.get('ceo_and_hq', 'N/A')}")
                    st.markdown("**💼 Core Business Model**")
                    st.info(row.get("business_model", "N/A"))
                    st.markdown("**📊 Current Performance & Outlook**")
                    st.warning(row.get("current_performance_and_outlook", "N/A"))

            # Comparison Table
            with st.expander("📋 Full Comparison Table", expanded=False):
                st.dataframe(df_out, use_container_width=True)

            # Excel Download
            with open(enriched_file, "rb") as f:
                st.download_button(
                    "📥 Download Enriched Excel (.xlsx)",
                    data=f,
                    file_name="Company_Intelligence_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )


# ==============================================================================
# PAGE 2: ARCHITECTURE & LANGGRAPH SCHEMA
# ==============================================================================
def show_architecture_page():
    st.title("📐 LangGraph Architecture")
    st.caption("Linear 4-node deterministic pipeline with state passing")

    # Render Visual Diagram
    st.image("image_0.png", caption="LangGraph Execution Graph", use_container_width=True)

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Key Architecture Pillars")
        st.markdown(
            """
            - **Linear StateGraph:** Ensures reliable state transitions without uncontrolled loops.
            - **Hybrid LLM Routing:** Uses `gpt-4o-mini` for query planning and `gpt-4o` for schema enforcement.
            - **Structured Output:** Strictly validates extractions via Pydantic schemas.
            """
        )

    with c2:
        st.subheader("Node Breakdown")
        st.markdown(
            """
            1. **Input Parser:** Validates company tickers and caps queue at 5.
            2. **Query Planner:** Generates 3 targeted web queries per company.
            3. **Web Research:** Queries Tavily API for live disclosures and news.
            4. **Synthesis & Export:** Parses findings into Pydantic models and writes multi-sheet Excel.
            """
        )


# ==============================================================================
# MULTIPAGE ROUTING
# ==============================================================================
pg = st.navigation({
    "Workspace": [
        st.Page(run_agent_page, title="Agent Runner", icon="🚀"),
        st.Page(show_architecture_page, title="Architecture Schema", icon="📐")
    ]
})
pg.run()