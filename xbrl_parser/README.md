# XBRL Parser & Converter

A lightweight, zero-dependency Python package for parsing XBRL XML documents and converting them into structured JSON and human-readable Markdown reports.

## Features

- **Fast Parsing**: Uses standard library `xml.etree.ElementTree`.
- **Clean Data**: Automatically strips HTML tags from text blocks.
- **Structured Output**: Produces flat JSON with resolved contexts and units.
- **LLM-Friendly**: Markdown reports are formatted as Key-Value pairs for easy ingestion by Large Language Models.

## Usage

### 1. Parse XBRL to JSON

```bash
python -m xbrl_parser.parser <input_xbrl.xml> <output.json>
```

Example:
```bash
python -m xbrl_parser.parser examples/aapl-20250628_htm.xml examples/data.json
```

### 2. Convert JSON to Markdown

```bash
python -m xbrl_parser.converter <input.json> <output.md>
```

Example:
```bash
python -m xbrl_parser.converter examples/data.json examples/report.md
```

## Output Format

The Markdown report includes:
- **Key Financial Metrics**: A summary of core GAAP indicators (Revenue, Net Income, Assets, etc.) with proper currency formatting (e.g., `$ 1,234.56`).
- **All Facts**: A comprehensive list of all data points found in the XBRL file, grouped by tag.

