# Get XML Module

This module provides a simple interface to download SEC filing XML files (10-Q and 10-K) for any ticker symbol.

## Files

- `get_filing_xml.py` - Main module with the `get_filing_xml()` function
- `get_xml_documentation.md` - Complete documentation and usage guide

## Quick Start

```python
from get_filing_xml import get_filing_xml

# Get 10-Q XML files (cached in memory)
results = get_filing_xml("CRWV", form_type="10Q", save=False)

if results:
    for filing in results:
        print(f"{filing['date']} - {filing['form']}")
        for xml in filing['xml_files']:
            print(f"  - {xml['filename']}")
            content = xml['content']  # Full XML content available here
```

## Documentation

See `get_xml_documentation.md` for complete documentation including:
- Function reference
- Usage examples
- Integration guides
- Troubleshooting

## Requirements

- Python 3.6+
- `requests` library
- `cik.json` file (ticker to CIK mapping)

## Installation

```bash
pip install requests
```

Ensure `cik.json` is in the same directory as `get_filing_xml.py`.

