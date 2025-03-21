"""
SEC API Knowledge Module

Contains mappings and helper functions for SEC filing analysis.
This module is based on the official sec-api-python repository documentation.
"""

from typing import Dict, Any, List, Optional, Tuple
import re

#################################################
# Section ID Mappings - Directly from documentation
#################################################

# 10-K Section IDs (as specified in sec-api-python documentation)
FORM_10K_SECTIONS = {
    "1": "Business",
    "1A": "Risk Factors",
    "1B": "Unresolved Staff Comments",
    "1C": "Cybersecurity",
    "2": "Properties",
    "3": "Legal Proceedings",
    "4": "Mine Safety Disclosures",
    "5": "Market for Registrant's Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities",
    "6": "Selected Financial Data",
    "7": "Management's Discussion and Analysis of Financial Condition and Results of Operations",
    "7A": "Quantitative and Qualitative Disclosures about Market Risk",
    "8": "Financial Statements and Supplementary Data",
    "9": "Changes in and Disagreements with Accountants on Accounting and Financial Disclosure",
    "9A": "Controls and Procedures",
    "9B": "Other Information",
    "10": "Directors, Executive Officers and Corporate Governance",
    "11": "Executive Compensation",
    "12": "Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters",
    "13": "Certain Relationships and Related Transactions, and Director Independence",
    "14": "Principal Accountant Fees and Services"
}

# 10-Q Section IDs (as specified in sec-api-python documentation)
FORM_10Q_SECTIONS = {
    "part1item1": "Financial Statements",
    "part1item2": "Management's Discussion and Analysis of Financial Condition and Results of Operations",
    "part1item3": "Quantitative and Qualitative Disclosures About Market Risk",
    "part1item4": "Controls and Procedures",
    "part2item1": "Legal Proceedings",
    "part2item1a": "Risk Factors",
    "part2item2": "Unregistered Sales of Equity Securities and Use of Proceeds",
    "part2item3": "Defaults Upon Senior Securities",
    "part2item4": "Mine Safety Disclosures",
    "part2item5": "Other Information",
    "part2item6": "Exhibits"
}

# 8-K Items - Commonly used in SEC API queries
FORM_8K_ITEMS = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "1.04": "Mine Safety - Reporting of Shutdowns and Patterns of Violations",
    "1.05": "Material Cybersecurity Incidents",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.03": "Creation of a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement",
    "2.04": "Triggering Events That Accelerate or Increase a Direct Financial Obligation",
    "2.05": "Cost Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Failure to Satisfy a Continued Listing Rule or Standard",
    "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modifications to Rights of Security Holders",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements or a Related Audit Report",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers",
    "5.03": "Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year",
    "5.04": "Temporary Suspension of Trading Under Registrant's Employee Benefit Plans",
    "5.05": "Amendments to the Registrant's Code of Ethics, or Waiver of a Provision of the Code of Ethics",
    "5.06": "Change in Shell Company Status",
    "5.07": "Submission of Matters to a Vote of Security Holders",
    "5.08": "Shareholder Nominations Pursuant to Exchange Act Rule 14a-11",
    "6.01": "ABS Informational and Computational Material",
    "6.02": "Change of Servicer or Trustee",
    "6.03": "Change in Credit Enhancement or Other External Support",
    "6.04": "Failure to Make a Required Distribution",
    "6.05": "Securities Act Updating Disclosure",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits"
}

# Common form types used in SEC API queries
COMMON_FORM_TYPES = {
    "10-K": "Annual Report",
    "10-Q": "Quarterly Report",
    "8-K": "Current Report",
    "S-1": "Registration Statement",
    "424B4": "Prospectus",
    "13F-HR": "Institutional Investment Manager Holdings Report",
    "DEF 14A": "Proxy Statement",
    "4": "Statement of Changes in Beneficial Ownership",
    "SC 13G": "Passive Investor Report",
    "SC 13D": "Activist Investor Report"
}

