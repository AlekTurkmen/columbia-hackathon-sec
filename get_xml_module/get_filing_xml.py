import json
import requests
import time
import os

# =========================
# REQUIRED SEC API HEADERS
# =========================
HEADERS = {
    "User-Agent": "jf3670@columbia.edu",
    "Accept-Encoding": "gzip, deflate",
}

HTML_CACHE = {}

# =========================
# HELPER FUNCTIONS
# =========================
def ticker_to_cik(ticker):
    """Convert ticker symbol to CIK number."""
    import os
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cik_json_path = os.path.join(script_dir, 'cik.json')
    
    with open(cik_json_path, 'r') as f:
        cik_data = json.load(f)
    ticker = ticker.upper()
    for _, company in cik_data.items():
        if company['ticker'] == ticker:
            return str(company['cik_str'])
    return None

def get_xml_files_for_filing(cik, accession):
    """Get XML files ending with _htm.xml for a filing."""
    acc_clean = accession.replace("-", "")
    index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_clean}/index.json"
    data = requests.get(index_url, headers=HEADERS).json()
    items = data["directory"]["item"]
    xml_files = []
    for item in items:
        name = item["name"]
        name_lower = name.lower()
        # Match files ending with _htm.xml (these are the main filing XML files)
        if name_lower.endswith("_htm.xml"):
            file_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_clean}/{name}"
            xml_files.append({"filename": name, "url": file_url})
    time.sleep(0.1)
    return xml_files

def download_text(url, cache_key):
    """Download text file with caching."""
    if cache_key in HTML_CACHE:
        return HTML_CACHE[cache_key]
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    content = response.text
    HTML_CACHE[cache_key] = content
    time.sleep(0.1)
    return content

def save_text_to_file(content, filename, output_dir):
    """Save text content to file."""
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path

# =========================
# MAIN FUNCTION
# =========================
def get_filing_xml(ticker, form_type="10Q", time_interval=None, save=False):
    """
    Simple function to get XML files for SEC filings.
    
    Args:
        ticker: Ticker symbol (e.g., "CRWV")
        form_type: "10Q", "10K", or "both" (default: "10Q")
        time_interval: Tuple of (start_date, end_date) in YYYY-MM-DD format, or None for all (default: None)
        save: If True, save files to disk. If False, only cache in memory (default: False)
    
    Returns:
        List of dictionaries with cached XML content:
        [
            {
                "date": "2025-11-13",
                "form": "10-Q",
                "accession": "000176962825000062",
                "xml_files": [
                    {"filename": "...", "content": "...", "file_path": "..." if save else None}
                ]
            },
            ...
        ]
    """
    cik = ticker_to_cik(ticker)
    if not cik:
        print(f"Error: Ticker '{ticker}' not found in cik.json")
        return []
    
    # Get filing history
    url = f"https://data.sec.gov/submissions/CIK{cik:0>10}.json"
    data = requests.get(url, headers=HEADERS).json()
    recent = data["filings"]["recent"]
    
    # Filter by form type
    forms = recent["form"]
    accession = recent["accessionNumber"]
    docs = recent["primaryDocument"]
    dates = recent["filingDate"]
    
    history = []
    for form, acc, doc, date in zip(forms, accession, docs, dates):
        if form_type == "both" and (form == "10-Q" or form == "10-K"):
            history.append({
                "date": date,
                "accession": acc.replace("-", ""),
                "form": form
            })
        elif form_type == "10Q" and form == "10-Q":
            history.append({
                "date": date,
                "accession": acc.replace("-", ""),
                "form": form
            })
        elif form_type == "10K" and form == "10-K":
            history.append({
                "date": date,
                "accession": acc.replace("-", ""),
                "form": form
            })
    
    # Filter by time interval if provided
    if time_interval:
        start_date, end_date = time_interval
        history = [f for f in history if start_date <= f["date"] <= end_date]
    
    # Get XML files for each filing
    results = []
    for filing in history:
        acc = filing["accession"]
        xml_files = get_xml_files_for_filing(cik, acc)
        
        if xml_files:  # Only add if XML files found
            xml_downloads = []
            for xml in xml_files:
                xml_content = download_text(xml["url"], xml["filename"])
                item = {
                    "filename": xml["filename"],
                    "content": xml_content
                }
                if save:
                    path = save_text_to_file(xml_content, xml["filename"], "xml_files")
                    item["file_path"] = path
                else:
                    item["file_path"] = None
                xml_downloads.append(item)
            
            results.append({
                "date": filing["date"],
                "form": filing["form"],
                "accession": acc,
                "xml_files": xml_downloads
            })
    
    return results

