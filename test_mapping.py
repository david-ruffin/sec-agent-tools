from sec_api import MappingApi
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("SEC_API_KEY")
mappingApi = MappingApi(api_key=api_key)

# Test resolving company name to ticker
result = mappingApi.resolve("name", "Microsoft Corporation")
print("\nMapping Result:", result) 