# Common XBRL field names for financial metrics
# These are the standardized XBRL tags used in SEC filings
XBRL_METRICS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "RevenueNet",
        "TotalRevenuesAndOtherIncome"
    ],
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic"
    ],
    "assets": [
        "Assets",
        "AssetsCurrent",
        "AssetsNoncurrent",
        "TotalAssets"
    ],
    "liabilities": [
        "Liabilities",
        "LiabilitiesCurrent",
        "LiabilitiesNoncurrent",
        "TotalLiabilities"
    ],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashAndCashEquivalentsPeriodIncreaseDecrease"
    ],
    "eps": [
        "EarningsPerShareBasic",
        "EarningsPerShareDiluted"
    ],
    "cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashProvidedByUsedInFinancingActivities"
    ]
}

#################################################
# SEC API Tool Selection
#################################################

def is_financial_metric_query(query: str) -> bool:
    """Determine if a query is asking for financial metrics that require XBRL-to-JSON API."""
    financial_terms = [
        "revenue", "income", "profit", "loss", "earnings", "eps", "per share",
        "assets", "liabilities", "cash", "sales", "margin", "financial statement",
        "balance sheet", "income statement", "cash flow", "financial data", "financial metrics"
    ]
    return any(term in query.lower() for term in financial_terms)

def is_textual_analysis_query(query: str) -> bool:
    """Determine if a query requires textual analysis of specific sections (Extractor API)."""
    analysis_terms = [
        "risk factors", "business description", "management discussion", "md&a",
        "properties", "legal proceedings", "disclosure", "controls", "procedures",
        "directors", "officers", "executive compensation", "risk"
    ]
    return any(term in query.lower() for term in analysis_terms)

def determine_form_type(query: str) -> str:
    """Determine which SEC form type is being requested in the query."""
    query = query.lower()
    
    # Check for specific form mentions
    if "10-k" in query or "annual report" in query or "yearly" in query:
        return "10-K"
    elif "10-q" in query or "quarter" in query or "quarterly" in query:
        return "10-Q"
    elif "8-k" in query or "current report" in query or "material event" in query:
        return "8-K"
    
    # Check for time periods that suggest form types
    if "quarter" in query or "q1" in query or "q2" in query or "q3" in query or "q4" in query:
        return "10-Q"
    if "annual" in query or "fiscal year" in query or "yearly" in query:
        return "10-K"
    
    # Default to most recent filing for general queries
    return "10-K"

def extract_company_info_type(query: str) -> str:
    """Determine what type of company identifier is being used in the query."""
    query = query.lower()
    
    if re.search(r'\b[A-Z]{1,5}\b', query, re.IGNORECASE):  # Check for likely ticker pattern
        return "ticker"
    elif re.search(r'\b\d{10}\b', query):  # CIK pattern (10 digits)
        return "cik"
    else:
        return "name"  # Default to company name

def get_section_id(form_type: str, section_name: str) -> Optional[str]:
    """Get the section ID for a given form type and section name."""
    section_name = section_name.lower()
    
    if form_type == "10-K":
        for id, name in FORM_10K_SECTIONS.items():
            if section_name in name.lower():
                return id
    elif form_type == "10-Q":
        for id, name in FORM_10Q_SECTIONS.items():
            if section_name in name.lower():
                return id
    elif form_type == "8-K":
        for id, name in FORM_8K_ITEMS.items():
            if section_name in name.lower():
                return id
                
    return None

def get_xbrl_fields(metric: str) -> List[str]:
    """Get possible XBRL field names for a given financial metric."""
    return XBRL_METRICS.get(metric.lower(), [])

