import os
from dotenv import load_dotenv
from sec_api import MappingApi, QueryApi, ExtractorApi
from mapping_api.mapping_apiv1 import resolve_company_info

# Load environment variables
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

if not SEC_API_KEY:
    raise ValueError("SEC_API_KEY not found in environment variables")

# Initialize API clients
query_api = QueryApi(api_key=SEC_API_KEY)
extractor_api = ExtractorApi(api_key=SEC_API_KEY)

def get_company_10k_mda(company_name: str, year: str = "2023") -> str:
    """
    Simple function to get a company's MD&A section from their 10-K
    """
    print(f"\nStep 1: Resolving company info for {company_name}")
    company_info = resolve_company_info("name", company_name)
    if not company_info:
        raise ValueError(f"Could not resolve company info for {company_name}")
    
    print(f"Found company: {company_info[0]}")
    ticker = company_info[0]["ticker"]
    
    print(f"\nStep 2: Finding {year} 10-K for {ticker}")
    query = {
        "query": f'ticker:{ticker} AND formType:"10-K" AND filedAt:[{year}-01-01 TO {year}-12-31]',
        "from": "0",
        "size": "1"
    }
    
    result = query_api.get_filings(query)
    if not result.get("filings"):
        raise ValueError(f"No 10-K found for {ticker} in {year}")
    
    filing_url = result["filings"][0]["linkToFilingDetails"]
    print(f"Found 10-K: {filing_url}")
    
    print(f"\nStep 3: Extracting MD&A section")
    # Section 7 is MD&A in 10-K filings per SEC-API docs
    mda_section = extractor_api.get_section(filing_url, "7", "text")
    
    return mda_section

if __name__ == "__main__":
    # Test with Microsoft
    try:
        mda = get_company_10k_mda("Microsoft")
        print("\nSuccess! First 500 characters of MD&A:")
        print(mda[:500] + "...")
    except Exception as e:
        print(f"Error: {str(e)}") 