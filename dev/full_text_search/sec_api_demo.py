#!/usr/bin/env python
"""
SEC API Demo Script

This script demonstrates how to use the SEC API LangChain tool
in a real-world application. It provides examples of different
search patterns and how to integrate the tool with LangChain.
"""

import os
from dotenv import load_dotenv
from langchain.tools import StructuredTool
from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import importlib.util
import sys

# Import the search function using the correct path with hyphens
spec = importlib.util.spec_from_file_location(
    "sec_api_module", 
    "./sec_api_langchain_fulltextsearch_tool-v7.py"
)
sec_api_module = importlib.util.module_from_spec(spec)
sys.modules["sec_api_module"] = sec_api_module
spec.loader.exec_module(sec_api_module)

# Get the search function from the module
search_sec_filings = sec_api_module.search_sec_filings

# Load environment variables
load_dotenv()

def main():
    """Run demonstration examples of the SEC API LangChain tool."""
    
    print("=" * 80)
    print("SEC API LangChain Tool Demonstration")
    print("=" * 80)
    
    # Example 1: Basic Search
    print("\n--- Example 1: Basic Search ---")
    basic_result = search_sec_filings(
        query="LPCN 1154",
        max_results=2
    )
    print(basic_result)
    
    # Example 2: Advanced Query with Boolean Operators
    print("\n--- Example 2: Advanced Query with Boolean Operators ---")
    advanced_result = search_sec_filings(
        query="LPCN 1154 OR LPCN 1107",
        use_exact_match=False,
        max_results=2
    )
    print(advanced_result)
    
    # Example 3: Count-Only Mode
    print("\n--- Example 3: Count-Only Mode ---")
    count_result = search_sec_filings(
        query="climate change",
        form_types=["10-K"],
        start_date="2020-01-01",
        end_date="2022-12-31",
        count_only=True
    )
    print(count_result)
    
    # Example 4: Detailed Results with Sorting
    print("\n--- Example 4: Detailed Results with Sorting ---")
    detailed_result = search_sec_filings(
        query="revenue growth",
        form_types=["10-K", "10-Q"],
        start_date="2021-01-01",
        end_date="2022-12-31",
        include_all_metadata=True,
        include_snippets=True,
        sort_by="filedAt",
        sort_order="desc",
        max_results=2
    )
    print(detailed_result)
    
    # Example 5: Pagination
    print("\n--- Example 5: Pagination Example ---")
    first_page = search_sec_filings(
        query="earnings",
        form_types=["8-K"],
        from_param=0,
        size=5,
        max_results=3
    )
    print(first_page)
    print("\n--- Second Page of Results ---")
    second_page = search_sec_filings(
        query="earnings",
        form_types=["8-K"],
        from_param=5,  # Start from the 6th result
        size=5,
        max_results=3
    )
    print(second_page)
    
    # Example 6: Using the tool with a LangChain agent
    print("\n--- Example 6: LangChain Agent Integration ---")
    # Create the tool
    sec_tool = StructuredTool.from_function(
        func=search_sec_filings,
        name="sec_filing_search",
        description="Search SEC EDGAR filings using keywords, form types, and date ranges."
    )
    
    # Set up a streaming LLM for visible agent thinking
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    llm = ChatOpenAI(
        temperature=0,
        streaming=True,
        callback_manager=callback_manager,
        verbose=True
    )
    
    # Initialize the agent
    agent = initialize_agent(
        [sec_tool],
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True
    )
    
    # Run the agent with a natural language query
    print("\nAsking the agent: How many 10-K forms mentioned 'climate risk' in 2022?")
    agent.invoke({
        "input": "How many 10-K forms mentioned 'climate risk' in 2022?"
    })
    
    print("\nAsking the agent: Show me the 3 most recent 8-K filings about acquisitions, sorted by date.")
    agent.invoke({
        "input": "Show me the 3 most recent 8-K filings about acquisitions, sorted by date."
    })
    
    print("\n" + "=" * 80)
    print("Demonstration Complete")
    print("=" * 80)


if __name__ == "__main__":
    main() 