# SEC-API LangChain Tools Implementation Plan

## Project Overview

This project aims to build LangChain-compatible tools that enable AI agents to interact with SEC-API.io services for retrieving and analyzing SEC filing data. The goal is to create agents that can understand natural language queries about SEC filings and use the appropriate tools to fetch and analyze the relevant data.

## First Principles Approach

We're following a first principles approach, focusing on fundamental logic rather than complex architectures:

1. **Data Access**: Use SEC-API.io endpoints to access filing data
2. **Tool Specialization**: Each tool serves a specific purpose
3. **Agent Intelligence**: Agent selects appropriate tools based on query requirements
4. **Response Formatting**: Results formatted for human consumption

## Available Tools

Based on the repository structure, we have these tool categories:

1. **Query API**: Search and filter SEC EDGAR filings by specific criteria
2. **Full Text Search API**: Semantically search across filings
3. **Extractor API**: Extract specific sections from filings (10-K, 10-Q, 8-K)
4. **EDGAR Entities API**: Get company information from SEC database
5. **XBRL-to-JSON API**: Convert and access financial data in standardized format

## Agent Design

The agent will:
1. Parse the user's query to understand intent
2. Select appropriate tool(s)
3. Execute tool(s) with appropriate parameters
4. Format the response in a user-friendly way

## Implementation Plan

### 1. Tool Integration and Testing

First, ensure each individual tool works correctly:

```python
# For each tool type:
# 1. Create test queries
# 2. Verify correct results
# 3. Document input/output patterns
```

### 2. Agent Configuration

Create a LangChain agent with access to all tools:

```python
from langchain.agents import AgentType, initialize_agent
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool

# Initialize LLM
llm = ChatOpenAI(model_name="gpt-3.5-turbo")

# Create tool instances
query_tool = SECQueryTool()
search_tool = SECFullTextSearchTool()
extractor_tool = SECExtractorTool()
entities_tool = SECEdgarEntitiesAPI()
xbrl_tool = SECXbrlTool()

# Create LangChain-compatible tools
tools = [
    StructuredTool.from_function(
        func=query_tool.search_filings,
        name="SECQueryAPI",
        description="Search SEC filings by ticker, form type, date range, etc."
    ),
    StructuredTool.from_function(
        func=search_tool.search_sec_filings,
        name="SECFullTextSearch",
        description="Search the full text content of SEC filings"
    ),
    StructuredTool.from_function(
        func=extractor_tool.get_section,
        name="SECExtractSection",
        description="Extract specific sections from SEC filings (10-K, 10-Q, 8-K)"
    ),
    StructuredTool.from_function(
        func=entities_tool.get_entity_data,
        name="SECEntityInfo",
        description="Get information about companies from the SEC EDGAR database"
    ),
    StructuredTool.from_function(
        func=xbrl_tool.xbrl_to_json,
        name="SECFinancialData",
        description="Convert XBRL financial statements to JSON format"
    )
]

# Create agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
```

### 3. Tool Selection Logic

The agent needs to understand which tool to use based on the query. Here's the decision logic:

| Query Type | Appropriate Tool | Example |
|------------|------------------|---------|
| Specific filing metadata | Query API | "Find Tesla's 10-K filings in 2020" |
| Content search | Full Text Search | "Find filings mentioning climate change" |
| Section analysis | Extractor API | "Extract risk factors from Tesla's latest 10-K" |
| Company information | EDGAR Entities API | "Get information about Microsoft" |
| Financial data | XBRL-to-JSON API | "Get Tesla's revenue for 2022" |

We'll create prompt templates that help the agent understand this logic.

## Testing Strategy

### 1. Basic Tool Tests

Test each tool with known inputs and verify outputs:

```python
# Example: Query API Test
def test_query_api():
    query_tool = SECQueryTool()
    query = {
        "query": "ticker:TSLA AND formType:\"10-K\" AND filedAt:[2020-01-01 TO 2020-12-31]",
        "from": "0",
        "size": "10",
        "sort": [{ "filedAt": { "order": "desc" } }]
    }
    results = query_tool.search_filings(query)
    assert len(results) > 0
    assert results[0]["ticker"] == "TSLA"
    assert results[0]["formType"] == "10-K"
```

### 2. Tool Selection Tests

Test if the agent selects the right tool for different queries:

```python
def test_agent_tool_selection():
    # Test with different query types and analyze which tools the agent selects
    result = agent.run("Find Tesla's most recent 10-K filing")
    # Verify Query API was used
    
    result = agent.run("Find filings mentioning cybersecurity risks")
    # Verify Full Text Search was used
    
    result = agent.run("Extract the risk factors section from Microsoft's latest 10-K")
    # Verify Extractor API was used
```

### 3. End-to-End Tests with Sample Questions

Test the agent with the provided sample questions:

```python
sample_questions = [
    "Summarize the Management Discussion and Analysis section of Microsoft's 2023 10-K",
    "How many shares outstanding did Immix Biopharma have as of 12/31/23?",
    # ... other sample questions
]

for question in sample_questions:
    result = agent.run(question)
    print(f"Question: {question}")
    print(f"Answer: {result}")
    print("-" * 50)
```

## Sample Questions Analysis

Let's analyze how the agent should approach each sample question:

### 1. "Summarize the Management Discussion and Analysis section of Microsoft's 2023 10-K"

**Tools needed:**
1. Query API - to find Microsoft's 2023 10-K filing
2. Extractor API - to extract the MD&A section (section 7)
3. LLM - to summarize the content

