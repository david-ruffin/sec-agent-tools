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

## Detailed Execution Flows for Sample Questions

### 1. "Summarize the Management Discussion and Analysis section of Microsoft's 2023 10-K"

**Execution Flow:**
```python
# 1. Query API Tool - Find Microsoft's 2023 10-K
query = {
  "query": "ticker:MSFT AND formType:\"10-K\" AND filedAt:[2023-01-01 TO 2023-12-31]",
  "from": "0",
  "size": "1",
  "sort": [{ "filedAt": { "order": "desc" } }]
}
filing = query_tool.search_filings(query)[0]
filing_url = filing["documentUrl"]  # Get the HTML URL

# 2. Extractor API Tool - Extract MD&A section
md_and_a = extractor_tool.get_section(filing_url, "7", "text")

# 3. LLM Summarization
summary = llm.generate("Summarize the following Management Discussion and Analysis section: " + md_and_a)
return summary
```

### 2. "How many shares outstanding did Immix Biopharma have as of 12/31/23?"

**Execution Flow:**
```python
# 1. Query API Tool - Find filing closest to the date
query = {
  "query": "ticker:IMMX AND (formType:\"10-K\" OR formType:\"10-Q\") AND filedAt:[2023-12-01 TO 2024-03-31]",
  "from": "0",
  "size": "10",
  "sort": [{ "filedAt": { "order": "asc" } }]  # First filing after the date
}
filing = query_tool.search_filings(query)[0]
filing_url = filing["documentUrl"]

# 2. Try XBRL-to-JSON Tool first
xbrl_data = xbrl_tool.xbrl_to_json(htm_url=filing_url)
# Look for shares outstanding in structured data
if "SharesOutstanding" in xbrl_data:
    return xbrl_data["SharesOutstanding"]

# 3. Extractor API Tool as backup
# If XBRL doesn't have it, extract relevant section (Part II Item 5)
section = extractor_tool.get_section(filing_url, "part2item5", "text")
# Use LLM to parse text for shares outstanding
return llm.generate("Extract the number of shares outstanding as of 12/31/23 from: " + section)
```

### 3. "What did Immix Biopharma report as revenue for the quarter ended September 30, 2024?"

**Execution Flow:**
```python
# 1. Query API Tool - Find the Q3 2024 report
query = {
  "query": "ticker:IMMX AND formType:\"10-Q\" AND periodOfReport:\"2024-09-30\"",
  "from": "0",
  "size": "1"
}
filing = query_tool.search_filings(query)[0]
filing_url = filing["documentUrl"]

# 2. XBRL-to-JSON Tool - Get structured financial data
xbrl_data = xbrl_tool.xbrl_to_json(htm_url=filing_url)
# Look for revenue in structured data
if "Revenues" in xbrl_data or "Revenue" in xbrl_data:
    return xbrl_data.get("Revenues") or xbrl_data.get("Revenue")

# 3. Extractor API Tool as backup
# If XBRL doesn't have it, extract financial statements section
section = extractor_tool.get_section(filing_url, "part1item1", "text")  # Financial Statements
# Use LLM to parse text for revenue
return llm.generate("Extract the revenue for the quarter ended September 30, 2024 from: " + section)
```

### 4. "Identify and list risk factors that are similar across Apple's four most recent quarterly (10-Q) filings."

**Execution Flow:**
```python
# 1. Query API Tool - Get last 4 quarterly filings
query = {
  "query": "ticker:AAPL AND formType:\"10-Q\"",
  "from": "0",
  "size": "4",
  "sort": [{ "filedAt": { "order": "desc" } }]
}
filings = query_tool.search_filings(query)
filing_urls = [filing["documentUrl"] for filing in filings]

# 2. Extractor API Tool - Extract risk factors from each filing
risk_factors = []
for url in filing_urls:
    section = extractor_tool.get_section(url, "part2item1a", "text")
    risk_factors.append(section)

# 3. LLM Analysis - Compare and find similarities
result = llm.generate(f"""
Identify and list risk factors that are similar across these four Apple 10-Q filings:

Filing 1: {risk_factors[0]}
Filing 2: {risk_factors[1]}
Filing 3: {risk_factors[2]}
Filing 4: {risk_factors[3]}

List only the risk factors that appear consistently across all four filings.
""")
return result
```

