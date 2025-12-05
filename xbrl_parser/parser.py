import xml.etree.ElementTree as ET
import json
import sys
import re

def parse_xbrl(xml_file):
    """
    Parse an XBRL XML file and extract contexts, units, and facts.
    
    Args:
        xml_file (str): Path to the XBRL XML file.
        
    Returns:
        dict: A dictionary containing document_type, contexts, units, and facts.
    """
    # Parse with iterator to get namespaces if needed, but ElementTree handles standard parsing well enough
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML: {e}")
    
    contexts = {}
    units = {}
    facts = []

    # Iterate direct children of root
    for child in root:
        tag = child.tag
        # tag is like '{http://www.xbrl.org/2003/instance}context'
        
        # Helper to extract local name
        local_name = tag.split('}')[-1] if '}' in tag else tag
        
        if local_name == 'context':
            ctx_id = child.get('id')
            ctx_data = {}
            
            # Parse period
            for node in child.iter():
                node_local = node.tag.split('}')[-1]
                if node_local in ['startDate', 'endDate', 'instant']:
                    ctx_data[node_local] = node.text
            
            # Parse dimensions (segment)
            dims = {}
            # Search specifically for explicitMember
            for node in child.iter():
                node_local = node.tag.split('}')[-1]
                if node_local == 'explicitMember':
                    dim_name = node.get('dimension')
                    if dim_name:
                        dims[dim_name] = node.text
            
            if dims:
                ctx_data['dimensions'] = dims
                
            contexts[ctx_id] = ctx_data
            
        elif local_name == 'unit':
            unit_id = child.get('id')
            # Simplified unit parsing
            measure = None
            for node in child.iter():
                node_local = node.tag.split('}')[-1]
                if node_local == 'measure':
                    measure = node.text
                    break
            if measure:
                units[unit_id] = measure
        
        elif local_name in ['schemaRef', 'linkbaseRef', 'roleRef', 'arcroleRef']:
            continue
            
        else:
            # This is likely a Fact (Concept)
            # e.g. us-gaap:Assets
            
            context_ref = child.get('contextRef')
            if not context_ref:
                continue # Not a fact if it doesn't have contextRef
            
            # Try to reconstruct prefix:name
            ns_uri = tag.split('}')[0][1:] if '}' in tag else ""
            
            prefix = "unknown"
            if "us-gaap" in ns_uri: prefix = "us-gaap"
            elif "dei" in ns_uri: prefix = "dei"
            elif "sec.gov" in ns_uri: prefix = "sec"
            elif "fasb" in ns_uri: prefix = "fasb"
            elif "apple" in ns_uri or "aapl" in ns_uri: prefix = "aapl"
            
            friendly_tag = f"{prefix}:{local_name}"
            
            # Handle text content safely, collapsing whitespace
            # .itertext() extracts all text recursively, ignoring tags
            raw_text = "".join(child.itertext())
            clean_value = " ".join(raw_text.split())
            
            fact = {
                "tag": friendly_tag,
                "raw_tag": tag,
                "value": clean_value,
                "contextRef": context_ref,
                "unitRef": child.get('unitRef'),
                "decimals": child.get('decimals')
            }
            facts.append(fact)

    # Assemble result
    final_result = {
        "document_type": "XBRL XML",
        "contexts": contexts,
        "units": units,
        "facts": []
    }
    
    # Denormalize for easier JSON reading
    for f in facts:
        enriched = f.copy()
        if f['contextRef'] in contexts:
            enriched['period'] = contexts[f['contextRef']]
        if f['unitRef'] in units:
            enriched['unit'] = units[f['unitRef']]
        
        final_result['facts'].append(enriched)
        
    return final_result

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m xbrl_parser.parser <xml_file> <output_json>")
        sys.exit(1)
        
    xml_file = sys.argv[1]
    out_file = sys.argv[2]
    
    try:
        data = parse_xbrl(xml_file)
        with open(out_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully converted {xml_file} to {out_file}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

