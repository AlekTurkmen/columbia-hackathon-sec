# SEC Filing XML Downloader - Complete Documentation

## Overview

The `get_filing_xml.py` module provides a simple, clean interface to download SEC filing XML files (10-Q and 10-K forms) for any publicly traded company. This tool is designed for financial analysis, data extraction, and pipeline integration.

## Key Features

- **Ticker to CIK Conversion**: Automatically converts ticker symbols to SEC CIK numbers
- **Form Type Filtering**: Get 10-Q, 10-K, or both filing types
- **Time Interval Filtering**: Filter filings by date range
- **In-Memory Caching**: Efficient caching to avoid redundant downloads
- **Optional File Saving**: Save XML files to disk or keep in memory
- **Rate Limiting**: Built-in compliance with SEC's 10 requests/second limit
- **Clean API**: Simple function interface with no mocks or defaults

## Installation

### Prerequisites

- Python 3.6 or higher
- `requests` library
- `cik.json` file (ticker to CIK mapping)

### Setup

```bash
# Install dependencies
pip install requests

# Ensure cik.json is in the same directory as get_filing_xml.py
# Download from: https://www.sec.gov/files/company_tickers.json
# Rename to cik.json
```

## Function Reference

### `get_filing_xml()`

#### Signature

```python
def get_filing_xml(ticker, form_type="10Q", time_interval=None, save=False)
```

#### Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `ticker` | `str` | - | **Yes** | Company ticker symbol (e.g., "AAPL", "MSFT", "CRWV") |
| `form_type` | `str` | `"10Q"` | No | Filing type: `"10Q"`, `"10K"`, or `"both"` |
| `time_interval` | `tuple` or `None` | `None` | No | Date range `(start_date, end_date)` in "YYYY-MM-DD" format. `None` returns all filings |
| `save` | `bool` | `False` | No | If `True`, saves files to `xml_files/` directory. If `False`, only caches in memory |

#### Return Value

Returns a **list of dictionaries**, each representing a filing:

```python
[
    {
        "date": "2025-11-13",                    # Filing date (YYYY-MM-DD)
        "form": "10-Q",                          # Form type ("10-Q" or "10-K")
        "accession": "000176962825000062",       # SEC accession number
        "xml_files": [                          # List of XML files for this filing
            {
                "filename": "crwv-20250930_htm.xml",  # XML filename
                "content": "<xml>...</xml>",         # Full XML content (string)
                "file_path": None                     # File path if saved, else None
            }
        ]
    },
    ...
]
```

**Returns empty list `[]` if:**
- Ticker not found in `cik.json`
- No filings match the criteria
- No XML files found for the filings

## Usage Examples

### Basic Usage

#### Example 1: Get 10-Q XML files (cached in memory)

```python
from get_filing_xml import get_filing_xml

results = get_filing_xml("CRWV", form_type="10Q", save=False)

if results:
    print(f"Retrieved {len(results)} filings")
    for filing in results:
        print(f"{filing['date']} - {filing['form']}: {len(filing['xml_files'])} XML file(s)")
        # Access XML content
        for xml in filing['xml_files']:
            content = xml['content']  # Full XML as string
            print(f"  - {xml['filename']} ({len(content):,} chars)")
```

#### Example 2: Get 10-K XML files

```python
results = get_filing_xml("AAPL", form_type="10K", save=False)
```

#### Example 3: Get both 10-Q and 10-K filings

```python
results = get_filing_xml("MSFT", form_type="both", save=False)
```

### Advanced Usage

#### Example 4: Filter by time interval

```python
# Get 10-Q filings from 2024-01-01 to 2025-12-31
results = get_filing_xml(
    "CRWV", 
    form_type="10Q", 
    time_interval=("2024-01-01", "2025-12-31"),
    save=False
)
```

#### Example 5: Save files to disk

```python
# Downloads and saves XML files to xml_files/ directory
results = get_filing_xml("CRWV", form_type="10Q", save=True)

if results:
    for filing in results:
        for xml in filing['xml_files']:
            if xml['file_path']:
                print(f"Saved: {xml['file_path']}")
```

#### Example 6: Pipeline integration

```python
# Get XML files and process in your pipeline
results = get_filing_xml("CRWV", form_type="10Q", save=False)

# Process each filing's XML content
for filing in results:
    date = filing['date']
    form = filing['form']
    accession = filing['accession']
    
    for xml_file in filing['xml_files']:
        filename = xml_file['filename']
        xml_content = xml_file['content']  # Full XML as string
        
        # Your processing here:
        # - Parse XML with lxml, BeautifulSoup, etc.
        # - Extract financial data
        # - Store in database
        # - Feed to ML models
        # etc.
        
        print(f"Processing {filename} from {date} {form}")
        # process_xml(xml_content)
```

#### Example 7: Multiple tickers

```python
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]

all_results = {}
for ticker in tickers:
    results = get_filing_xml(ticker, form_type="both", save=False)
    all_results[ticker] = results
    print(f"{ticker}: {len(results)} filings")
```

## Technical Details

### XML File Filtering

The function only downloads files ending with `_htm.xml` (e.g., `crwv-20250930_htm.xml`). These are the main filing XML files that contain the complete XBRL (eXtensible Business Reporting Language) data.

**Files NOT downloaded:**
- `_cal.xml` (Calculation linkbase)
- `_def.xml` (Definition linkbase)
- `_lab.xml` (Label linkbase)
- `_pre.xml` (Presentation linkbase)
- `FilingSummary.xml` (Filing summary)

These files are typically not needed for most analysis tasks, as the `_htm.xml` file contains all the essential financial data.

### Caching Mechanism

