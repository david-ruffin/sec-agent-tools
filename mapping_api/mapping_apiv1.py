import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from sec_api import MappingApi

# Load environment variables
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

if not SEC_API_KEY:
    raise ValueError("SEC_API_KEY not found in environment variables")

# Initialize API client
mappingApi = MappingApi(api_key=SEC_API_KEY)

def resolve_company_info(
    parameter_type: str,
    value: str
) -> List[Dict[str, Any]]:
    """
    Resolve company information using various parameters.
    
    Args:
        parameter_type: Type of parameter to resolve ('ticker', 'cik', 'cusip', 'name', 'exchange', 'sector', 'industry')
        value: Value to resolve
        
    Returns:
        List of company information dictionaries
    """
    try:
        result = mappingApi.resolve(parameter_type, value)
        return result
    except Exception as e:
        print(f"Error resolving company info: {str(e)}")
        return []

if __name__ == "__main__":
    # Test cases from documentation
    print("\nTest 1 - Resolve by ticker:")
    result1 = resolve_company_info("ticker", "TSLA")
    print(result1)
    
    print("\nTest 2 - Resolve by CIK:")
    result2 = resolve_company_info("cik", "1318605")
    print(result2)
    
    print("\nTest 3 - Resolve by CUSIP:")
    result3 = resolve_company_info("cusip", "88160R101")
    print(result3)
    
    print("\nTest 4 - Resolve by exchange:")
    result4 = resolve_company_info("exchange", "NASDAQ")
    print(result4)
    
    print("\nTest 5 - Resolve by company name:")
    result5 = resolve_company_info("name", "Microsoft Corporation")
    print(result5) 