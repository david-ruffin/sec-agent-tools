################################
## Imports ##
## Required libraries for the tool ##
################################
import os
from dotenv import load_dotenv
from sec_api import QueryApi
from langchain.tools import StructuredTool
from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from typing import List, Optional

################################
## Environment Setup ##
## Load API keys and configs ##
################################
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEC_API_KEY = os.getenv("SEC_API_KEY")

# Initialize SEC API client
queryApi = QueryApi(api_key=SEC_API_KEY)

################################
## Tool Function ##
## Main query functionality ##
################################
def search_sec_filings(query: str) -> str:
    """
    Search SEC filings using the QueryApi with exact parameters from the documentation example.
    
    Args:
        query: Search query following SEC-API query syntax
    """
    # Use the EXACT parameters from the TSLA documentation example
    search_params = {
        "query": query,
        "from": "0",
        "size": "10",
        "sort": [{ "filedAt": { "order": "desc" } }]
    }
    
    print(f"Executing SEC API query: {search_params}")
    
    # Call the API
    filings = queryApi.get_filings(search_params)
    
    if not filings:
        return "No results found matching your criteria."
    
    # Format results
    formatted_results = ["Search Results:"]
    
    for i, filing in enumerate(filings.get("filings", [])[:3], 1):
        formatted_results.append(f"\nResult {i}:")
        formatted_results.append(f"Company: {filing.get('companyName', 'N/A')} (Ticker: {filing.get('ticker', 'N/A')})")
        formatted_results.append(f"Form Type: {filing.get('formType', 'N/A')}")
        formatted_results.append(f"Filed At: {filing.get('filedAt', 'N/A')}")
    
    return "\n".join(formatted_results)

################################
## LangChain Integration ##
## Tool and agent setup ##
################################
# Create the tool
sec_tool = StructuredTool.from_function(
    func=search_sec_filings,
    name="sec_filing_search",
    description="Search SEC filings using the Query API. Supports searching by ticker, form type, and date range."
)

# Create LLM and agent
llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
agent = initialize_agent(
    [sec_tool],
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

################################
## Testing ##
## Using documented examples ##
################################
if __name__ == "__main__":
    # Test using the exact TSLA example from documentation
    print("\n=== Testing Direct Example ===")
    test_query = 'ticker:TSLA AND filedAt:[2020-01-01 TO 2020-12-31] AND formType:"10-Q"'
    result = search_sec_filings(test_query)
    print(result)

    # Test using agent with the same query
    print("\n=== Testing Agent with Example Query ===")
    response = agent.invoke({"input": "Find all 10-Q filings filed by Tesla in 2020"})
    print(f"\nAgent response:\n{response['output']}") 