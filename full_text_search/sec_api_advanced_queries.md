# Advanced SEC API Query Guide

This document provides detailed examples and explanations for constructing advanced queries with the SEC API LangChain tool. Understanding these query patterns will help you efficiently search and analyze SEC filings for research, compliance, and investment purposes.

## Query Syntax Reference

When using the tool with `use_exact_match=False`, you can leverage the full query syntax capabilities:

| Syntax | Description | Example |
|--------|-------------|---------|
| Basic terms | Simple word search | `cybersecurity` |
| Exact phrases | Search for exact phrases using quotes | `"revenue growth"` |
| Boolean OR | Find documents with either term | `AI OR "artificial intelligence"` |
| Boolean AND | Find documents with both terms | `cybersecurity AND breach` |
| Exclusion | Exclude documents with specific terms | `cybersecurity -insurance` or `cybersecurity NOT insurance` |
| Wildcards | Match variations of terms | `cyber*` (matches cybersecurity, cyberattack, etc.) |
| Grouping | Group expressions with parentheses | `(AI OR "machine learning") AND risk` |
| Proximity | Find terms within specified distance | `"climate change"~10` |
| Field-specific | Search within specific fields | `formType:10-K AND ticker:AAPL` |

## Advanced Query Examples

### 1. Boolean Operators with Grouping

**Query:** `(AI OR "artificial intelligence") AND "risk factors"`

**Explanation:** This query finds filings that mention either the term "AI" or the exact phrase "artificial intelligence" in conjunction with the exact phrase "risk factors". The parentheses ensure the OR operation is processed first.

**Use case:** Research how companies are disclosing AI-related risks in their SEC filings.

### 2. Wildcards and Exclusions

**Query:** `cyber* -insurance`

**Explanation:** Finds filings containing terms starting with "cyber" (cybersecurity, cyberattacks, etc.) but excludes filings that mention "insurance".

**Use case:** Focus on operational cybersecurity discussions rather than insurance coverage for cyber risks.

### 3. Proximity Search

**Query:** `"climate change"~10`

**Explanation:** Finds filings where the words "climate" and "change" appear within 10 words of each other, allowing for variations like "change in climate" or "climate-related change".

**Use case:** More flexible phrase matching that captures related discussions even when terms aren't directly adjacent.

### 4. Field-Specific Search

**Query:** `formType:10-K AND ticker:AAPL AND "supply chain"`

**Explanation:** Searches specifically for 10-K filings from Apple Inc. that mention "supply chain".

**Use case:** Target analysis to specific companies and filing types.

### 5. Complex Multi-Criteria Search

**Query:** `("revenue decline" OR "decreased revenue") AND (covid* OR pandemic) -guidance`

**Explanation:** Finds filings mentioning revenue declines in relation to COVID/pandemic, but excludes those just mentioning future "guidance".

**Use case:** Analyze actual financial impacts of events rather than forward-looking statements.

### 6. Date-Based Comparison Research

**Strategy:** Run identical queries across different time periods to track trends.

**Example:**
```python
# Early period (2018-2019)
search_sec_filings(
    query='"ESG" OR "Environmental Social Governance"',
    form_types=["10-K"],
    start_date="2018-01-01",
    end_date="2019-12-31",
    count_only=True,
    use_exact_match=False
)

# Middle period (2020-2021)
# Same query, different date range

# Recent period (2022-2023)
# Same query, different date range
```

**Use case:** Track the evolution of ESG reporting or other topics over time.

### 7. Industry Analysis

**Query:** `semiconductor AND ("supply chain" OR shortage OR constraint) AND formType:10-K`

**Explanation:** Finds 10-K filings discussing semiconductor supply chain issues.

**Use case:** Industry-specific research on supply chain challenges.

### 8. Competitive Analysis

**Strategy:** Loop through competitor tickers with the same complex query:

```python
companies = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
for ticker in companies:
    search_sec_filings(
        query=f'ticker:{ticker} AND ("artificial intelligence" OR "machine learning" OR "neural network" OR "generative AI" OR "LLM" OR "large language model")',
        form_types=["10-K", "10-Q"],
        start_date="2021-01-01",
        end_date="2023-12-31",
        count_only=True,
        use_exact_match=False
    )
```

**Use case:** Compare how often different companies in the same sector discuss key technologies or trends.

## Tips for Effective Queries

1. **Start broad, then refine**: Begin with a more general query and examine results before adding restrictions.

2. **Use count_only=True for initial testing**: Quickly check if your query returns a reasonable number of results before retrieving detailed results.

3. **Leverage field-specific searches**: When you know exactly what you're looking for, targeting specific fields can dramatically improve relevance.

4. **Save complex query results**: For complex queries that you might want to analyze further, use `save_to_file=True` to preserve the raw API response.

5. **Balance specificity and flexibility**: Very specific queries might miss relevant results due to variations in terminology. Consider using wildcards and proximity searches for more flexibility.

6. **Pagination for large result sets**: When dealing with queries that return hundreds or thousands of results, use the pagination parameters (`from_param` and `size`) to iterate through results in manageable chunks.

## Common Research Patterns

### Risk Factor Analysis
```
"risk factors" AND (cybersecurity OR "data breach" OR "information security")
```

### Regulatory Impact Assessment
```
("SEC" OR "Securities and Exchange Commission") AND ("climate disclosure" OR "ESG reporting") AND guidance
```

### Supply Chain Monitoring
```
"supply chain" AND (disruption OR shortage OR constraint OR bottleneck)
```

### Litigation Tracking
```
(litigation OR lawsuit OR "legal proceedings") AND (settlement OR "class action" OR verdict)
```

### Executive Departure Analysis
```
("CEO" OR "Chief Executive Officer") AND (resign* OR depart* OR terminat*)
```

### Merger & Acquisition Research
```
(acquisition OR merger OR "business combination") AND (complet* OR announc* OR terminat*)
``` 