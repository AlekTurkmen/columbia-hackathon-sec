# MCP for SEC EDGAR Database semantic search

---

One liner: Fast MCP semantic search 

- There are 2 main SEC datasets
    1. Company Facts 
        1. [1.34 GB ZIP - 18,360,620,696 bytes (18.4 GB on disk) for 19,051 item]
    2. Submission 
        1. [1.49 GB ZIP - 5,359,128,717 bytes (7.52 GB on disk) for 946,190 items]
- There are 4 main SEC endpoints
    1. [data.sec.gov/submissions/AAPL](http://data.sec.gov/submissions/AAPL) → CIK
        1. https://data.sec.gov/submissions/CIK##########.json
    2. data.sec.gov/api/xbrl/companyconcept/
        1. https://data.sec.gov/api/xbrl/companyconcept/CIK##########/us-gaap/AccountsPayableCurrent.json
    3. data.sec.gov/api/xbrl/companyfacts/
        1. https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
    4. data.sec.gov/api/xbrl/frames/
        1. https://data.sec.gov/api/xbrl/frames/us-gaap/AccountsPayableCurrent/USD/CY2019Q1I.json

For CIK → Ticker Mapping (CIK0000320193 → $APPL)

https://www.sec.gov/files/company_tickers.json

API has 10 requests/sec rate limit based on IP

Files like CIK0000001750-submissions-001.json can be ignored, since those are for fillings that are very old (first json file has most recent 1,000 fillings)