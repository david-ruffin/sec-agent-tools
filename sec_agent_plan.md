# SEC Filing Analysis System: LangGraph Implementation Plan

## Project Goal

Create an accurate, reliable system for analyzing SEC filings using the SEC-API.io service with a LangGraph-based agent architecture to answer complex queries without guessing when data is unavailable.

## Architecture Overview

The system follows a "smart orchestrator, dumb tools" pattern:

1. **Smart Planning Agent**: Analyzes user queries, determines necessary steps, and orchestrates tool agents
2. **Tool Agents**: Single-purpose wrappers around specific SEC-API endpoints with no decision-making capabilities
3. **LangGraph Framework**: Manages state and workflow between agents

```
User Query → Planning Agent → Tool Agents → Response
                    ↑              ↓
                    └── State Management ──┘
```

## Core Components

### 1. State Schema

LangGraph requires a defined state schema to maintain context between agent calls:

```python
state_schema = {
    "user_query": str,                          # Original user question
    "companies": list,                          # Resolved company information
    "filings": list,                            # Located filing information
    "sections": list,                           # Extracted section content
    "financial_data": list,                     # Extracted financial metrics
    "comparisons": list,                        # Multi-filing analysis results
    "errors": list,                             # Error tracking
    "current_step": str,                        # Current execution step
    "next_step": str,                           # Next step to execute
    "plan": dict,                               # Execution plan details
    "final_answer": str                         # Final answer to user
}
```

### 2. Knowledge Base

The existing `sec_api_knowledge.py` will be maintained and extended as needed to provide:

- Section ID mappings for different form types (10-K, 10-Q, 8-K)
- XBRL field mappings for financial metrics
- Query intent detection and analysis
- Date range extraction
- Company identifier parsing

### 3. Agent Types

The system will use three types of nodes:

1. **Planning Node**: Analyzes queries, generates execution plans
2. **Tool Nodes**: Execute specific SEC-API operations
3. **Processing Nodes**: Handle multi-filing comparison, answer formatting

### 4. Graph Structure

The workflow will be defined as a directed graph with conditional branching based on query type:

```
                      ┌─── Section Extraction ───┐
                      │                          │
Planning ─── Company Resolution ─── Filing Search ─── XBRL Conversion ───┐
                      │                          │                        │
                      └─── Multi-Filing Compare ─┘                        │
                                                                          │
                                                                   Answer Generation
```

## Query Handling Patterns

### Pattern 1: Section Extraction
For queries like "Summarize the Management Discussion and Analysis section of Microsoft's 2023 10-K"

1. Analyze query to determine:
   - Company: Microsoft
   - Form type: 10-K
   - Section: Management Discussion and Analysis (Section 7)
   - Time period: 2023

2. Workflow:
   - Planning → Company Resolution → Filing Search → Section Extraction → Answer Generation

### Pattern 2: Financial Data Extraction
For queries like "How many shares outstanding did Immix Biopharma have as of 12/31/23?"

1. Analyze query to determine:
   - Company: Immix Biopharma
   - Data needed: Shares outstanding
   - Date: 12/31/23

2. Workflow:
   - Planning → Company Resolution → Filing Search → XBRL Conversion → Answer Generation

### Pattern 3: Multi-Filing Comparison
For queries like "Identify risk factors that are similar across Apple's four most recent quarterly filings"

1. Analyze query to determine:
   - Company: Apple
   - Form type: 10-Q
   - Section: Risk Factors
   - Count: 4 most recent
   - Analysis type: Similarity comparison

2. Workflow:
   - Planning → Company Resolution → Filing Search (multiple) → Section Extraction (multiple) → Multi-Filing Analysis → Answer Generation

### Pattern 4: Change Detection
For queries like "Identify new accounting policies in Amazon's latest quarterly report compared to previous reports"

1. Analyze query to determine:
   - Company: Amazon
   - Form type: 10-Q
   - Section: Accounting Policies
   - Analysis type: Change detection

2. Workflow:
   - Planning → Company Resolution → Filing Search (multiple) → Section Extraction (multiple) → Change Detection → Answer Generation

## Implementation Details

### Planning Agent

The planning agent will:
1. Use `sec_api_knowledge.py` to analyze the query
2. Determine which companies, filings, sections, and/or financial data are needed
3. Create a step-by-step execution plan
4. Set the initial `next_step` in the state

```python
def planning_agent(state):
    query = state["user_query"]
    query_context = analyze_query_for_tools(query)
    
    # Determine the primary task type
    task_type = determine_task_type(query, query_context)
    
    # Generate a detailed plan based on task type
    plan = generate_plan(task_type, query_context)
    
    return {
        "next_step": plan["first_step"],
        "current_step": "planning",
        "plan": plan
    }
```

### Tool Agent Nodes

