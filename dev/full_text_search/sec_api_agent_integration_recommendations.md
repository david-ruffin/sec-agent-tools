# SEC API Agent Integration Recommendations

## Core Architecture

1. **Tool-Based Pattern**: Implement each SEC API endpoint as a standalone tool with consistent interfaces
2. **Unified Base Class**: Use a common base class that handles API keys, error handling, and shared utilities
3. **LangChain Integration**: Expose all tools as LangChain-compatible structured tools

## Standard Tool Implementation Template

Every SEC API endpoint should follow this pattern:

```python
class SecApiTool:
    """Base implementation for a SEC API endpoint."""
    
    def __init__(self, api_key=None):
        # Set up API key and initialize specific SEC API client
        self.api_key = api_key or os.getenv("SEC_API_KEY")
        self.api_client = SpecificSecApiClient(self.api_key)
    
    def prepare_params(self, **kwargs):
        # Validate and format parameters for this specific API
        # Handle defaults and special formatting requirements
        return params_dict
    
    def execute_query(self, **kwargs):
        # Execute the API call with proper parameters
        # Handle errors and return results
        params = self.prepare_params(**kwargs)
        return self.api_client.get_data(params)
    
    def format_results(self, data, **kwargs):
        # Format the results in a consistent, human-readable way
        # Include source URLs and relevant metadata
        return formatted_string
    
    def search(self, **kwargs):
        # Main entry point that ties everything together
        # This is the function exposed to the agent
        data = self.execute_query(**kwargs)
        return self.format_results(data, **kwargs)
```

## Tool Integration with LangChain

```python
def get_sec_tool(tool_class):
    """Create a LangChain-compatible tool from any SEC API tool."""
    tool = tool_class()
    
    return StructuredTool.from_function(
        func=tool.search,
        name=f"sec_{tool_class.tool_name}",
        description=tool_class.description
    )

# Create tools for all SEC API endpoints
sec_fulltext_tool = get_sec_tool(SecApiFullTextSearch)
sec_13f_tool = get_sec_tool(SecApi13F)
sec_section_tool = get_sec_tool(SecApiSectionExtractor)
# etc.

# Combine all tools for agent use
all_sec_tools = [
    sec_fulltext_tool,
    sec_13f_tool,
    sec_section_tool,
    # etc.
]
```

## Parameter Standardization

For consistent behavior across tools:

1. **Common Parameters**: Use consistent parameter names across tools:
   - `query`: The search term or filter
   - `start_date`/`end_date`: Date range in YYYY-MM-DD format
   - `max_results`: Number of results to return
   - `sort_by`/`sort_order`: Sorting parameters

2. **Output Format**: All tools should return:
   - Clear result counts
   - Formatted, human-readable results
   - Source URLs for verification
   - Error messages when queries fail

## Practical Implementation Steps

1. Start with the existing FullTextSearch implementation as a template
2. Implement priority endpoints first (Section Extractor, Query API, Form 13F)
3. Create a simple dispatching mechanism based on user query keywords
4. Test with both direct Python calls and through LangChain agent

## Example Usage

```python
# Initialize LangChain agent with SEC tools
agent = initialize_agent(
    all_sec_tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# User query examples
agent.invoke("What were the risk factors mentioned in Apple's latest 10-K?")
agent.invoke("Show me Berkshire Hathaway's holdings in their recent 13F filings")
agent.invoke("Find SEC filings mentioning 'climate risk' in 2022")
```

## Core Focus Areas

1. **Modular Implementation**: Each API endpoint as a separate tool
2. **Consistent Interfaces**: Standardized parameter names and output formats
3. **Self-Describing Tools**: Clear descriptions for agent to select appropriate tool
4. **Error Handling**: Graceful error handling and informative messages
5. **Result Formatting**: Human-readable output with source links 