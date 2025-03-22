# SEC-API Python Package - Complete API Endpoints Overview

## 1. EDGAR Filing Search & Download APIs

### 1.1 Query API (Filing Search)
**Purpose:** Search and filter all 18M+ filings and exhibits from SEC EDGAR since 1993

**Example 1 - Get Tesla's 10-Q filings from 2020:**
```python
from sec_api import QueryApi

queryApi = QueryApi(api_key="YOUR_API_KEY")
query = {
    "query": "ticker:TSLA AND filedAt:[2020-01-01 TO 2020-12-31] AND formType:\"10-Q\"",
    "from": "0",
    "size": "10",
    "sort": [{ "filedAt": { "order": "desc" } }]
}
filings = queryApi.get_filings(query)
```

**Example 2 - Find recent 8-K filings with Item 9.01:**
```python
query = {
    "query": "formType:\"8-K\" AND items:\"9.01\"",
    "from": "0",
    "size": "10",
    "sort": [{ "filedAt": { "order": "desc" } }]
}
filings = queryApi.get_filings(query)
```

### 1.2 Real-Time Filing Stream API
**Purpose:** Receive new filings as soon as they are published on SEC EDGAR

**Example 1 - Set up a real-time stream for all filings:**
```python
from sec_api import RealTimeStream

def filing_callback(filing):
    print(f"New filing: {filing['formType']} for {filing['companyName']}")

stream = RealTimeStream("YOUR_API_KEY")
stream.on_filing(filing_callback)
stream.start()
```

**Example 2 - Filter for specific form types:**
```python
from sec_api import RealTimeStream

def filing_callback(filing):
    print(f"New 10-K/Q filing: {filing['formType']} for {filing['companyName']}")

stream = RealTimeStream("YOUR_API_KEY")
stream.on_filing(filing_callback, form_types=["10-K", "10-Q"])
stream.start()
```

### 1.3 Download API (RenderApi)
**Purpose:** Download any SEC filing, exhibit and attached file

**Example 1 - Download HTML filing:**
```python
from sec_api import RenderApi

renderApi = RenderApi("YOUR_API_KEY")
url_8k_html = "https://www.sec.gov/Archives/edgar/data/1045810/000104581023000014/nvda-20230222.htm"
filing_8k_html = renderApi.get_file(url_8k_html)

# Save to disk
with open("filing_8k_html.htm", "wb") as f:
    f.write(filing_8k_html.encode("utf-8"))
```

**Example 2 - Download binary files (PDF, Excel, Images):**
```python
url_pdf_file = "https://www.sec.gov/Archives/edgar/data/1798925/999999999724004095/filename1.pdf"
url_excel_file = "https://www.sec.gov/Archives/edgar/data/1045810/000104581023000014/Financial_Report.xlsx"

pdf_file = renderApi.get_file(url_pdf_file, return_binary=True)
excel_file = renderApi.get_file(url_excel_file, return_binary=True)

# Save to disk
with open("document.pdf", "wb") as f:
    f.write(pdf_file)
```

### 1.4 PDF Generator API
**Purpose:** Convert any SEC filing or exhibit into PDF format

**Example 1 - Generate PDF from 10-K filing:**
```python
from sec_api import PdfGeneratorApi

pdfGeneratorApi = PdfGeneratorApi("YOUR_API_KEY")
url_10k_filing = "https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm"
pdf_10k_filing = pdfGeneratorApi.get_pdf(url_10k_filing)

# Save PDF to disk
with open("apple_10k.pdf", "wb") as f:
    f.write(pdf_10k_filing)
```

**Example 2 - Generate PDF from an 8-K exhibit:**
```python
url_8k_exhibit = "https://www.sec.gov/ix?doc=/Archives/edgar/data/1320695/000132069520000148/ths12-31x201910krecast.htm"
pdf_8k_exhibit = pdfGeneratorApi.get_pdf(url_8k_exhibit)

# Save PDF to disk
with open("exhibit_8k.pdf", "wb") as f:
    f.write(pdf_8k_exhibit)
```