Each tool agent will:
1. Extract required parameters from the state
2. Call the appropriate agent function from the `agents/` directory
3. Update the state with results
4. Set the `next_step` based on the execution plan and current results

Example:
```python
def mapping_agent_node(state):
    """Company resolution node using mapping_agent.py"""
    company_name = extract_company_name(state["user_query"])
    
    result = mapping_agent({
        "identifier_type": "name",
        "identifier_value": company_name
    })
    
    if result["status"] == 200:
        return {
            "companies": [result["data"]],
            "current_step": "company_resolution",
            "next_step": state["plan"]["after_company_resolution"]
        }
    else:
        return {
            "errors": state["errors"] + [{
                "source": "company_resolution", 
                "message": result["error"]
            }],
            "current_step": "company_resolution",
            "next_step": "error_handling"
        }
```

### Error Handling

A critical aspect of the implementation:

1. No guessing - if data is not found, report the error clearly
2. Each agent returns standardized error information
3. Error handling node decides whether to:
   - Try an alternative approach
   - Ask for clarification
   - Return a clear error message

## Sample Workflows

### Example 1: Section Content Query

Query: "Summarize the Management Discussion and Analysis section of Microsoft's 2023 10-K"

1. **Planning Node**:
   - Analyzes query using `sec_api_knowledge.py`
   - Identifies company (Microsoft), form type (10-K), section (MD&A), year (2023)
   - Sets `next_step` to "company_resolution"

2. **Company Resolution Node**:
   - Calls `mapping_agent` with name="Microsoft"
   - Updates state with CIK, ticker
   - Sets `next_step` to "filing_search"

3. **Filing Search Node**:
   - Calls `filing_search_agent` with CIK and form type "10-K" for 2023
   - Updates state with filing URL
   - Sets `next_step` to "section_extraction"

4. **Section Extraction Node**:
   - Calls `section_extraction_agent` with filing URL and section ID "7"
   - Updates state with section content
   - Sets `next_step` to "answer_generation"

5. **Answer Generation Node**:
   - Formats response based on section content
   - Sets final_answer in state

### Example 2: Multi-Filing Comparison

Query: "Identify risk factors that are similar across Apple's four most recent quarterly filings"

1. **Planning Node**:
   - Identifies company (Apple), form type (10-Q), section (Risk Factors), count (4)
   - Sets `next_step` to "company_resolution"

2. **Company Resolution Node**:
   - Resolves "Apple" to CIK and ticker
   - Sets `next_step` to "filing_search"

3. **Filing Search Node**:
   - Searches for 4 most recent 10-Q filings
   - Updates state with multiple filing URLs
   - Sets `next_step` to "multi_section_extraction"

4. **Multi-Section Extraction Node**:
   - Extracts Risk Factors section from each filing
   - Updates state with all section contents
   - Sets `next_step` to "similarity_analysis"

5. **Similarity Analysis Node**:
   - Compares section texts to identify similarities
   - Updates state with comparison results
   - Sets `next_step` to "answer_generation"

6. **Answer Generation Node**:
   - Formats final answer based on similarity analysis

## Context Preservation

A key advantage of LangGraph is maintaining context between steps:

1. **Company Context**: Once resolved, company information (CIK, ticker) is preserved in state
2. **Filing Context**: Filing metadata remains available throughout workflow
3. **Section Context**: Section contents and identifiers remain accessible
4. **Plan Context**: The full execution plan remains part of the state

This ensures that each agent has access to all necessary information from previous steps.

## Testing Strategy

For this implementation, we will prioritize:

1. **Unit tests** for each agent function and node
2. **Integration tests** for specific query patterns
3. **Accuracy tests** comparing results to manually verified data

Success criteria:
- No guessing when data is unavailable
- Correct handling of all sample queries
- Clear error messages when API calls fail
- Proper context preservation between steps

## Implementation Phases

### Phase 1: Core Framework
- Implement LangGraph state schema
- Create planning agent
- Build basic graph structure
- Testing harness

### Phase 2: Basic Query Patterns
- Implement company resolution node
- Implement filing search node
- Implement section extraction node
- Implement answer generation node
- Support for simple section extraction queries

### Phase 3: Financial Data Extraction
- Implement XBRL conversion node
- Support for financial metric queries

### Phase 4: Advanced Analysis
- Implement multi-filing comparison nodes
- Support for change detection
- Support for similarity analysis

### Phase 5: Edge Cases and Refinement
- Implement error recovery strategies
- Handle ambiguous queries
- Support for mixed query types

## Conclusion

This implementation plan provides a clear path to creating a flexible, accurate SEC filing analysis system using LangGraph and the existing agent framework. By separating the smart planning logic from the tool execution, the system maintains modularity while providing sophisticated query handling.

The focus on accuracy over guessing ensures that the system delivers reliable results, with clear error messaging when data cannot be found or is ambiguous. 