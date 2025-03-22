# langchain_tool.py
from langchain.agents import Tool
from full_text_search_tool import full_text_search_tool

full_text_search = Tool(
    name="FullTextSearch",
    func=full_text_search_tool,
    description=(
        "Use this tool to search the full text of SEC filings. "
        "Provide a query string, a comma-separated list of form types, "
        "a start date, and an end date (format YYYY-MM-DD)."
    )
)
