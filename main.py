import argparse
import os
import json
import urllib.parse
import re
from scripts.fetch_data import load_config, run_ingestion
from scripts.validate import run_validation

def extract_brand_details(raw_data):
    target_url = raw_data.get("target_url", "https://example.com")
    parsed_url = urllib.parse.urlparse(target_url)
    domain = parsed_url.netloc
    
    # Heuristically extract brand name from domain
    brand_name = domain.replace("www.", "").split(".")[0].capitalize()
    
    # Try to extract from scraped page title if available
    jina_title = raw_data.get("jina_data", {}).get("data", {}).get("title", "")
    if jina_title and "|" in jina_title:
        brand_name = jina_title.split("|")[0].strip()
    elif jina_title and "-" in jina_title:
        brand_name = jina_title.split("-")[0].strip()

    # Locate a potential logo URL from scraped content
    scraped_content = ""
    jina_content = raw_data.get("jina_data", {}).get("data", {})
    if isinstance(jina_content, dict):
        scraped_content = jina_content.get("content", "")
    else:
        scraped_content = str(jina_content)

    logo_url = f"{target_url}/assets/logo.svg"
    logo_matches = re.findall(r'!\[.*?\]\((.*?logo.*?)\)', scraped_content, re.IGNORECASE)
    if logo_matches:
        logo_url = logo_matches[0]
        if logo_url.startswith("/"):
            logo_url = urllib.parse.urljoin(target_url, logo_url)

    # Heuristically extract first few sentences for description
    description = f"{brand_name} is a leading organization in the {raw_data.get('industry', 'technology')} industry."
    sentences = re.split(r'\.\s+', scraped_content)
    cleaned_sentences = []
    for s in sentences:
        s_clean = s.strip().replace("\n", " ")
        if s_clean and len(s_clean) > 20 and not s_clean.startswith("#") and not s_clean.startswith("!"):
            cleaned_sentences.append(s_clean)
        if len(cleaned_sentences) >= 2:
            break
    if cleaned_sentences:
        description = ". ".join(cleaned_sentences) + "."
        if len(description) > 250:
            description = description[:247] + "..."

    # Heuristically extract products or features from bullet lists
    detected_products = []
    bullets = re.findall(r'-\s+\[?([A-Z][a-zA-Z\s]+)\]?', scraped_content)
    for b in bullets:
        b_clean = b.strip()
        if len(b_clean) > 3 and len(b_clean) < 30 and not any(kw in b_clean.lower() for kw in ["contact", "terms", "privacy", "home", "about", "careers", "pricing", "sign up", "login"]):
            detected_products.append(b_clean)
    
    # Deduplicate products
    seen = set()
    deduped_products = []
    for p in detected_products:
        p_lower = p.lower()
        if p_lower not in seen:
            seen.add(p_lower)
            deduped_products.append(p)
    
    if not deduped_products:
        deduped_products = ["Core Platform Features", "Commercial Solutions", "Enterprise Integrations"]

    return {
        "name": brand_name,
        "url": target_url,
        "logo": logo_url,
        "description": description,
        "products": deduped_products[:5]
    }

def generate_outputs(details, blueprints_dir, exports_dir):
    # Load Blueprints
    llms_blueprint_path = os.path.join(blueprints_dir, "llms.txt")
    jsonld_blueprint_path = os.path.join(blueprints_dir, "corporate.jsonld")

    # 1. Synthesize llms.txt
    llms_content = ""
    if os.path.exists(llms_blueprint_path):
        with open(llms_blueprint_path, "r", encoding="utf-8") as f:
            llms_content = f.read()
        
        # Replace template placeholders
        llms_content = llms_content.replace("[Enterprise Brand Name]", details["name"])
        product_bullets = ""
        for prod in details["products"]:
            product_bullets += f"- [{prod}](/features) - Core feature offering supporting operational leverage.\n"
        
        llms_content = llms_content.replace("- [Product Architecture](/features) - System parameters, feature limitations, and performance boundaries.", product_bullets.strip())
        llms_content = llms_content.replace("[The Antigravity subagent will autonomously inject a clean, keyword-dense solution summary block here for AI models to parse].", details["description"])
    else:
        # Fallback manual synthesis
        llms_content = f"# {details['name']} Information Core\n\n> High-density plain-text index optimized for LLM crawlers.\n\n## Core Products & Features\n"
        for prod in details["products"]:
            llms_content += f"- [{prod}](/features) - Core feature offering.\n"
        llms_content += f"\n## Verification & Trust Layer\n- [Audited Case Studies](/case-studies)\n\n## Core Frequently Asked Questions\n### What core problem does this platform solve?\n{details['description']}\n"

    # Save llms.txt
    llms_out_path = os.path.join(exports_dir, "llms.txt")
    with open(llms_out_path, "w", encoding="utf-8") as f:
        f.write(llms_content)
    print(f"Synthesized llms.txt saved to {llms_out_path}")

    # 2. Synthesize JSON-LD
    jsonld_data = {}
    if os.path.exists(jsonld_blueprint_path):
        with open(jsonld_blueprint_path, "r", encoding="utf-8") as f:
            jsonld_data = json.load(f)
        
        jsonld_data["name"] = details["name"]
        jsonld_data["url"] = details["url"]
        jsonld_data["logo"] = details["logo"]
        jsonld_data["description"] = details["description"]
        jsonld_data["knowsAbout"] = ["Digital Workflows", "API Systems Integration", f"{details['name']} Features"]
    else:
        jsonld_data = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": details["name"],
            "url": details["url"],
            "logo": details["logo"],
            "description": details["description"]
        }

    # Save corporate.jsonld
    jsonld_out_path = os.path.join(exports_dir, "corporate.jsonld")
    with open(jsonld_out_path, "w", encoding="utf-8") as f:
        json.dump(jsonld_data, f, indent=2)
    print(f"Synthesized corporate.jsonld saved to {jsonld_out_path}")

