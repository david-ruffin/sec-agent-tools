"""
Simple SEC filing analyzer using SEC-API
"""

import os
from dotenv import load_dotenv
from sec_api import QueryApi, ExtractorApi, XbrlApi

# Load environment variables
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

if not SEC_API_KEY:
    raise ValueError("SEC_API_KEY not found in .env file")

# Initialize API clients
query_api = QueryApi(api_key=SEC_API_KEY)
xbrl_api = XbrlApi(api_key=SEC_API_KEY)

def get_company_filings(company_name, form_type=None, from_date=None, to_date=None):
    """Search for company filings."""
    query = f'companyName:"{company_name}"'
    if form_type:
        query += f' AND formType:"{form_type}"'
    if from_date and to_date:
        query += f' AND filedAt:[{from_date} TO {to_date}]'
    
    return query_api.get_filings({
        "query": query,
        "from": "0",
        "size": "10",
        "sort": [{"filedAt": {"order": "desc"}}]
    })

def get_financial_data(filing_url):
    """Get XBRL financial data from a filing."""
    return xbrl_api.xbrl_to_json(htm_url=filing_url)

def process_query(query):
    """Process a user query about SEC filings."""
    try:
        # Example: "What did Immix Biopharma report as revenue for the quarter ended March 31, 2024?"
        company_name = "Immix Biopharma"  # We'd extract this from the query
        form_type = "10-Q"  # For quarterly reports
        
        # Search for filings
        filings = get_company_filings(company_name, form_type)
        
        if not filings or not filings.get("filings"):
            return "No filings found for this company."
        
        # Print available filings first
        print("\nAvailable filings:")
        for filing in filings["filings"]:
            print(f"Form {filing.get('formType')} filed on {filing.get('filedAt')}")
        print()
        
        # Get the most recent filing
        filing = filings["filings"][0]
        filing_url = filing.get("linkToFilingDetails")
        
        if not filing_url:
            return "Filing URL not found."
            
        print(f"Using filing from {filing.get('filedAt')}")
        
        # Get financial data
        financial_data = get_financial_data(filing_url)
        
        if not financial_data:
            return "No financial data found in the filing."
        
        # Extract revenue information
        if "StatementsOfIncome" in financial_data:
            income_data = financial_data["StatementsOfIncome"]
            revenue_fields = [
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues",
                "SalesRevenueNet",
                "RevenueNet"
            ]
            
            for field in revenue_fields:
                if field in income_data:
                    return f"Revenue: ${income_data[field]:,}"
            
            return "Revenue information not found in the filing."
        else:
            return "Income statement data not found in the filing."
            
    except Exception as e:
        return f"Error processing query: {str(e)}"

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(process_query(query))
    else:
        print("SEC Filing Analyzer")
        print("Type 'exit' to quit")
        while True:
            query = input("\nEnter your question: ")
            if query.lower() in ['exit', 'quit']:
                break
            print("\n" + process_query(query)) 