### 5. "Identify new significant accounting policies introduced in Amazon's latest quarterly report compared to the previous four quarterly reports."

**Execution Flow:**
```python
# 1. Query API Tool - Get 5 most recent quarterly filings
query = {
  "query": "ticker:AMZN AND formType:\"10-Q\"",
  "from": "0",
  "size": "5",
  "sort": [{ "filedAt": { "order": "desc" } }]
}
filings = query_tool.search_filings(query)
filing_urls = [filing["documentUrl"] for filing in filings]
latest_filing_url = filing_urls[0]
previous_filing_urls = filing_urls[1:5]

# 2. Extractor API Tool - Extract accounting policies section from each
# Get accounting policies sections (typically in Notes to Financial Statements)
latest_accounting = extractor_tool.get_section(latest_filing_url, "part1item1", "text")

previous_accounting = []
for url in previous_filing_urls:
    section = extractor_tool.get_section(url, "part1item1", "text")
    previous_accounting.append(section)

# 3. LLM Analysis - Compare and identify new policies
result = llm.generate(f"""
Compare the accounting policies in Amazon's latest quarterly report with those in the previous four reports.

Latest report: {latest_accounting}

Previous reports:
Report 1: {previous_accounting[0]}
Report 2: {previous_accounting[1]}
Report 3: {previous_accounting[2]}
Report 4: {previous_accounting[3]}

Identify and list any new significant accounting policies that appear in the latest report but not in the previous ones.
""")
return result
```

### 6. "Are there any new footnote disclosures related to cybersecurity in the latest 10-Q for Tesla?"

**Execution Flow:**
```python
# 1. Query API Tool - Get latest and previous 10-Q
query = {
  "query": "ticker:TSLA AND formType:\"10-Q\"",
  "from": "0",
  "size": "2",
  "sort": [{ "filedAt": { "order": "desc" } }]
}
filings = query_tool.search_filings(query)
latest_url = filings[0]["documentUrl"]
previous_url = filings[1]["documentUrl"]

# 2. Full Text Search Tool - Find cybersecurity mentions
# Search for cybersecurity in both filings
latest_search = search_tool.search_sec_filings(
    query="cybersecurity",
    url=latest_url
)

previous_search = search_tool.search_sec_filings(
    query="cybersecurity",
    url=previous_url
)

# 3. Extractor API Tool - Get relevant sections if needed
# If full text search found mentions, extract those sections
latest_sections = []
if latest_search:
    for result in latest_search:
        section_id = result.get("section_id")
        if section_id:
            section = extractor_tool.get_section(latest_url, section_id, "text")
            latest_sections.append(section)

previous_sections = []
if previous_search:
    for result in previous_search:
        section_id = result.get("section_id")
        if section_id:
            section = extractor_tool.get_section(previous_url, section_id, "text")
            previous_sections.append(section)

# 4. LLM Analysis - Compare the sections to identify new disclosures
result = llm.generate(f"""
Compare cybersecurity disclosures in Tesla's latest 10-Q with the previous 10-Q.

Latest 10-Q sections mentioning cybersecurity:
{latest_sections}

Previous 10-Q sections mentioning cybersecurity:
{previous_sections}

Are there any new footnote disclosures related to cybersecurity in the latest 10-Q? If yes, what are they?
""")
return result
```

### 7. "How many stock options, on average, have been granted each quarter over the past eight quarters for Coca-Cola?"

**Execution Flow:**
```python
# 1. Query API Tool - Get last 8 quarterly filings
query = {
  "query": "ticker:KO AND formType:\"10-Q\"",
  "from": "0",
  "size": "8",
  "sort": [{ "filedAt": { "order": "desc" } }]
}
filings = query_tool.search_filings(query)
filing_urls = [filing["documentUrl"] for filing in filings]

# 2. XBRL-to-JSON Tool - Try to get structured data first
options_data = []
for url in filing_urls:
    xbrl_data = xbrl_tool.xbrl_to_json(htm_url=url)
    # Look for stock options data in structured format
    if "StockOptionsGranted" in xbrl_data:
        options_data.append(xbrl_data["StockOptionsGranted"])

# 3. Extractor API Tool - If XBRL doesn't have it
# If XBRL doesn't have it, extract equity compensation sections
if not options_data:
    for url in filing_urls:
        # Usually in Notes to Financial Statements under Equity Compensation
        section = extractor_tool.get_section(url, "part1item1", "text")
        
        # Use LLM to extract options granted
        options_granted = llm.generate(
            "Extract the number of stock options granted during this quarter from: " + section
        )
        options_data.append(options_granted)

# 4. Calculate Average
# Calculate average from collected data
if options_data:
    avg_options = sum(options_data) / len(options_data)
    return f"On average, Coca-Cola granted {avg_options} stock options per quarter over the past eight quarters."
else:
    return "Could not find stock options data in the quarterly filings."
```