### 1.5 Full-Text Search API
**Purpose:** Search the full text content of all filings submitted since 2001

**Example 1 - Search for climate risk mentions:**
```python
from sec_api import FullTextSearchApi

fullTextSearchApi = FullTextSearchApi("YOUR_API_KEY")
query = {
    "query": "climate risk",
    "formTypes": ["10-K"],
    "startDate": "2020-01-01",
    "endDate": "2021-12-31"
}
results = fullTextSearchApi.get_filings(query)
```

**Example 2 - Search with proximity operators:**
```python
query = {
    "query": "cybersecurity NEAR/10 risk",  # Find where "cybersecurity" appears within 10 words of "risk"
    "formTypes": ["10-K", "10-Q"],
    "startDate": "2021-01-01",
    "endDate": "2022-12-31"
}
results = fullTextSearchApi.get_filings(query)
```

## 2. Converter & Extractor APIs

### 2.1 XBRL-to-JSON Converter API
**Purpose:** Convert XBRL financial statements to JSON format

**Example 1 - Extract financial statements from 10-K:**
```python
from sec_api import XbrlApi

xbrlApi = XbrlApi("YOUR_API_KEY")
filing_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm"
financial_data = xbrlApi.xbrl_to_json(filing_url)

# Access specific financial statements
income_statement = financial_data["IncomeStatement"]
balance_sheet = financial_data["BalanceSheet"]
cash_flow = financial_data["CashFlow"]
```

**Example 2 - Filter for specific metrics:**
```python
filing_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
financial_data = xbrlApi.xbrl_to_json(filing_url)

# Get revenue and net income
revenue = financial_data["IncomeStatement"]["Revenue"]
net_income = financial_data["IncomeStatement"]["NetIncomeLoss"]
```

### 2.2 10-K/10-Q/8-K Section Extraction API
**Purpose:** Extract specific sections from major SEC filings

**Example 1 - Extract Risk Factors section from 10-K:**
```python
from sec_api import ExtractorApi

extractorApi = ExtractorApi("YOUR_API_KEY")
filing_url = "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm"
risk_factors = extractorApi.get_section(filing_url, "1A")  # Item 1A: Risk Factors
```

**Example 2 - Extract MD&A section from 10-Q:**
```python
filing_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019322000070/aapl-20220625.htm"
mda_section = extractorApi.get_section(filing_url, "2")  # Item 2: Management's Discussion and Analysis
```

## 3. Investment Advisers APIs

### 3.1 Form ADV API
**Purpose:** Access Investment Advisor data, brochures, and schedules

**Example 1 - Get Form ADV data for an investment adviser:**
```python
from sec_api import FormAdvApi

formAdvApi = FormAdvApi("YOUR_API_KEY")
crd_number = "104569"  # BlackRock
adv_data = formAdvApi.get_adv(crd_number)
```

**Example 2 - Get adviser's brochure (Part 2A):**
```python
crd_number = "104569"  # BlackRock
brochure = formAdvApi.get_brochure(crd_number)
```

## 4. Ownership Data APIs

### 4.1 Form 3/4/5 API (Insider Trading Disclosures)
**Purpose:** Access Insider Trading Disclosures

**Example 1 - Get insider transactions for a company:**
```python
from sec_api import InsiderTradingApi

insiderApi = InsiderTradingApi("YOUR_API_KEY")
ticker = "AAPL"
transactions = insiderApi.get_transactions(ticker)
```

**Example 2 - Get transactions for a specific insider:**
```python
cik = "0001214156"  # Tim Cook
transactions = insiderApi.get_transactions_by_insider(cik)
```

### 4.2 Form 13F API
**Purpose:** Access Institutional Investment Manager Holdings

**Example 1 - Get holdings for an investment manager:**
```python
from sec_api import Form13FApi

form13fApi = Form13FApi("YOUR_API_KEY")
cik = "0001036308"  # Berkshire Hathaway
quarter = "2022-Q1"
holdings = form13fApi.get_holdings(cik, quarter)
```

