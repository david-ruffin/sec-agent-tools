"""
SEC Edgar Entities API Tool - Version 2
Provides access to SEC EDGAR entity information through sec-api.io
"""

import os
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv
from sec_api import EdgarEntitiesApi
import pandas as pd

class SECEdgarEntitiesAPI:
    """
    A tool for accessing SEC EDGAR entity information.
    Designed for use with LangChain agents.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the SEC Edgar Entities API tool."""
        if api_key is None:
            load_dotenv()
            api_key = os.getenv('SEC_API_KEY')
            
        if not api_key:
            raise ValueError("SEC API key is required. Set it in .env file or pass directly.")
            
        self.api = EdgarEntitiesApi(api_key)
        
    def _structure_entity_data(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure raw entity data into organized categories.
        """
        return {
            "basic_info": {
                "cik": entity.get("cik"),
                "name": entity.get("name"),
                "phone": entity.get("phone"),
                "irs_number": entity.get("irsNo")
            },
            "classification": {
                "sic": entity.get("sic"),
                "sic_description": entity.get("sicLabel"),
                "filer_category": entity.get("filerCategory"),
                "state_of_incorporation": entity.get("stateOfIncorporation")
            },
            "address": {
                "business": {
                    "street": entity.get("businessAddress", {}).get("street1"),
                    "city": entity.get("businessAddress", {}).get("city"),
                    "state": entity.get("businessAddress", {}).get("state"),
                    "zip": entity.get("businessAddress", {}).get("zip"),
                    "country": entity.get("businessAddress", {}).get("country", "US")
                },
                "mailing": {
                    "street": entity.get("mailingAddress", {}).get("street1"),
                    "city": entity.get("mailingAddress", {}).get("city"),
                    "state": entity.get("mailingAddress", {}).get("state"),
                    "zip": entity.get("mailingAddress", {}).get("zip"),
                    "country": entity.get("mailingAddress", {}).get("country", "US")
                }
            },
            "filing_details": {
                "fiscal_year_end": entity.get("fiscalYearEnd"),
                "supported_forms": [
                    form_type for form_type, supported 
                    in entity.get("formTypes", {}).items() 
                    if supported
                ],
                "latest_filing_date": entity.get("cikUpdatedAt")
            },
            "audit_info": {
                "auditor_name": entity.get("auditorName"),
                "auditor_location": entity.get("auditorLocation"),
                "latest_audit_date": entity.get("latestIcfrAuditFiledAt")
            },
            "status": {
                "current_reporting": entity.get("currentReportingStatus", False),
                "voluntary_filer": entity.get("voluntaryFiler", False),
                "well_known_seasoned_issuer": entity.get("wellKnownSeasonedIssuer", False),
                "emerging_growth_company": entity.get("emergingGrowthCompany", False)
            }
        }

    def get_entity_data(self, 
                       query: str,
                       start_index: str = "0",
                       size: str = "50",
                       sort_field: str = "cikUpdatedAt",
                       sort_order: str = "desc",
                       format_output: bool = True) -> Dict[str, Any]:
        """
        Search and retrieve entity information from SEC EDGAR.
        
        Args:
            query (str): Search query (e.g., "cik:1318605", "ticker:TSLA")
            start_index (str): Starting index for pagination
            size (str): Number of results to return
            sort_field (str): Field to sort by
            sort_order (str): Sort order ("asc" or "desc")
            format_output (bool): Whether to return formatted output (default: True)
            
        Returns:
            Dict containing the search results and metadata
        """
        try:
            search_request = {
                "query": query,
                "from": start_index,
                "size": size,
                "sort": [{sort_field: {"order": sort_order}}]
            }
            
            response = self.api.get_data(search_request)
            
            if not format_output:
                return response
            
            # Structure the response
            entities = response.get("data", [])
            structured_entities = [
                self._structure_entity_data(entity) 
                for entity in entities
            ]
            
            return {
                "data": structured_entities,
                "metadata": {
                    "query": query,
                    "total_results": len(entities),
                    "page_size": int(size),
                    "sort_field": sort_field,
                    "sort_order": sort_order
                }
            }
            
        except Exception as e:
            raise ValueError(f"Error accessing SEC EDGAR API: {str(e)}")
    
    def to_dataframe(self, data: Dict[str, Any], section: Optional[str] = None) -> pd.DataFrame:
        """
        Convert entity data to a pandas DataFrame.
        
        Args:
            data: The response from get_entity_data
            section: Optional section to convert (e.g., 'basic_info', 'address')
            
        Returns:
            pandas DataFrame with the entity data
        """
        if not isinstance(data, dict) or "data" not in data:
            raise ValueError("Invalid data format. Must be response from get_entity_data")
            
        entities = data["data"]
        
        if not entities:
            return pd.DataFrame()
            
        if section:
            # Extract specific section from each entity
            section_data = []
            for entity in entities:
                if section in entity:
                    # Flatten nested dictionaries
                    flattened = {}
                    for key, value in entity[section].items():
                        if isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                flattened[f"{key}_{subkey}"] = subvalue
                        else:
                            flattened[key] = value
                    section_data.append(flattened)
            return pd.DataFrame(section_data)
        else:
            # Flatten all sections
            flat_data = []
            for entity in entities:
                flat_entity = {}
                for section_name, section_data in entity.items():
                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            if isinstance(value, dict):
                                for subkey, subvalue in value.items():
                                    flat_entity[f"{section_name}_{key}_{subkey}"] = subvalue
                            else:
                                flat_entity[f"{section_name}_{key}"] = value
                    else:
                        flat_entity[section_name] = section_data
                flat_data.append(flat_entity)
            return pd.DataFrame(flat_data)

def test_documentation_example():
    """Test the example from the documentation with formatted output."""
    try:
        # Initialize the tool
        tool = SECEdgarEntitiesAPI()
        
        print("\nTesting raw API response:")
        # Test with Tesla's CIK - raw response
        raw_response = tool.get_entity_data("cik:1318605", format_output=False)
        print("\nRaw Response Data:")
        print(raw_response["data"])
        
        print("\nTesting formatted response:")
        # Test with Tesla's CIK - formatted response
        formatted_response = tool.get_entity_data("cik:1318605")
        
        # Print each section clearly
        for entity in formatted_response["data"]:
            print("\nEntity Information:")
            for section, data in entity.items():
                print(f"\n{section.upper()}:")
                for key, value in data.items():
                    print(f"  {key}: {value}")
        
        print("\nTesting DataFrame conversion:")
        # Convert to DataFrame
        df = tool.to_dataframe(formatted_response)
        print("\nFull DataFrame Info:")
        print(df.info())
        
        # Test specific section
        print("\nBasic Info DataFrame:")
        basic_info_df = tool.to_dataframe(formatted_response, "basic_info")
        print(basic_info_df)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_documentation_example() 