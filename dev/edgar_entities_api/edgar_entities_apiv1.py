"""
SEC Edgar Entities API Tool - Version 1
Provides access to SEC EDGAR entity information through sec-api.io
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from sec_api import EdgarEntitiesApi

class SECEdgarEntitiesAPI:
    """
    A tool for accessing SEC EDGAR entity information.
    Designed for use with LangChain agents.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the SEC Edgar Entities API tool."""
        if api_key is None:
            load_dotenv()
            api_key = os.getenv('SEC_API_KEY')
            
        if not api_key:
            raise ValueError("SEC API key is required. Set it in .env file or pass directly.")
            
        self.api = EdgarEntitiesApi(api_key)
        
    def get_entity_data(self, 
                       query: str,
                       start_index: str = "0",
                       size: str = "50",
                       sort_field: str = "cikUpdatedAt",
                       sort_order: str = "desc") -> Dict[str, Any]:
        """
        Search and retrieve entity information from SEC EDGAR.
        
        Args:
            query (str): Search query (e.g., "cik:1318605", "ticker:TSLA")
            start_index (str): Starting index for pagination
            size (str): Number of results to return
            sort_field (str): Field to sort by
            sort_order (str): Sort order ("asc" or "desc")
            
        Returns:
            Dict containing the search results and metadata
        """
        try:
            search_request = {
                "query": query,
                "from": start_index,
                "size": size,
                "sort": [{sort_field: {"order": sort_order}}]
            }
            
            return self.api.get_data(search_request)
            
        except Exception as e:
            raise ValueError(f"Error accessing SEC EDGAR API: {str(e)}")

def test_documentation_example():
    """Test the example from the documentation."""
    try:
        # Initialize the tool
        tool = SECEdgarEntitiesAPI()
        
        # Test with Tesla's CIK (example from documentation)
        response = tool.get_entity_data("cik:1318605")
        
        # Print the data as shown in the documentation
        print("Response data:")
        print(response["data"])
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_documentation_example() 