# Missing SEC-API Agent Plans

Based on the SEC-API Python documentation, the following APIs don't yet have plan files in our agents directory:

## Form-Specific APIs

1. **Form 13F API**
   - Institutional Investment Manager Holdings
   - Cover Pages
   
2. **Form 3/4/5 API**
   - Insider Trading Disclosures
   
3. **Form 13D/13G API**
   - Activist and Passive Investor Holdings
   
4. **Form N-PORT API**
   - Mutual Funds, ETFs and Closed-End Fund Holdings
   
5. **Form N-PX API**
   - Proxy Voting Records
   
6. **Form S-1/424B4 API**
   - Registration Statements and Prospectuses
   - IPOs, Debt/Warrants Offerings
   
7. **Form C API**
   - Crowdfunding Offerings & Campaigns
   
8. **Form D API**
   - Private Security Offerings

## Company Information APIs

9. **Form ADV API**
   - Investment Advisors
   - Firm & Individual Advisors
   - Brochures
   - Schedules
   
10. **Directors & Board Members API**
    - Board member information
    - Qualifications and experience
    - Committee memberships
   
11. **Executive Compensation API**
    - Standardized compensation data
    - Annual salary, option awards, etc.
    
12. **Outstanding Shares & Public Float API**
    - Share count data
    - Public float information
    
13. **Company Subsidiary API**
    - Company subsidiary information

## Enforcement Action APIs

14. **SEC Enforcement Actions API**
    - Enforcement action information
    
15. **SEC Litigation Releases API**
    - Litigation release information
    
16. **SEC Administrative Proceedings API**
    - Administrative proceeding information
    
17. **AAER Database API**
    - Accounting and Auditing Enforcement Releases
    
18. **SRO Filings Database API**
    - Self-Regulatory Organization filings

## Other APIs

19. **Download API**
    - Download any SEC filing, exhibit or attached file
    
20. **PDF Generator API**
    - Generate PDFs from SEC filings and exhibits
    
21. **Real-Time Filing Stream API**
    - Stream new filings in real-time
    
22. **EDGAR Entities Database API**
    - Entity database information

## Next Steps

1. Create plan files for each missing API
2. Implement agents following the plans
3. Create comprehensive tests for each agent
4. Document usage examples

Each plan file should follow our standardized format:
- API overview
- Available methods
- Parameters and options
- Response format
- Implementation notes 