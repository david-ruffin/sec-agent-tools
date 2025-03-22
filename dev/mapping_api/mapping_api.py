"""
Enhanced SEC-API Mapping Implementation with complete functionality.
"""

import os
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv
from sec_api import MappingApi
from dataclasses import dataclass
from enum import Enum

# Load environment variables
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")

if not SEC_API_KEY:
    raise ValueError("SEC_API_KEY not found in environment variables")

class ParameterType(str, Enum):
    """Valid parameter types for company resolution"""
    CUSIP = "cusip"
    CIK = "cik"
    TICKER = "ticker"
    NAME = "name"
    EXCHANGE = "exchange"
    SECTOR = "sector"
    INDUSTRY = "industry"

@dataclass
class CompanyInfo:
    """Structured company information from SEC-API"""
    name: str
    ticker: str
    cik: str
    cusip: str
    exchange: str
    is_delisted: bool
    category: str
    sector: str
    industry: str
    sic: str
    sic_sector: str
    sic_industry: str
    fama_sector: str
    fama_industry: str
    currency: str
    location: str
    id: str

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'CompanyInfo':
        """Create CompanyInfo instance from API response"""
        return cls(
            name=data.get('name', ''),
            ticker=data.get('ticker', ''),
            cik=data.get('cik', ''),
            cusip=data.get('cusip', ''),
            exchange=data.get('exchange', ''),
            is_delisted=data.get('isDelisted', False),
            category=data.get('category', ''),
            sector=data.get('sector', ''),
            industry=data.get('industry', ''),
            sic=data.get('sic', ''),
            sic_sector=data.get('sicSector', ''),
            sic_industry=data.get('sicIndustry', ''),
            fama_sector=data.get('famaSector', ''),
            fama_industry=data.get('famaIndustry', ''),
            currency=data.get('currency', ''),
            location=data.get('location', ''),
            id=data.get('id', '')
        )

class SECMappingAPI:
    """Enhanced SEC Mapping API implementation"""
    
    def __init__(self, api_key: Optional[str] = None, proxies: Optional[Dict[str, str]] = None):
        """
        Initialize the SEC Mapping API client
        
        Args:
            api_key: SEC API key (optional, defaults to environment variable)
            proxies: Optional proxy configuration for HTTP/HTTPS requests
        """
        self.api_key = api_key or SEC_API_KEY
        if not self.api_key:
            raise ValueError("API key must be provided or set in SEC_API_KEY environment variable")
            
        self.mapping_api = MappingApi(api_key=self.api_key, proxies=proxies)

    def resolve_company(
        self,
        parameter_type: Union[str, ParameterType],
        value: str,
        return_first_match: bool = False
    ) -> Union[List[CompanyInfo], CompanyInfo, None]:
        """
        Resolve company information using various parameters
        
        Args:
            parameter_type: Type of parameter to resolve (use ParameterType enum)
            value: Value to resolve
            return_first_match: If True, returns only the first match (if any)
            
        Returns:
            List of CompanyInfo objects, single CompanyInfo if return_first_match=True,
            or None if no matches found
            
        Raises:
            ValueError: If parameter_type is invalid
            Exception: For API errors
        """
        # Validate parameter type
        if isinstance(parameter_type, str):
            try:
                parameter_type = ParameterType(parameter_type.lower())
            except ValueError:
                valid_types = ", ".join([t.value for t in ParameterType])
                raise ValueError(
                    f"Invalid parameter_type: {parameter_type}. Must be one of: {valid_types}"
                )
        
        try:
            result = self.mapping_api.resolve(parameter_type.value, value)
            
            # Convert API response to CompanyInfo objects
            companies = [CompanyInfo.from_api_response(item) for item in result]
            
            if not companies:
                return None
                
            return companies[0] if return_first_match else companies
            
        except Exception as e:
            raise Exception(f"Error resolving company info: {str(e)}")

    def search_by_exchange(self, exchange: str) -> List[CompanyInfo]:
        """
        Get all companies listed on a specific exchange
        
        Args:
            exchange: Exchange name (e.g., 'NASDAQ', 'NYSE')
            
        Returns:
            List of CompanyInfo objects
        """
        return self.resolve_company(ParameterType.EXCHANGE, exchange)

    def search_by_sector(self, sector: str) -> List[CompanyInfo]:
        """
        Get all companies in a specific sector
        
        Args:
            sector: Sector name (e.g., 'Technology', 'Healthcare')
            
        Returns:
            List of CompanyInfo objects
        """
        return self.resolve_company(ParameterType.SECTOR, sector)

    def search_by_industry(self, industry: str) -> List[CompanyInfo]:
        """
        Get all companies in a specific industry
        
        Args:
            industry: Industry name
            
        Returns:
            List of CompanyInfo objects
        """
        return self.resolve_company(ParameterType.INDUSTRY, industry)

    def get_company_by_ticker(self, ticker: str) -> Optional[CompanyInfo]:
        """
        Get company information by ticker symbol
        
        Args:
            ticker: Company ticker symbol
            
        Returns:
            CompanyInfo object if found, None otherwise
        """
        return self.resolve_company(ParameterType.TICKER, ticker, return_first_match=True)

    def get_company_by_cik(self, cik: str) -> Optional[CompanyInfo]:
        """
        Get company information by CIK number
        
        Args:
            cik: Company CIK number
            
        Returns:
            CompanyInfo object if found, None otherwise
        """
        return self.resolve_company(ParameterType.CIK, cik, return_first_match=True)

    def get_company_by_cusip(self, cusip: str) -> Optional[CompanyInfo]:
        """
        Get company information by CUSIP
        
        Args:
            cusip: Company CUSIP
            
        Returns:
            CompanyInfo object if found, None otherwise
        """
        return self.resolve_company(ParameterType.CUSIP, cusip, return_first_match=True)

    def get_company_by_name(self, name: str) -> List[CompanyInfo]:
        """
        Get company information by name (may return multiple matches)
        
        Args:
            name: Company name
            
        Returns:
            List of CompanyInfo objects matching the name
        """
        return self.resolve_company(ParameterType.NAME, name) or []

if __name__ == "__main__":
    # Example usage and tests
    api = SECMappingAPI()
    
    # Test with Tesla
    print("\nTest 1 - Get company by ticker:")
    tesla = api.get_company_by_ticker("TSLA")
    if tesla:
        print(f"Found: {tesla.name} ({tesla.ticker})")
        print(f"CIK: {tesla.cik}")
        print(f"Industry: {tesla.industry}")
        
    # Test with Microsoft
    print("\nTest 2 - Get company by name:")
    microsoft_matches = api.get_company_by_name("Microsoft Corporation")
    for company in microsoft_matches:
        print(f"Found: {company.name} ({company.ticker})")
        
    # Test exchange search
    print("\nTest 3 - First 5 NASDAQ companies:")
    nasdaq_companies = api.search_by_exchange("NASDAQ")
    for company in (nasdaq_companies or [])[:5]:
        print(f"{company.name} ({company.ticker})") 