**Example 2 - Get recent holders of a specific security:**
```python
cusip = "037833100"  # Apple Inc.
quarter = "2022-Q2"
holders = form13fApi.get_holders(cusip, quarter)
```

### 4.3 Form 13D/13G API
**Purpose:** Access Activist and Passive Investor Holdings

**Example 1 - Get 13D filings for a company:**
```python
from sec_api import Form13DGApi

form13dgApi = Form13DGApi("YOUR_API_KEY")
ticker = "TWTR"  # Twitter
filings = form13dgApi.get_filings(ticker, form_type="13D")
```

**Example 2 - Get 13G filings by a specific filer:**
```python
cik = "0001067983"  # Vanguard Group
filings = form13dgApi.get_filings_by_filer(cik, form_type="13G")
```

### 4.4 Form N-PORT API
**Purpose:** Access Mutual Funds, ETFs and Closed-End Fund Holdings

**Example 1 - Get fund holdings:**
```python
from sec_api import FormNportApi

nportApi = FormNportApi("YOUR_API_KEY")
cik = "0000936653"  # Fidelity
filing_date = "2022-03-31"
holdings = nportApi.get_holdings(cik, filing_date)
```

**Example 2 - Get funds holding a specific security:**
```python
cusip = "037833100"  # Apple Inc.
filing_date = "2022-06-30"
holders = nportApi.get_holders(cusip, filing_date)
```

## 5. Proxy Voting Records

### 5.1 Form N-PX Proxy Voting Records API
**Purpose:** Access proxy voting records of mutual funds and ETFs

**Example 1 - Get voting records for a fund:**
```python
from sec_api import FormNpxApi

npxApi = FormNpxApi("YOUR_API_KEY")
cik = "0000036405"  # Vanguard Index Funds
period = "2022"
votes = npxApi.get_votes(cik, period)
```

**Example 2 - Get proxy votes related to specific issues:**
```python
cik = "0000036405"  # Vanguard Index Funds
period = "2022"
keyword = "climate change"
votes = npxApi.get_votes(cik, period, keyword=keyword)
```

## 6. Security Offerings APIs

### 6.1 Form S-1/424B4 API
**Purpose:** Access Registration Statements and Prospectuses

**Example 1 - Get S-1 filings for IPOs:**
```python
from sec_api import RegistrationApi

registrationApi = RegistrationApi("YOUR_API_KEY")
start_date = "2021-01-01"
end_date = "2021-12-31"
s1_filings = registrationApi.get_filings("S-1", start_date, end_date)
```

**Example 2 - Get 424B4 prospectus filings:**
```python
start_date = "2022-01-01"
end_date = "2022-06-30"
prospectus_filings = registrationApi.get_filings("424B4", start_date, end_date)
```

### 6.2 Form C API
**Purpose:** Access Crowdfunding Offerings & Campaigns

**Example 1 - Get crowdfunding offerings:**
```python
from sec_api import FormCApi

formCApi = FormCApi("YOUR_API_KEY")
start_date = "2021-01-01"
end_date = "2021-12-31"
offerings = formCApi.get_offerings(start_date, end_date)
```

**Example 2 - Get offerings by a specific issuer:**
```python
issuer_name = "Specific Company Name"
offerings = formCApi.get_offerings_by_issuer(issuer_name)
```

### 6.3 Form D API
**Purpose:** Access Private Security Offerings

**Example 1 - Get Form D filings for private offerings:**
```python
from sec_api import FormDApi

formDApi = FormDApi("YOUR_API_KEY")
start_date = "2022-01-01"
end_date = "2022-06-30"
offerings = formDApi.get_filings(start_date, end_date)
```

**Example 2 - Get offerings by industry:**
```python
industry = "Biotechnology"
offerings = formDApi.get_filings_by_industry(industry)
```

## 7. Structured Material Event Data (Form 8-K)

