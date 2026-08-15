import json
import os
import re

def validate_jsonld(filepath):
    errors = []
    if not os.path.exists(filepath):
        errors.append(f"File not found: {os.path.basename(filepath)}")
        return False, errors, {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON format in JSON-LD: {str(e)}")
        return False, errors, {}

    required_keys = ["@context", "@type", "name", "url"]
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing mandatory JSON-LD Org key: '{key}'")
        elif not data[key]:
            errors.append(f"JSON-LD Org key '{key}' is empty")

    if "@type" in data and data["@type"] != "Organization":
        errors.append(f"Invalid @type in JSON-LD. Expected 'Organization', got '{data['@type']}'")

    status = len(errors) == 0
    return status, errors, data

def validate_llmstxt(filepath):
    errors = []
    if not os.path.exists(filepath):
        errors.append(f"File not found: {os.path.basename(filepath)}")
        return False, errors, ""

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        errors.append(f"Failed to read llms.txt: {str(e)}")
        return False, errors, ""

    # Check for basic H1 title structure
    if not content.startswith("#"):
        errors.append("llms.txt must start with a level 1 heading (# Title)")
    
    # Check for required section elements
    required_sections = ["## Core Products & Features", "## Verification & Trust Layer"]
    for section in required_sections:
        if section not in content:
            errors.append(f"Missing required section header in llms.txt: '{section}'")

    status = len(errors) == 0
    return status, errors, content

def verify_traceability(jsonld_data, llms_content, raw_crawl_path):
    errors = []
    warnings = []
    if not os.path.exists(raw_crawl_path):
        warnings.append(f"Raw crawl file not found at {raw_crawl_path}. Skipping evidence traceability check.")
        return errors, warnings

    try:
        with open(raw_crawl_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        warnings.append(f"Failed to load raw crawl file for traceability checks: {str(e)}")
        return errors, warnings

    # Accumulate all readable text content from raw crawl (firecrawl & jina)
    scraped_corpus = ""
    if "firecrawl_data" in raw_data and isinstance(raw_data["firecrawl_data"], dict):
        scraped_corpus += str(raw_data["firecrawl_data"].get("data", ""))
        scraped_corpus += str(raw_data["firecrawl_data"].get("markdown", ""))
    if "jina_data" in raw_data and isinstance(raw_data["jina_data"], dict):
        jina_content = raw_data["jina_data"].get("data", {})
        if isinstance(jina_content, dict):
            scraped_corpus += str(jina_content.get("content", ""))
        else:
            scraped_corpus += str(jina_content)

    scraped_corpus_lower = scraped_corpus.lower()

    # Trace main brand name from JSON-LD
    brand_name = jsonld_data.get("name")
    if brand_name and brand_name.lower() not in scraped_corpus_lower:
        # Check if brand_name is a generic template placeholder
        if "[Client Brand Name]" not in brand_name:
            warnings.append(f"Fact Traceability Warning: Brand name '{brand_name}' not explicitly found in raw crawl corpus.")

    # Trace core products listed in llms.txt (words from bullets/links)
    # Match links like [Product Name](/features) or similar keywords
    product_mentions = re.findall(r'-\s+\[([^\]]+)\]', llms_content)
    for prod in product_mentions:
        # Skip generic blueprints placeholders
        if "Product Architecture" in prod or "Commercial Packaging" in prod or "Audited Case Studies" in prod:
            continue
        # Split words to check if key terms exist
        first_term = prod.split()[0] if prod.split() else prod
        if first_term.lower() not in scraped_corpus_lower:
            warnings.append(f"Fact Traceability Warning: Core product mention '{prod}' not explicitly verified in raw crawl text.")

    return errors, warnings

def run_validation(exports_dir, raw_crawl_path=None):
    if raw_crawl_path is None:
        raw_crawl_path = os.path.join(exports_dir, "raw_crawl.json")

    report = {
        "status": "PASS",
        "errors": [],
        "warnings": [],
        "telemetry": {
            "jsonld_valid": False,
            "llms_valid": False,
            "traceability_checked": False
        }
    }

    jsonld_path = os.path.join(exports_dir, "corporate.jsonld")
    jsonld_status, jsonld_errors, jsonld_data = validate_jsonld(jsonld_path)
    report["telemetry"]["jsonld_valid"] = jsonld_status
    report["errors"].extend(jsonld_errors)

    llms_path = os.path.join(exports_dir, "llms.txt")
    llms_status, llms_errors, llms_content = validate_llmstxt(llms_path)
    report["telemetry"]["llms_valid"] = llms_status
    report["errors"].extend(llms_errors)

    if jsonld_status and llms_status:
        trace_errors, trace_warnings = verify_traceability(jsonld_data, llms_content, raw_crawl_path)
        report["errors"].extend(trace_errors)
        report["warnings"].extend(trace_warnings)
        report["telemetry"]["traceability_checked"] = True

    if len(report["errors"]) > 0:
        report["status"] = "FAIL"

    # Save validation report file
    report_file = os.path.join(exports_dir, "validation_report.json")
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Validation report saved to {report_file}")
    except Exception as e:
        print(f"Error saving validation report file: {e}")

    return report

def main():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    # Resolve config
    config_path = os.path.join(base_dir, "project.config")
    exports_dir = os.path.join(base_dir, "production_exports")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                exports_path_rel = config.get("storage_routing", {}).get("exports_path", "./production_exports")
                exports_dir = os.path.normpath(os.path.join(base_dir, exports_path_rel))
        except:
            pass

    print(f"Starting schema and evidence validation on outputs in {exports_dir}...")
    report = run_validation(exports_dir)
    print(f"Validation Status: [{report['status']}]")
    if report["errors"]:
        print(f"Errors ({len(report['errors'])}):")
        for err in report["errors"]:
            print(f" - {err}")
    if report["warnings"]:
        print(f"Warnings ({len(report['warnings'])}):")
        for wrn in report["warnings"]:
            print(f" - {wrn}")

if __name__ == "__main__":
    main()
