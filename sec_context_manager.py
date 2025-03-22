"""
SEC Context Manager

A module for maintaining context between SEC API calls to improve analysis accuracy.
Preserves company information, filing details, section relationships, and financial data context.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SECContext:
    """
    Maintains context between SEC API calls.
    
    This class tracks:
    1. Company context (name, ticker, CIK)
    2. Filing metadata (type, date, URL)
    3. Section hierarchy and relationships
    4. Financial data context (period, metrics)
    """
    
    def __init__(self):
        """Initialize an empty context."""
        # Company context
        self.company_context = {
            "name": None,
            "ticker": None,
            "cik": None,
            "exchange": None,
            "industry": None,
            "sector": None,
            "most_recent_lookup": None,  # Stores lookup type (name, ticker, cik)
        }
        
        # Filing context
        self.filing_context = {
            "current_filing": None,  # Current filing being analyzed
            "filings": [],            # List of filings in the current analysis
            "form_type": None,        # Current form type (10-K, 10-Q, 8-K)
            "filing_date": None,      # Filing date
            "accession_no": None,     # Accession number
            "filing_url": None,       # URL to the filing
            "period_end_date": None,  # Period end date (for financial data)
            "fiscal_year": None,      # Fiscal year
            "fiscal_period": None,    # Fiscal period (Q1, Q2, Q3, FY)
        }
        
        # Section context
        self.section_context = {
            "current_section": None,   # Current section being analyzed
            "current_section_id": None,  # Current section ID
            "sections_analyzed": [],   # List of sections analyzed in this session
            "section_relationships": {},  # Relationships between sections
        }
        
        # Financial data context
        self.financial_context = {
            "metrics_retrieved": {},   # Financial metrics retrieved in this session
            "xbrl_data_available": None,  # Whether XBRL data is available for current filing
            "currency": None,          # Currency used in the filing
            "units": {},               # Units for financial metrics
            "fiscal_period": None,     # Fiscal period (Q1, Q2, Q3, FY)
            "fiscal_year": None,       # Fiscal year
            "period_end_date": None,   # Period end date
        }
        
        # Query context
        self.query_context = {
            "original_query": None,    # Original user query
            "query_type": None,        # Type of query (financial, textual, comparative)
            "time_period": None,       # Time period mentioned in query
            "comparison_type": None,   # Type of comparison requested
            "metrics_requested": [],   # Financial metrics requested
        }
        
        # Error tracking
        self.errors = []
    
    def update_company_context(self, company_data: Dict[str, Any], lookup_type: str = "name") -> None:
        """
        Update company context with new information.
        
        Args:
            company_data: Dictionary containing company information
            lookup_type: How the company was looked up (name, ticker, cik)
        """
        if not company_data:
            return
        
        # Handle error case
        if "error" in company_data:
            self.errors.append({
                "type": "company_resolution",
                "error": company_data["error"],
                "timestamp": datetime.now().isoformat()
            })
            return
            
        # Update company context with new data
        self.company_context["name"] = company_data.get("name", self.company_context["name"])
        self.company_context["ticker"] = company_data.get("ticker", self.company_context["ticker"])
        self.company_context["cik"] = company_data.get("cik", self.company_context["cik"])
        self.company_context["exchange"] = company_data.get("exchange", self.company_context["exchange"])
        self.company_context["industry"] = company_data.get("industry", self.company_context["industry"])
        self.company_context["sector"] = company_data.get("sector", self.company_context["sector"])
        self.company_context["most_recent_lookup"] = lookup_type
        
        logger.info(f"Updated company context: {self.company_context['name']} ({self.company_context['ticker']})")
    
    def update_filing_context(self, filing_data: Dict[str, Any]) -> None:
        """
        Update filing context with new information.
        
        Args:
            filing_data: Dictionary containing filing information
        """
        if not filing_data:
            return
        
        # Check if this is a filing object from the Query API
        if "filings" in filing_data and filing_data["filings"]:
            filing = filing_data["filings"][0]  # Take the first filing
            
            # Store the filing for later reference
            if filing not in self.filing_context["filings"]:
                self.filing_context["filings"].append(filing)
            
            # Update current filing
            self.filing_context["current_filing"] = filing
            self.filing_context["form_type"] = filing.get("formType")
            self.filing_context["filing_date"] = filing.get("filedAt")
            self.filing_context["accession_no"] = filing.get("accessionNo")
            self.filing_context["filing_url"] = filing.get("linkToFilingDetails", filing.get("linkToHtml"))
            
            # Extract period information if available
            if "periodOfReport" in filing:
                self.filing_context["period_end_date"] = filing.get("periodOfReport")
                self.financial_context["period_end_date"] = filing.get("periodOfReport")
            
            logger.info(f"Updated filing context: {self.filing_context['form_type']} filed on {self.filing_context['filing_date']}")
        
        # Direct filing data update
        elif isinstance(filing_data, dict):
            for key, value in filing_data.items():
                if key in self.filing_context and value is not None:
                    self.filing_context[key] = value
                    
                    # Also update financial context if relevant
                    if key in ["period_end_date", "fiscal_year", "fiscal_period"]:
                        self.financial_context[key] = value
            
            logger.info(f"Updated filing context with direct data")
    
    def update_section_context(self, section_data: Dict[str, Any]) -> None:
        """
        Update section context with new information.
        
        Args:
            section_data: Dictionary containing section information
        """
        if not section_data:
            return
        
        # Handle error case
        if section_data.get("is_error", False):
            self.errors.append({
                "type": "section_extraction",
                "error": section_data.get("error", "Unknown section extraction error"),
                "section_id": section_data.get("section_id"),
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Update section context
        self.section_context["current_section"] = section_data.get("section_name")
        self.section_context["current_section_id"] = section_data.get("section_id")
        
        # Add to analyzed sections if not already there
        section_info = {
            "section_id": section_data.get("section_id"),
            "section_name": section_data.get("section_name"),
            "form_type": section_data.get("form_type", self.filing_context["form_type"]),
            "filing_url": self.filing_context["filing_url"],
            "filing_date": self.filing_context["filing_date"],
            "content_available": True
        }
        
        if section_info not in self.section_context["sections_analyzed"]:
            self.section_context["sections_analyzed"].append(section_info)
        
        logger.info(f"Updated section context: {self.section_context['current_section']} (ID: {self.section_context['current_section_id']})")
    
    def update_financial_context(self, financial_data: Dict[str, Any]) -> None:
        """
        Update financial data context with new information.
        
        Args:
            financial_data: Dictionary containing financial data
        """
        if not financial_data:
            return
        
        # Handle error case
        if financial_data.get("is_error", False):
            self.errors.append({
                "type": "financial_data",
                "error": financial_data.get("error", "Unknown financial data error"),
                "timestamp": datetime.now().isoformat()
            })
            self.financial_context["xbrl_data_available"] = False
            return
            
        # XBRL data is available
        self.financial_context["xbrl_data_available"] = True
        
        # Update fiscal period information from XBRL data
        data = financial_data.get("data", {})
        
        if "CoverPage" in data:
            cover_data = data["CoverPage"]
            if "DocumentFiscalPeriodFocus" in cover_data:
                self.financial_context["fiscal_period"] = cover_data["DocumentFiscalPeriodFocus"]
                self.filing_context["fiscal_period"] = cover_data["DocumentFiscalPeriodFocus"]
            if "DocumentFiscalYearFocus" in cover_data:
                self.financial_context["fiscal_year"] = cover_data["DocumentFiscalYearFocus"]
                self.filing_context["fiscal_year"] = cover_data["DocumentFiscalYearFocus"]
            if "DocumentPeriodEndDate" in cover_data:
                self.financial_context["period_end_date"] = cover_data["DocumentPeriodEndDate"]
                self.filing_context["period_end_date"] = cover_data["DocumentPeriodEndDate"]
        
        # Extract key metrics if available in the summary
        if "summary" in financial_data and "key_metrics" in financial_data["summary"]:
            metrics = financial_data["summary"]["key_metrics"]
            for metric, value in metrics.items():
                self.financial_context["metrics_retrieved"][metric] = {
                    "value": value,
                    "filing_date": self.filing_context["filing_date"],
                    "period_end_date": self.filing_context.get("period_end_date"),
                    "form_type": self.filing_context["form_type"],
                    "fiscal_period": self.financial_context.get("fiscal_period"),
                    "fiscal_year": self.financial_context.get("fiscal_year")
                }
        
        logger.info(f"Updated financial context with XBRL data")
    
    def update_query_context(self, query: str, query_type: Optional[str] = None) -> None:
        """
        Update query context with new query information.
        
        Args:
            query: User query string
            query_type: Type of query (financial, textual, comparative)
        """
        self.query_context["original_query"] = query
        
        if query_type:
            self.query_context["query_type"] = query_type
        
        logger.info(f"Updated query context: {query}")
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current context.
        
        Returns:
            Dictionary containing context summary
        """
        return {
            "company": {
                "name": self.company_context["name"],
                "ticker": self.company_context["ticker"],
                "cik": self.company_context["cik"]
            },
            "filing": {
                "form_type": self.filing_context["form_type"],
                "filing_date": self.filing_context["filing_date"],
                "period_end_date": self.filing_context["period_end_date"]
            },
            "section": {
                "current_section": self.section_context["current_section"],
                "sections_analyzed": len(self.section_context["sections_analyzed"])
            },
            "financial": {
                "xbrl_available": self.financial_context["xbrl_data_available"],
                "metrics_retrieved": list(self.financial_context["metrics_retrieved"].keys()),
                "fiscal_period": self.financial_context["fiscal_period"],
                "fiscal_year": self.financial_context["fiscal_year"]
            },
            "errors": len(self.errors)
        }
    
    def enrich_response(self, response: str) -> str:
        """
        Enrich a response with relevant context.
        
        Args:
            response: The original response
            
        Returns:
            Enriched response with context
        """
        if not response:
            return response
            
        # Create context parts
        context_parts = []
        
        # Add company context
        if self.company_context["name"]:
            company_info = f"{self.company_context['name']}"
            if self.company_context["ticker"]:
                company_info += f" ({self.company_context['ticker']})"
            context_parts.append(company_info)
        
        # Add filing context
        if self.filing_context["form_type"] and self.filing_context["filing_date"]:
            filing_info = f"{self.filing_context['form_type']} filed on {self.filing_context['filing_date']}"
            if self.filing_context["period_end_date"]:
                filing_info += f" for the period ended {self.filing_context['period_end_date']}"
            context_parts.append(filing_info)
            
        # Add financial period context for XBRL data (use get with None default to avoid KeyError)
        if self.financial_context.get("fiscal_period") and self.financial_context.get("fiscal_year"):
            context_parts.append(f"Fiscal {self.financial_context['fiscal_period']} {self.financial_context['fiscal_year']}")
        
        # Create context header
        if context_parts:
            context_header = " | ".join(context_parts)
            return f"Context: {context_header}\n\n{response}"
        
        return response
    
    def clear_context(self) -> None:
        """Clear all context data."""
        self.__init__()
        logger.info("Context cleared")

    # Compatibility methods for the new API calls
    def set_company_context(self, company_info: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """
        Set company context from company info. 
        Handles both single dictionary and list of dictionaries.
        
        Args:
            company_info: Company information dictionary or list of dictionaries
        """
        if isinstance(company_info, list) and company_info:
            # Use the first result if it's a list
            self.update_company_context(company_info[0], "api_resolution")
        else:
            self.update_company_context(company_info, "api_resolution")
    
    def set_filing_context(self, filing_info: Dict[str, Any]) -> None:
        """
        Set filing context from filing info.
        
        Args:
            filing_info: Filing information dictionary
        """
        self.update_filing_context({"filings": [filing_info]})
    
    def set_section_context(self, section_info: Dict[str, Any]) -> None:
        """
        Set section context from section info.
        
        Args:
            section_info: Section information dictionary
        """
        self.update_section_context(section_info)
    
    def set_xbrl_context(self, xbrl_info: Dict[str, Any]) -> None:
        """
        Set XBRL context from XBRL info.
        
        Args:
            xbrl_info: XBRL information dictionary
        """
        self.update_financial_context(xbrl_info)
    
    def get_filing_url(self) -> Optional[str]:
        """
        Get filing URL from context if available.
        
        Returns:
            Filing URL string or None if not available
        """
        return self.filing_context.get("filing_url")


# For testing
if __name__ == "__main__":
    # Create context
    context = SECContext()
    
    # Test company context
    context.update_company_context({
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "cik": "0000320193",
        "exchange": "NASDAQ",
        "industry": "Technology",
        "sector": "Electronic Technology"
    })
    
    # Test filing context
    context.update_filing_context({
        "filings": [{
            "formType": "10-K",
            "filedAt": "2023-11-03",
            "accessionNo": "0000320193-23-000106",
            "linkToFilingDetails": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
            "periodOfReport": "2023-09-30"
        }]
    })
    
    # Print context summary
    print(context.get_context_summary())
    
    # Test response enrichment
    response = "Apple reported $383.3 billion in revenue for the fiscal year 2023."
    enriched = context.enrich_response(response)
    print("\nEnriched Response:")
    print(enriched) 