import os
from dotenv import load_dotenv
from sec_api import FullTextSearchApi
from langchain.tools import StructuredTool
from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from typing import List, Optional

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEC_API_KEY = os.getenv("SEC_API_KEY")

# Initialize SEC API client
fullTextSearchApi = FullTextSearchApi(api_key=SEC_API_KEY)

# Tool function
def search_sec_filings(query: str) -> str:
    """
    Search SEC filings using the exact parameters from the documentation example.
    
    Args:
        query: Search term to look for in SEC filings
    """
    # Use the EXACT parameters from the documentation example
    search_params = {
        "query": f'"{query}"',
        "formTypes": ['8-K', '10-Q'],
        "startDate": '2021-01-01',
        "endDate": '2021-06-14',
    }
    
    print(f"Executing SEC API query: {search_params}")
    
    # Call the API
    filings = fullTextSearchApi.get_filings(search_params)
    
    if not filings or "filings" not in filings or not filings["filings"]:
        return "No results found matching your criteria."
    
    # Format results
    total = filings.get("total", {}).get("value", 0)
    formatted_results = [f"Found {total} results. Showing first 3:"]
    
    for i, filing in enumerate(filings["filings"][:3], 1):
        formatted_results.append(f"Result {i}:")
        formatted_results.append(f"Company: {filing.get('companyName', 'N/A')} (Ticker: {filing.get('ticker', 'N/A')})")
        formatted_results.append(f"Form Type: {filing.get('formType', 'N/A')}")
        formatted_results.append(f"Filed At: {filing.get('filedAt', 'N/A')}")
        formatted_results.append("")
    
    return "\n".join(formatted_results)

# Create the tool
sec_tool = StructuredTool.from_function(
    func=search_sec_filings,
    name="sec_filing_search",
    description="Search SEC filings for a specific term."
)

# Create LLM and agent
llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
agent = initialize_agent(
    [sec_tool],
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# Test the direct example
print("\n=== Testing Direct Example ===")
result = search_sec_filings("LPCN 1154")
print(result)

# Test agent with the EXACT same query
print("\n=== Testing Agent with Specific Query ===")
response = agent.invoke({"input": "Find SEC filings that mention LPCN 1154"})
print(f"\nAgent response:\n{response['output']}")