### 7.1 Item 4.01 API (Auditor Changes)
**Purpose:** Access data on auditor and accountant changes

**Example 1 - Get auditor changes:**
```python
from sec_api import Form8KItemApi

form8kItemApi = Form8KItemApi("YOUR_API_KEY")
start_date = "2021-01-01"
end_date = "2021-12-31"
auditor_changes = form8kItemApi.get_item_401(start_date, end_date)
```

**Example 2 - Get auditor changes for a specific company:**
```python
ticker = "AAPL"
auditor_changes = form8kItemApi.get_item_401_by_company(ticker)
```

### 7.2 Item 4.02 API (Financial Restatements)
**Purpose:** Access data on financial restatements and non-reliance notices

**Example 1 - Get financial restatements:**
```python
start_date = "2021-01-01"
end_date = "2021-12-31"
restatements = form8kItemApi.get_item_402(start_date, end_date)
```

**Example 2 - Get restatements by reason:**
```python
reason = "accounting error"
restatements = form8kItemApi.get_item_402_by_reason(reason)
```

### 7.3 Item 5.02 API (Director/Officer Changes)
**Purpose:** Access data on changes of directors and board members

**Example 1 - Get director/officer changes:**
```python
start_date = "2022-01-01"
end_date = "2022-06-30"
changes = form8kItemApi.get_item_502(start_date, end_date)
```

**Example 2 - Get CEO changes:**
```python
position = "CEO"
changes = form8kItemApi.get_item_502_by_position(position)
```

## 8. Public Company Data APIs

### 8.1 Directors & Board Members API
**Purpose:** Access data on company directors and board members

**Example 1 - Get board members for a company:**
```python
from sec_api import BoardMembersApi

boardApi = BoardMembersApi("YOUR_API_KEY")
ticker = "MSFT"
board_members = boardApi.get_board(ticker)
```

**Example 2 - Get directors serving on multiple boards:**
```python
min_boards = 3
directors = boardApi.get_directors_with_multiple_boards(min_boards)
```

### 8.2 Executive Compensation Data API
**Purpose:** Access data on executive compensation

**Example 1 - Get executive compensation for a company:**
```python
from sec_api import CompensationApi

compensationApi = CompensationApi("YOUR_API_KEY")
ticker = "AMZN"
compensation_data = compensationApi.get_compensation(ticker)
```

**Example 2 - Get CEO compensation across industry:**
```python
industry = "Technology"
position = "CEO"
compensation_data = compensationApi.get_compensation_by_industry(industry, position)
```

### 8.3 Outstanding Shares & Public Float API
**Purpose:** Access data on outstanding shares and public float

**Example 1 - Get outstanding shares for a company:**
```python
from sec_api import SharesApi

sharesApi = SharesApi("YOUR_API_KEY")
ticker = "TSLA"
shares_data = sharesApi.get_outstanding_shares(ticker)
```

**Example 2 - Get public float history:**
```python
ticker = "TSLA"
start_date = "2021-01-01"
end_date = "2022-01-01"
float_history = sharesApi.get_float_history(ticker, start_date, end_date)
```

### 8.4 Company Subsidiary API
**Purpose:** Access data on company subsidiaries

**Example 1 - Get subsidiaries for a company:**
```python
from sec_api import SubsidiaryApi

subsidiaryApi = SubsidiaryApi("YOUR_API_KEY")
ticker = "GOOGL"
subsidiaries = subsidiaryApi.get_subsidiaries(ticker)
```

**Example 2 - Get parent companies in a specific jurisdiction:**
```python
jurisdiction = "Cayman Islands"
companies = subsidiaryApi.get_companies_with_subsidiaries(jurisdiction)
```

## 9. SRO Filings Database API
**Purpose:** Access and search all SRO filings since 1995

**Example 1 - Search NASDAQ SRO filings:**
```python
from sec_api import SroFilingsApi

sroFilingsApi = SroFilingsApi("YOUR_API_KEY")
query = {
    "query": "sro:NASDAQ",
    "from": "0",
    "size": "10",
    "sort": [{"issueDate": {"order": "desc"}}],
}
response = sroFilingsApi.get_data(query)
```

