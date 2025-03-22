# full_text_search_tool.py
from sec_api import FullTextSearchApi

def full_text_search_tool(
    query: str,
    form_types: str = "8-K,10-Q",
    start_date: str = "2021-01-01",
    end_date: str = "2021-06-14"
) -> dict:
    """
    Calls the sec-api Full-Text Search API to search SEC filings.

    Args:
        query (str): The search query string.
        form_types (str): A comma-separated list of form types (e.g., "8-K,10-Q").
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.

    Returns:
        dict: The API response containing the filings.
    """
    # Initialize the API client (replace YOUR_API_KEY with your actual key)
    full_text_search_api = FullTextSearchApi(api_key="86abfb8d1d091a440f3c391e21d7f1fe332eda723ff977a4df36275e7f10355d")
    
    # Prepare the query dictionary.
    # Convert the comma-separated form_types to a list.
    form_types_list = [ft.strip() for ft in form_types.split(",")]
    
    search_query = {
        "query": query,
        "formTypes": form_types_list,
        "startDate": start_date,
        "endDate": end_date,
    }
    
    # Call the API
    filings = full_text_search_api.get_filings(search_query)
    return filings