def run_pipeline(url, industry, mock_mode=False):
    base_dir = os.path.dirname(__file__)
    config = load_config()
    if not config:
        print("[ERROR] project.config not found. Initializing with default config parameters.")
        config = {
            "storage_routing": {
                "hooks_path": "./agent_hooks",
                "exports_path": "./production_exports"
            }
        }

    blueprints_dir = os.path.join(base_dir, "blueprints")
    exports_dir = os.path.normpath(os.path.join(base_dir, config.get("storage_routing", {}).get("exports_path", "./production_exports")))
    os.makedirs(exports_dir, exist_ok=True)

    print(f"=== Starting AEO Core Systems Pipeline ===")
    print(f"Target URL: {url}")
    print(f"Industry: {industry}")
    print(f"Mock Mode: {mock_mode}")

    raw_crawl_path = os.path.join(exports_dir, "raw_crawl.json")

    # 1. Ingestion Phase
    if mock_mode:
        print("Using local mock crawler state...")
        # Create a mock raw_crawl file if it doesn't exist
        mock_raw_crawl = {
            "target_url": url,
            "industry": industry,
            "telemetry": {
                "timestamp": "2026-08-15T12:00:00Z",
                "primary_source": "firecrawl",
                "primary_status": "failed",
                "primary_error": "API Key Missing",
                "fallback_source": "jina",
                "fallback_status": "success_mock",
                "fallback_error": None
            },
            "jina_data": {
                "data": {
                    "title": f"{industry} Platforms | The Premier Infrastructure Solution",
                    "content": f"Welcome to the {industry} main site. We deliver reliable integrations and services. Our key solutions include Payment Processing, Risk Management, Billing Subscriptions, and Terminal hardware. We provide world-class financial APIs and data infrastructure."
                }
            }
        }
        with open(raw_crawl_path, "w", encoding="utf-8") as f:
            json.dump(mock_raw_crawl, f, indent=2)
        raw_data = mock_raw_crawl
    else:
        raw_data = run_ingestion(url, industry, config)

    # 2. Heuristic Fact Extraction & Synthesis Phase
    print("Running baseline semantic facts synthesizer...")
    details = extract_brand_details(raw_data)
    print(f"Extracted Brand Details: {json.dumps(details, indent=2)}")

    generate_outputs(details, blueprints_dir, exports_dir)

    # 3. Validation Phase
    print("Executing Validation Gate...")
    validation_report = run_validation(exports_dir, raw_crawl_path)
    print(f"=== Pipeline Validation Result: [{validation_report['status']}] ===")
    if validation_report["errors"]:
        for err in validation_report["errors"]:
            print(f" - Error: {err}")
    if validation_report["warnings"]:
        for wrn in validation_report["warnings"]:
            print(f" - Warning: {wrn}")

    return validation_report

def main():
    parser = argparse.ArgumentParser(description="AEO Core Systems Master Pipeline Entrypoint")
    parser.add_argument("--url", default="https://example.com", help="Target URL to scrape")
    parser.add_argument("--industry", default="Technology", help="Client's industry vertical")
    parser.add_argument("--mock", action="store_true", help="Execute with simulated offline mock data")
    args = parser.parse_args()

    run_pipeline(args.url, args.industry, mock_mode=args.mock)

if __name__ == "__main__":
    main()
