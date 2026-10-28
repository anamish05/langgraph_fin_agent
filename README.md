# 📊 Financial Intelligence & Screening Agent

This notebook implements an automated, multi-agent qualitative research workflow using **LangGraph**, **Tavily Search**, and structured **Pydantic** extraction schemas.

---

### Workflow Objectives
1. **Input Ingestion:** Accepts up to 5 company names or ticker symbols.
2. **Dynamic Query Planning:** Generates targeted search queries for corporate identity, executive details, industry classifications, and recent performance.
3. **Web Intelligence Retrieval:** Queries real-time market data via Tavily API.
4. **Structured Qualitative Synthesis:** Uses an LLM to map unstructured findings into standardized schemas (`CompanyProfile`).
5. **Excel Enrichment:** Exports original inputs alongside newly gathered intelligence into a multi-tab Excel workbook (`_enriched.xlsx`).

---
### Architecture pipeline  

[User Input]  
     │  
     ▼  
[Input Parser Node] ────────► Validates company names/tickers (caps at 5)  
     │  
     ▼  
[Query Planner Node] ───────► Generates 3 targeted web queries per company  
     │  
     ▼  
[Web Research Node] ────────► Gathers live data via Tavily Search API  
     │  
     ▼  
[Synthesis & Export Node] ──► Validates via Pydantic & writes multi-sheet Excel  