def extract_date_from_query(query: str) -> Optional[Tuple[str, str]]:
    """Extract date information from a query for SEC-API date parameters."""
    query = query.lower()
    
    # Look for year patterns
    year_pattern = r'(?:in|for|during|from)?\s*(?:the\s*year)?\s*(20\d{2})'
    year_matches = re.findall(year_pattern, query)
    
    if year_matches:
        year = year_matches[0]
        return (f"{year}-01-01", f"{year}-12-31")
    
    # Look for quarter patterns
    quarter_pattern = r'(?:q[1-4]|first quarter|second quarter|third quarter|fourth quarter|1st quarter|2nd quarter|3rd quarter|4th quarter)(?:\s*of)?\s*(20\d{2})'
    quarter_matches = re.findall(quarter_pattern, query)
    
    if quarter_matches:
        quarter_text = quarter_matches[0][0].lower()
        year = quarter_matches[0][1]
        
        if "q1" in quarter_text or "first" in quarter_text or "1st" in quarter_text:
            return (f"{year}-01-01", f"{year}-03-31")
        elif "q2" in quarter_text or "second" in quarter_text or "2nd" in quarter_text:
            return (f"{year}-04-01", f"{year}-06-30")
        elif "q3" in quarter_text or "third" in quarter_text or "3rd" in quarter_text:
            return (f"{year}-07-01", f"{year}-09-30")
        elif "q4" in quarter_text or "fourth" in quarter_text or "4th" in quarter_text:
            return (f"{year}-10-01", f"{year}-12-31")
    
    # Look for specific date mentions
    specific_date_pattern = r'(?:for|on|as of|dated|ending|ended)?\s*(\w+ \d{1,2},? 20\d{2})'
    date_matches = re.findall(specific_date_pattern, query)
    
    if date_matches:
        # This would need to be converted to YYYY-MM-DD format
        # For simplicity, we'll just note that a specific date was found
        return None
    
    # Default to recent period if no specific dates found
    return None

def analyze_query_for_tools(query: str) -> Dict[str, Any]:
    """
    Analyze a query to determine which SEC-API tools and parameters to use.
    
    Args:
        query: User's query string
        
    Returns:
        Dictionary with recommended tools and parameters
    """
    result = {
        "query": query,
        "requires_company_resolution": True,  # Almost always needed first
        "form_type": determine_form_type(query),
        "company_identifier_type": extract_company_info_type(query),
        "date_range": extract_date_from_query(query),
        "requires_financial_data": is_financial_metric_query(query),
        "requires_section_extraction": is_textual_analysis_query(query),
        "recommended_tools": ["ResolveCompany", "SECQueryAPI"]  # Base tools almost always needed
    }
    
    # Add XBRL tool if financial data is requested
    if result["requires_financial_data"]:
        result["recommended_tools"].append("SECFinancialData")
    
    # Add section extraction if textual analysis is requested
    if result["requires_section_extraction"]:
        result["recommended_tools"].append("SECExtractSection")
        
        # Try to determine specific section
        for section_name in FORM_10K_SECTIONS.values():
            if section_name.lower() in query.lower():
                result["section_name"] = section_name
                result["section_id"] = get_section_id(result["form_type"], section_name)
                break
                
        if "section_id" not in result and result["form_type"] == "10-Q":
            for section_name in FORM_10Q_SECTIONS.values():
                if section_name.lower() in query.lower():
                    result["section_name"] = section_name
                    result["section_id"] = get_section_id(result["form_type"], section_name)
                    break
    
    # Determine potential financial metrics of interest
    if result["requires_financial_data"]:
        result["financial_metrics"] = []
        for metric in XBRL_METRICS.keys():
            if metric in query.lower() or any(alias in query.lower() for alias in get_metric_aliases(metric)):
                result["financial_metrics"].append(metric)
    
    return result

def get_metric_aliases(metric: str) -> List[str]:
    """Get alternative terms for a financial metric."""
    aliases = {
        "revenue": ["sales", "top line", "turnover"],
        "net_income": ["profit", "bottom line", "earnings", "net profit"],
        "assets": ["total assets", "asset base"],
        "liabilities": ["debts", "obligations", "total liabilities"],
        "eps": ["earnings per share", "profit per share"],
        "cash_flow": ["cash flows", "cash position", "liquidity"]
    }
    
    return aliases.get(metric, []) 