### 8. "What did Microsoft list as the recent accounting guidance on their last 10-K?"

**Execution Flow:**
```python
# 1. Query API Tool - Get the latest 10-K
query = {
  "query": "ticker:MSFT AND formType:\"10-K\"",
  "from": "0",
  "size": "1",
  "sort": [{ "filedAt": { "order": "desc" } }]
}
filing = query_tool.search_filings(query)[0]
filing_url = filing["documentUrl"]

# 2. Extractor API Tool - Get accounting policies section
# Accounting guidance is typically in Note 1 to Financial Statements
# Section 8 contains Financial Statements and Supplementary Data
financial_statements = extractor_tool.get_section(filing_url, "8", "text")

# 3. Full Text Search Tool - If needed for backup
# If exact section not found, use full text search
if not "recent accounting guidance" in financial_statements.lower():
    search_results = search_tool.search_sec_filings(
        query="recent accounting guidance OR recently adopted accounting standards",
        url=filing_url
    )
    
    # Extract those sections
    for result in search_results:
        section_id = result.get("section_id")
        if section_id:
            section = extractor_tool.get_section(filing_url, section_id, "text")
            financial_statements += "\n" + section

# 4. LLM Analysis - Extract the accounting guidance information
result = llm.generate(f"""
From Microsoft's latest 10-K, extract and list what they reported as recent accounting guidance or recently adopted accounting standards:

{financial_statements}
""")
return result
```

## Guiding the Agent: How It Will Follow These Approaches

To ensure the agent knows which tools to use and in what sequence, we'll implement several mechanisms:

### 1. Comprehensive Tool Descriptions

Each tool needs detailed descriptions that clearly communicate:
- What the tool does
- When to use it
- Required parameters
- Expected output

Example:
```python
StructuredTool.from_function(
    func=extractor_tool.get_section,
    name="SECExtractSection",
    description="""Extract a specific section from an SEC filing (10-K, 10-Q, 8-K).
    Use this when you need to analyze a particular section like "Risk Factors", "MD&A", etc.
    Required parameters: filing_url (URL of filing), section_id (e.g., "1A" for Risk Factors in 10-K)
    Returns the text content of the requested section."""
)
```

### 2. System Prompt with Decision Logic

The system prompt will contain explicit instructions on when to use each tool:

```python
SYSTEM_PROMPT = """You are an expert SEC filing analyst with access to SEC data tools.

When analyzing SEC filings, follow this approach:
1. First find the relevant filing(s) using the Query API
2. For section analysis, use the Extractor API
3. For financial data, use the XBRL-to-JSON tool
4. For text searching across filings, use the Full Text Search tool

For specific types of questions:
- When asked about a company's financial data: Find the filing first, then use XBRL-to-JSON
- When asked to compare sections across filings: Find all filings first, then extract sections
- When asked about specific sections: Find the filing first, then extract that section

Always proceed step-by-step and explain your process."""
```

### 3. Few-Shot Examples

Include examples in the prompt to show the agent how to approach different query types:

```python
few_shot_examples = [
    {"question": "What were Tesla's total revenues in Q2 2023?",
     "thinking": """
     This question asks for Tesla's revenue in Q2 2023. I need to:
     1. Find Tesla's Q2 2023 10-Q filing using QueryAPI
     2. Extract financial data using XBRL-to-JSON
     3. Locate the revenue figure
     """,
     "tools": [
         {"name": "SECQueryAPI", "params": {"query": "ticker:TSLA AND formType:10-Q AND periodOfReport:2023-06-30"}},
         {"name": "SECFinancialData", "params": {"htm_url": "[Extracted URL from previous step]"}}
     ]},
    
    {"question": "Summarize Apple's risk factors from their latest 10-K",
     "thinking": """
     This question asks for a summary of Apple's risk factors from their latest 10-K. I need to:
     1. Find Apple's most recent 10-K using QueryAPI
     2. Extract the Risk Factors section (1A) using ExtractorAPI
     3. Summarize the content
     """,
     "tools": [
         {"name": "SECQueryAPI", "params": {"query": "ticker:AAPL AND formType:10-K", "size": "1", "sort": [{"filedAt": {"order": "desc"}}]}},
         {"name": "SECExtractSection", "params": {"filing_url": "[Extracted URL from previous step]", "section_id": "1A"}}
     ]}
]
```

