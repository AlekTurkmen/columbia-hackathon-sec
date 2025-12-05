import json
import sys
from collections import defaultdict
import re

def clean_html(raw_html):
    """Remove HTML tags and collapse whitespace."""
    if not isinstance(raw_html, str) or '<' not in raw_html:
        return raw_html
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', raw_html)
    return ' '.join(cleantext.split())

def format_currency(value, unit=None):
    """
    Format a numeric value as currency string if applicable.
    
    Args:
        value: The numeric value (string or float).
        unit: The unit string (e.g., 'iso4217:USD').
        
    Returns:
        str: Formatted string (e.g., '$ 1,234.56').
    """
    # Try to clean if it's a string with HTML
    if isinstance(value, str):
        value = clean_html(value)
        
    try:
        val = float(value)
        formatted_val = f"{val:,.2f}"
        
        # Handle USD special case
        if unit == 'iso4217:USD':
            return f"$ {formatted_val}"
        elif unit:
            return f"{formatted_val} {unit}"
        else:
            return formatted_val
    except:
        if unit:
            return f"{value} {unit}"
        return value

def json_to_markdown(json_file, output_file):
    """
    Convert an XBRL JSON dump to a Markdown report.
    
    Args:
        json_file (str): Path to input JSON file.
        output_file (str): Path to output Markdown file.
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        sys.exit(1)
    
    markdown_lines = []
    markdown_lines.append(f"# Financial Report (from XBRL)")
    markdown_lines.append(f"**Source Data:** `{json_file}`")
    markdown_lines.append(f"**Document Type:** {data.get('document_type', 'Unknown')}")
    markdown_lines.append("")
    
    # Group facts by tag to see history/dimensions
    facts_by_tag = defaultdict(list)
    if 'facts' in data:
        for fact in data['facts']:
            if 'tag' in fact:
                facts_by_tag[fact['tag']].append(fact)
    
    # 1. Key Metrics Overview (Filtering for common tags)
    key_metrics = [
        "us-gaap:Revenues",
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap:NetIncomeLoss",
        "us-gaap:ProfitLoss",
        "us-gaap:EarningsPerShareBasic",
        "us-gaap:Assets",
        "us-gaap:AssetsCurrent",
        "us-gaap:Liabilities",
        "us-gaap:LiabilitiesCurrent",
        "us-gaap:StockholdersEquity",
        "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        "us-gaap:OperatingIncomeLoss"
    ]
    
    markdown_lines.append("## Key Financial Metrics")
    markdown_lines.append("Selected high-level indicators from the report.")
    markdown_lines.append("")
    
    found_metrics = False
    for tag in key_metrics:
        if tag in facts_by_tag:
            found_metrics = True
            metrics = facts_by_tag[tag]
            # Sort helper: prioritize end date, then instant
            metrics.sort(key=lambda x: x.get('period', {}).get('endDate', x.get('period', {}).get('instant', '')), reverse=True)
            
            # Take top 5 most recent/relevant entries
            primary_metrics = [m for m in metrics if 'dimensions' not in m.get('period', {})]
            secondary_metrics = [m for m in metrics if 'dimensions' in m.get('period', {})]
            
            display_metrics = (primary_metrics + secondary_metrics)[:5]
            
            for m in display_metrics:
                unit = m.get('unit', '')
                val = format_currency(m['value'], unit)
                
                period_str = "Unknown"
                if 'period' in m:
                    p = m['period']
                    if 'startDate' in p and 'endDate' in p:
                        period_str = f"{p['startDate']} to {p['endDate']}"
                    elif 'instant' in p:
                        period_str = f"As of {p['instant']}"
                
                dims = ""
                if 'period' in m and 'dimensions' in m['period']:
                    dim_list = [f"{v.split(':')[-1]}" for k, v in m['period']['dimensions'].items()]
                    dims = f" ({', '.join(dim_list)})"
                
                display_name = tag.split(':')[-1]
                
                markdown_lines.append(f"- **{display_name}**: {val} ({period_str}){dims}")

    if not found_metrics:
        markdown_lines.append("- No key metrics found in this file.")

    markdown_lines.append("")
    
    # 2. All Data by Tag
    markdown_lines.append("## All Financial Facts")
    markdown_lines.append(f"Total facts found: {sum(len(v) for v in facts_by_tag.values())}")
    markdown_lines.append("")
    
    sorted_tags = sorted(facts_by_tag.keys())
    
    for tag in sorted_tags:
        facts = facts_by_tag[tag]
        display_name = tag
        
        markdown_lines.append(f"### {display_name}")
        
        facts.sort(key=lambda x: x.get('period', {}).get('endDate', x.get('period', {}).get('instant', '')), reverse=True)
        
        for f in facts:
            unit = f.get('unit', '')
            val = format_currency(f['value'], unit)
            
            period_str = "-"
            if 'period' in f:
                p = f['period']
                if 'startDate' in p and 'endDate' in p:
                    period_str = f"{p['startDate']} to {p['endDate']}"
                elif 'instant' in p:
                    period_str = f"As of {p['instant']}"
            
            dims = ""
            if 'period' in f and 'dimensions' in f['period']:
                dim_list = [f"{k.split(':')[-1]}: {v.split(':')[-1]}" for k, v in f['period']['dimensions'].items()]
                dims = f"  \n  *Dimensions: {', '.join(dim_list)}*"
            
            markdown_lines.append(f"- **{val}** ({period_str}){dims}")
        
        markdown_lines.append("")

    try:
        with open(output_file, 'w') as f:
            f.write("\n".join(markdown_lines))
        print(f"Successfully generated Markdown report: {output_file}")
    except Exception as e:
        print(f"Error writing Markdown file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m xbrl_parser.converter <input_json> <output_markdown>")
        sys.exit(1)
    
    json_to_markdown(sys.argv[1], sys.argv[2])

