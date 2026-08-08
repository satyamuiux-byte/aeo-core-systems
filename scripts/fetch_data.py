import json
import urllib.request
import urllib.error
import argparse
import os

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "project.config")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading project.config: {e}")
        return None

def post_request(url, headers, payload):
    if "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8')
            return {"error": f"HTTP Error {e.code}: {e.reason}", "details": json.loads(err_body)}
        except:
            return {"error": f"HTTP Error {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Mechanical Extraction Arm for AEO Core Systems")
    parser.add_argument("--url", default="https://example.com", help="Target URL to scrape")
    parser.add_argument("--industry", default="Technology", help="Client's industry vertical")
    args = parser.parse_args()

    config = load_config()
    if not config:
        print("Failed to run extraction: project.config not found or invalid.")
        return

    integrations = config.get("free_tier_integrations", {})
    firecrawl_key = integrations.get("FIRECRAWL_API_KEY")
    tavily_key = integrations.get("TAVILY_API_KEY")
    serper_key = integrations.get("SERPER_API_KEY")

    output = {
        "target_url": args.url,
        "industry": args.industry,
        "firecrawl_data": {},
        "tavily_data": {},
        "serper_data": {}
    }

    # 1. Firecrawl Scrape
    firecrawl_success = False
    if firecrawl_key:
        print(f"Initiating Firecrawl scrape for {args.url}...")
        url = "https://api.firecrawl.dev/v1/scrape"
        headers = {
            "Authorization": f"Bearer {firecrawl_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": args.url,
            "formats": ["markdown"]
        }
        res = post_request(url, headers, payload)
        output["firecrawl_data"] = res
        if "error" not in res:
            firecrawl_success = True
        else:
            print(f"Firecrawl scrape failed: {res.get('error')}. Detail: {res.get('details')}")
    else:
        output["firecrawl_data"] = {"error": "Missing FIRECRAWL_API_KEY"}

    # Fallback to Jina Reader if Firecrawl failed or is not available
    jina_key = integrations.get("JINA_API_KEY")
    if not firecrawl_success and jina_key:
        print(f"Attempting Jina Reader fallback scrape for {args.url}...")
        url = f"https://r.jina.ai/{args.url}"
        headers = {
            "Authorization": f"Bearer {jina_key}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        
        def execute_jina_request(use_auth):
            current_headers = headers.copy()
            if not use_auth:
                current_headers.pop("Authorization", None)
            req = urllib.request.Request(
                url,
                headers=current_headers,
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        
        try:
            output["jina_data"] = execute_jina_request(use_auth=True)
            print("[SUCCESS] Jina Reader fallback scrape completed with credentials.")
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print("Jina Reader key returned 403 Forbidden. Retrying anonymously...")
                try:
                    output["jina_data"] = execute_jina_request(use_auth=False)
                    print("[SUCCESS] Jina Reader fallback scrape completed anonymously.")
                except Exception as retry_err:
                    output["jina_data"] = {"error": f"Anonymous retry failed: {retry_err}"}
                    print(f"Jina Reader anonymous fallback failed: {retry_err}")
            else:
                output["jina_data"] = {"error": f"HTTP Error {e.code}: {e.reason}"}
                print(f"Jina Reader fallback failed with HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            output["jina_data"] = {"error": str(e)}
            print(f"Jina Reader fallback failed: {e}")


    # 2. Tavily Search
    if tavily_key:
        query = f"top long-tail transactional intent prompts and search queries for {args.industry} industry"
        print(f"Initiating Tavily search for: {query}...")
        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": tavily_key,
            "query": query,
            "search_depth": "basic"
        }
        output["tavily_data"] = post_request(url, headers, payload)
    else:
        output["tavily_data"] = {"error": "Missing TAVILY_API_KEY"}

    # 3. Serper Search
    if serper_key:
        query = f"{args.industry} industry transactional intent keywords gap analysis AI SEO"
        print(f"Initiating Serper search for: {query}...")
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": serper_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query}
        output["serper_data"] = post_request(url, headers, payload)
    else:
        output["serper_data"] = {"error": "Missing SERPER_API_KEY"}

    # Save outputs
    exports_path = config.get("storage_routing", {}).get("exports_path", "./production_exports")
    # Resolve relative path based on workspace root (parent of scripts directory)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    resolved_exports_path = os.path.normpath(os.path.join(base_dir, exports_path))
    os.makedirs(resolved_exports_path, exist_ok=True)

    output_file = os.path.join(resolved_exports_path, "raw_crawl.json")
    try:
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
        print(f"[SUCCESS] Data saved to {output_file}")
    except Exception as e:
        print(f"Error saving outputs: {e}")

if __name__ == "__main__":
    main()