### 4. Pattern Recognition and Tool Selection Chain

Implement a structured reasoning process for tool selection:

```python
TOOL_SELECTION_TEMPLATE = """
To answer this question: "{question}"

I need to determine which tools to use and in what order.

1. What specific information am I looking for? {information_type}
2. Which company/companies are involved? {companies}
3. What time period is relevant? {time_period}
4. What filing types would contain this information? {filing_types}

Based on this analysis:
- First tool to use: {first_tool} because {first_tool_reason}
- Second tool to use: {second_tool} because {second_tool_reason}
- Additional tools if needed: {additional_tools}

I'll execute these tools in sequence to find the answer.
"""
```

### 5. ReAct Framework

Use a Reasoning and Acting (ReAct) framework that explicitly makes the agent:

1. **Reason**: Think about what information is needed and which tools to use
2. **Act**: Call the appropriate tool with the right parameters
3. **Observe**: Analyze the results from the tool
4. **Plan**: Determine next steps based on the information gathered

Example agent output format:
```
Thought: This question is asking about Microsoft's Management Discussion and Analysis section from their 2023 10-K. I need to find the filing first, then extract the MD&A section.

Action: SECQueryAPI
Action Input: {"query": "ticker:MSFT AND formType:\"10-K\" AND filedAt:[2023-01-01 TO 2023-12-31]", "size": "1", "sort": [{"filedAt": {"order": "desc"}}]}

Observation: [Result from query showing filing URL]

Thought: Now I have the filing URL. MD&A is typically in section 7 of a 10-K. I'll extract that section.

Action: SECExtractSection
Action Input: {"filing_url": "[URL from previous step]", "section_id": "7", "output_format": "text"}

Observation: [Extracted MD&A text]

Thought: I now have the full MD&A section. I'll summarize the key points.

Final Answer: [Summary of MD&A section]
```

### 6. Query Pattern Matching

Implement pattern recognition to help identify the query type and appropriate tools:

```python
def identify_query_type(query):
    # Financial data patterns
    if re.search(r"(revenue|income|earnings|profit|shares|outstanding)", query, re.I):
        return "FINANCIAL_DATA"
    
    # Section analysis patterns
    if re.search(r"(section|risk factor|management discussion|MD&A)", query, re.I):
        return "SECTION_ANALYSIS"
    
    # Comparison patterns
    if re.search(r"(compare|similar|across|difference|new|change)", query, re.I):
        return "COMPARISON"
    
    # Default to general query
    return "GENERAL"

def get_tool_sequence(query_type):
    if query_type == "FINANCIAL_DATA":
        return ["SECQueryAPI", "SECFinancialData"]
    elif query_type == "SECTION_ANALYSIS":
        return ["SECQueryAPI", "SECExtractSection"]
    elif query_type == "COMPARISON":
        return ["SECQueryAPI", "SECExtractSection", "LLMComparison"]
    else:
        return ["SECFullTextSearch"]
```

### 7. Custom Agent Executor

Create a custom agent executor that performs a planning step before execution:

```python
class SECAgentExecutor(AgentExecutor):
    def _plan(self, query):
        # Generate analysis of query
        analysis = self.llm.generate(f"Analyze this SEC filing query: {query}")
        
        # Determine tool sequence
        tool_sequence = self.llm.generate(
            f"Based on this analysis: {analysis}\n"
            f"List the tools needed in sequence to answer this query."
        )
        
        return tool_sequence
        
    def _execute(self, query):
        # Get the plan
        plan = self._plan(query)
        
        # Execute the plan using appropriate tools
        results = []
        for step in plan.split('\n'):
            if "SECQueryAPI" in step:
                # Execute query step
                pass
            elif "SECExtractSection" in step:
                # Execute extraction step
                pass
            # ... other tools
            
        # Combine results
        return self._synthesize_results(results)
```

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