**Example 2 - Search for rule change filings:**
```python
query = {
    "query": "title:\"rule change\"",
    "from": "0",
    "size": "10",
    "sort": [{"issueDate": {"order": "desc"}}],
}
response = sroFilingsApi.get_data(query)
```

## 10. Enforcement Actions APIs

### 10.1 SEC Enforcement Actions API
**Purpose:** Access data on SEC enforcement actions

**Example 1 - Get recent enforcement actions:**
```python
from sec_api import EnforcementApi

enforcementApi = EnforcementApi("YOUR_API_KEY")
start_date = "2022-01-01"
end_date = "2022-06-30"
actions = enforcementApi.get_actions(start_date, end_date)
```

**Example 2 - Get enforcement actions by violation type:**
```python
violation_type = "insider trading"
actions = enforcementApi.get_actions_by_violation(violation_type)
```

### 10.2 SEC Litigation Releases API
**Purpose:** Access data on SEC litigation releases

**Example 1 - Get recent litigation releases:**
```python
from sec_api import LitigationApi

litigationApi = LitigationApi("YOUR_API_KEY")
start_date = "2022-01-01"
end_date = "2022-06-30"
releases = litigationApi.get_releases(start_date, end_date)
```

**Example 2 - Get litigation releases by keyword:**
```python
keyword = "fraud"
releases = litigationApi.get_releases_by_keyword(keyword)
```

### 10.3 SEC Administrative Proceedings API
**Purpose:** Access data on SEC administrative proceedings

**Example 1 - Get recent administrative proceedings:**
```python
from sec_api import AdminProceedingsApi

adminApi = AdminProceedingsApi("YOUR_API_KEY")
start_date = "2022-01-01"
end_date = "2022-06-30"
proceedings = adminApi.get_proceedings(start_date, end_date)
```

**Example 2 - Get proceedings by respondent type:**
```python
respondent_type = "investment adviser"
proceedings = adminApi.get_proceedings_by_respondent(respondent_type)
```

### 10.4 AAER Database API
**Purpose:** Access Accounting and Auditing Enforcement Releases

**Example 1 - Get recent AAERs:**
```python
from sec_api import AaerApi

aaerApi = AaerApi("YOUR_API_KEY")
start_date = "2022-01-01"
end_date = "2022-06-30"
aaers = aaerApi.get_aaers(start_date, end_date)
```

**Example 2 - Get AAERs by accounting issue:**
```python
accounting_issue = "revenue recognition"
aaers = aaerApi.get_aaers_by_issue(accounting_issue)
```

## 11. Utility APIs

### 11.1 CUSIP/CIK/Ticker Mapping API
**Purpose:** Map between different company identifiers

**Example 1 - Map ticker to CIK:**
```python
from sec_api import MappingApi

mappingApi = MappingApi("YOUR_API_KEY")
ticker = "AAPL"
cik = mappingApi.get_cik(ticker)
```

**Example 2 - Map CUSIP to ticker and company name:**
```python
cusip = "037833100"  # Apple Inc.
company_info = mappingApi.get_company_info_by_cusip(cusip)
```

### 11.2 EDGAR Entities Database API
**Purpose:** Access information about all entities in the EDGAR database

**Example 1 - Search for companies by name:**
```python
from sec_api import EdgarEntitiesApi

entitiesApi = EdgarEntitiesApi("YOUR_API_KEY")
company_name = "Apple"
entities = entitiesApi.search_entities(company_name)
```

**Example 2 - Get entity information by CIK:**
```python
cik = "0000320193"  # Apple Inc.
entity_info = entitiesApi.get_entity(cik)
```

## Note
The examples above are provided to illustrate how each API endpoint might work. In practice, the actual implementation details may vary as the SEC-API documentation evolves. For the most up-to-date documentation, always refer to https://sec-api.io/docs. 