- **In-Memory Cache**: Files are cached in the `HTML_CACHE` dictionary
- **Cache Key**: Uses filename as cache key
- **Cache Persistence**: Cache persists for the Python session
- **Cache Benefits**: 
  - Avoids redundant downloads
  - Faster subsequent access
  - Reduces API calls

### Rate Limiting

The function includes `time.sleep(0.1)` between requests to comply with SEC's rate limit:
- **SEC Limit**: 10 requests per second
- **Our Rate**: ~10 requests/second (0.1 second delay)
- **Compliance**: Fully compliant with SEC guidelines

### User-Agent Header

SEC requires a custom User-Agent header for programmatic access:

```python
HEADERS = {
    "User-Agent": "jf3670@columbia.edu",
    "Accept-Encoding": "gzip, deflate",
}
```

**Important**: Update the email in `get_filing_xml.py` to your own email address.

### Error Handling

- **Ticker Not Found**: Returns empty list `[]` and prints error message
- **No Filings Match**: Returns empty list `[]`
- **API Request Fails**: Raises `requests.exceptions.HTTPError`
- **Network Issues**: Raises `requests.exceptions.RequestException`

## File Structure

```
.
├── get_filing_xml.py          # Main module
├── cik.json                    # Ticker to CIK mapping (required)
├── xml_files/                  # Created when save=True
│   ├── crwv-20250930_htm.xml
│   ├── crwv-20250630_htm.xml
│   └── ...
└── README.md                   # This documentation
```

## Helper Functions

The module exports these helper functions for advanced use:

### `ticker_to_cik(ticker)`

Converts ticker symbol to CIK number.

```python
from get_filing_xml import ticker_to_cik

cik = ticker_to_cik("AAPL")  # Returns "320193"
```

### `get_xml_files_for_filing(cik, accession)`

Gets list of XML files for a specific filing.

```python
from get_filing_xml import get_xml_files_for_filing

xml_files = get_xml_files_for_filing("1769628", "000176962825000062")
# Returns: [{"filename": "...", "url": "..."}, ...]
```

### `download_text(url, cache_key)`

Downloads text file with caching.

```python
from get_filing_xml import download_text

content = download_text("https://...", "cache_key")
```

### `save_text_to_file(content, filename, output_dir)`

Saves text content to file.

```python
from get_filing_xml import save_text_to_file

path = save_text_to_file(content, "file.xml", "xml_files")
```

## Integration Examples

### With XML Parsing Libraries

```python
from get_filing_xml import get_filing_xml
from lxml import etree

results = get_filing_xml("CRWV", form_type="10Q", save=False)

for filing in results:
    for xml_file in filing['xml_files']:
        xml_content = xml_file['content']
        
        # Parse with lxml
        root = etree.fromstring(xml_content.encode('utf-8'))
        
        # Extract data
        # ...
```

### With Pandas

```python
from get_filing_xml import get_filing_xml
import pandas as pd
from lxml import etree

results = get_filing_xml("CRWV", form_type="10Q", save=False)

data = []
for filing in results:
    for xml_file in filing['xml_files']:
        root = etree.fromstring(xml_file['content'].encode('utf-8'))
        # Extract data and append to data list
        # ...

df = pd.DataFrame(data)
```

### With Database Storage

```python
from get_filing_xml import get_filing_xml
import sqlite3

results = get_filing_xml("CRWV", form_type="10Q", save=False)

conn = sqlite3.connect('filings.db')
cursor = conn.cursor()

for filing in results:
    for xml_file in filing['xml_files']:
        cursor.execute(
            "INSERT INTO filings (date, form, filename, content) VALUES (?, ?, ?, ?)",
            (filing['date'], filing['form'], xml_file['filename'], xml_file['content'])
        )

conn.commit()
```

## Troubleshooting

### No results returned?

1. **Check ticker exists**: Verify ticker is in `cik.json`
2. **Check filings exist**: Company may not have 10-Q or 10-K filings
3. **Check XML files exist**: Some older filings may not have `_htm.xml` files
4. **Check date range**: If using `time_interval`, ensure dates are correct

### Import error?

1. **Check file location**: Ensure `get_filing_xml.py` is in Python path
2. **Check dependencies**: Run `pip install requests`
3. **Check cik.json**: Ensure `cik.json` exists in same directory

### Rate limit errors?

1. **Wait and retry**: Function already includes rate limiting, but wait a few seconds
2. **Check network**: Ensure stable internet connection
3. **Check SEC status**: SEC API may be temporarily unavailable

### XML parsing errors?

1. **Check encoding**: XML files are UTF-8 encoded
2. **Check XML validity**: Some files may be malformed
3. **Use proper parser**: Use `lxml` or `xml.etree.ElementTree`

## Performance Considerations

- **Caching**: First call downloads files, subsequent calls use cache
- **Rate Limiting**: 0.1 second delay between requests (10 req/sec)
- **Memory Usage**: XML files can be large (1-5 MB each)
- **Network**: Download speed depends on internet connection

## Best Practices

1. **Use caching**: Set `save=False` for in-memory caching
2. **Filter by date**: Use `time_interval` to limit downloads
3. **Error handling**: Always check if results is empty
4. **Update User-Agent**: Use your own email in User-Agent header
5. **Batch processing**: Process multiple tickers sequentially to respect rate limits

## License

This code is provided as-is for educational and research purposes.

## References

- [SEC EDGAR API Documentation](https://www.sec.gov/edgar/sec-api-documentation)
- [XBRL Documentation](https://www.xbrl.org/)
- [SEC Company Tickers JSON](https://www.sec.gov/files/company_tickers.json)

## Support

For issues or questions, please refer to the main repository or create an issue.

