# pydantic models
from pydantic import BaseModel, Field
from typing import List

class CompanyProfile(BaseModel):
    company_name: str = Field(description="Standardized name of the company")
    ticker_and_exchange: str = Field(description="Stock ticker and exchange (e.g., TSLA (NASDAQ)), or 'Private'")
    industry_sector: str = Field(description="Sector and industry classification")
    sic_naics_code: str = Field(description="Primary SIC and/or NAICS code, or 'N/A' if private/unknown")
    ceo_and_hq: str = Field(description="Current CEO name and headquarters city/state/country")
    business_model: str = Field(description="1-paragraph summary of core business model (e.g., B2B SaaS, Hardware, Marketplace)")
    current_performance_and_outlook: str = Field(description="Summary of how the company is performing recently and whether it is worth considering for investment")

class SearchPlan(BaseModel):
    queries: List[str] = Field(
        description="3-5 targeted search queries to extract industry codes, executive details, business model, and recent outlook"
    )