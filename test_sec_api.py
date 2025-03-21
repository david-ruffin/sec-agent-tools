from sec_api import QueryApi
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("SEC_API_KEY")
queryApi = QueryApi(api_key=api_key)

query = {
    "query": 'ticker:MSFT AND formType:"10-K"',
    "size": "1"
}

print("Testing query:", query)
response = queryApi.get_filings(query)
print("\nResponse:", response) 