**Agent steps:**
1. Use Query API to find Microsoft's 2023 10-K
2. Extract the filing URL
3. Use Extractor API to get section 7
4. Summarize the extracted content

### 2. "How many shares outstanding did Immix Biopharma have as of 12/31/23?"

**Tools needed:**
1. Query API - to find Immix Biopharma's recent filings
2. XBRL-to-JSON API - to extract financial data
3. Extractor API - backup if XBRL data isn't available

**Agent steps:**
1. Use Query API to find Immix Biopharma's annual report (10-K) or quarterly report (10-Q) for the period containing 12/31/23
2. Extract the filing URL
3. Use XBRL-to-JSON to get structured data or Extractor API to get relevant section
4. Extract the shares outstanding information

### 3. "What did Immix Biopharma report as revenue for the quarter ended September 30, 2024?"

**Tools needed:**
1. Query API - to find Immix Biopharma's Q3 2024 report
2. XBRL-to-JSON API - to extract financial data

**Agent steps:**
1. Use Query API to find the 10-Q for Q3 2024
2. Extract the filing URL
3. Use XBRL-to-JSON to get revenue data

### 4. "Identify and list risk factors that are similar across Apple's four most recent quarterly (10-Q) filings."

**Tools needed:**
1. Query API - to find Apple's four most recent 10-Q filings
2. Extractor API - to extract risk factors sections
3. LLM - to compare and identify similarities

**Agent steps:**
1. Use Query API to find Apple's four most recent 10-Q filings
2. For each filing, use Extractor API to get risk factors (Part II, Item 1A)
3. Compare the content to identify similarities

### 5. "Identify new significant accounting policies introduced in Amazon's latest quarterly report compared to the previous four quarterly reports."

**Tools needed:**
1. Query API - to find Amazon's five most recent quarterly reports
2. Extractor API - to extract accounting policies sections
3. LLM - to compare and identify differences

**Agent steps:**
1. Use Query API to find Amazon's five most recent quarterly reports
2. For each filing, use Extractor API to get the accounting policies section
3. Compare to identify new policies

### 6. "Are there any new footnote disclosures related to cybersecurity in the latest 10-Q for Tesla?"

**Tools needed:**
1. Query API - to find Tesla's latest and previous 10-Q filings
2. Full Text Search API - to search for cybersecurity mentions
3. Extractor API - to extract relevant sections
4. LLM - to compare and identify differences

**Agent steps:**
1. Use Query API to find Tesla's latest and previous 10-Q filings
2. Use Full Text Search to locate cybersecurity mentions
3. Use Extractor API to get relevant sections
4. Compare to identify new disclosures

### 7. "How many stock options, on average, have been granted each quarter over the past eight quarters for Coca-Cola?"

**Tools needed:**
1. Query API - to find Coca-Cola's eight most recent quarterly reports
2. XBRL-to-JSON API - to extract stock option data
3. Extractor API - backup if XBRL data isn't available

**Agent steps:**
1. Use Query API to find Coca-Cola's eight most recent quarterly reports
2. For each filing, extract stock option grant information
3. Calculate the average

### 8. "What did Microsoft list as the recent accounting guidance on their last 10-K?"

**Tools needed:**
1. Query API - to find Microsoft's latest 10-K
2. Extractor API - to extract the accounting guidance section
3. Full Text Search API - backup to find accounting guidance mentions

**Agent steps:**
1. Use Query API to find Microsoft's latest 10-K
2. Use Extractor API to get the accounting policy section
3. Extract information about recent accounting guidance

## Multi-agent Approach

For version 1, a single agent with access to all tools is sufficient. This keeps the architecture simple while still providing powerful capabilities.

However, if needed later, we could explore:

1. **Tool-specific agents**: Specialized agents for each tool category
2. **ReAct agent**: Agent that can reason about which tools to use
3. **Chain of thought**: Break complex queries into sub-tasks

## Implementation Roadmap

### Phase 1: Foundation (Days 1-2)
- Set up environment and dependencies
- Create basic test suite for each tool
- Implement simple agent with access to all tools

### Phase 2: Intelligence (Days 3-4)
- Enhance tool selection logic
- Create prompt templates for better tool selection
- Test with basic queries

### Phase 3: Testing & Refinement (Days 5-6)
- Test with sample questions
- Refine agent based on test results
- Document behavior patterns

### Phase 4: Optimization (Day 7)
- Optimize performance
- Enhance error handling
- Create final test suite

## SEC-API Python Query Examples

We'll start testing using these query examples from the SEC-API Python documentation:

1. **Query API**: 
   ```python
   query = {
     "query": "ticker:TSLA AND filedAt:[2020-01-01 TO 2020-12-31] AND formType:\"10-Q\"",
     "from": "0",
     "size": "10",
     "sort": [{ "filedAt": { "order": "desc" } }]
   }
   ```

2. **Extractor API**:
   ```python
   filing_url_10k = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
   section_text = extractorApi.get_section(filing_url_10k, "1A", "text")
   ```

3. **Form ADV API**:
   ```python
   response = formAdvApi.get_firms(
       {
           "query": "Info.FirmCrdNb:361",
           "from": "0",
           "size": "10",
           "sort": [{"Info.FirmCrdNb": {"order": "desc"}}],
       }
   )
   ```

## Conclusion

This implementation plan follows first principles, focusing on the logic of tool selection and data retrieval rather than complex architectures. By testing each component individually and then integrating them into a single agent, we can create a powerful system that answers SEC-related questions accurately.

For version 2, we'll enhance the agent to cite sources with links, providing more transparency and credibility to the answers. 