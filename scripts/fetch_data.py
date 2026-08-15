import json
import urllib.request
import urllib.error
import argparse
import os
import datetime

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "project.config")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading project.config: {e}")
        return None

def post_request(url, headers, payload, timeout=20):
    if "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8')), None
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8')
            parsed_err = json.loads(err_body)
        except:
            parsed_err = None
        err_msg = f"HTTP Error {e.code}: {e.reason}"
        return {"error": err_msg, "details": parsed_err}, err_msg
    except urllib.error.URLError as e:
        err_msg = f"Network URL Error: {e.reason}"
        return {"error": err_msg}, err_msg
    except Exception as e:
        err_msg = f"Unexpected Request Exception: {str(e)}"
        return {"error": err_msg}, err_msg

def run_ingestion(target_url, industry, config):
    if not config:
        return {"error": "Invalid configuration parameters"}

    integrations = config.get("free_tier_integrations", {})
    firecrawl_key = integrations.get("FIRECRAWL_API_KEY")
    tavily_key = integrations.get("TAVILY_API_KEY")
    serper_key = integrations.get("SERPER_API_KEY")
    jina_key = integrations.get("JINA_API_KEY")

    output = {
        "target_url": target_url,
        "industry": industry,
        "telemetry": {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "primary_source": "firecrawl",
            "primary_status": "failed",
            "primary_error": None,
            "fallback_source": "jina",
            "fallback_status": "unused",
            "fallback_error": None,
            "tavily_status": "unused",
            "tavily_error": None,
            "serper_status": "unused",
            "serper_error": None
        },
        "firecrawl_data": {},
        "jina_data": {},
        "tavily_data": {},
        "serper_data": {}
    }

    # 1. Firecrawl Scrape
    firecrawl_success = False
    if firecrawl_key:
        print(f"Initiating Firecrawl scrape for {target_url}...")
        url = "https://api.firecrawl.dev/v1/scrape"
        headers = {
            "Authorization": f"Bearer {firecrawl_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": target_url,
            "formats": ["markdown"]
        }
        res, err = post_request(url, headers, payload)
        output["firecrawl_data"] = res
        if not err and "error" not in res:
            firecrawl_success = True
            output["telemetry"]["primary_status"] = "success"
            print("[SUCCESS] Firecrawl scrape completed.")
        else:
            output["telemetry"]["primary_status"] = "failed"
            output["telemetry"]["primary_error"] = err or res.get("error")
            print(f"Firecrawl scrape failed: {err or res.get('error')}")
    else:
        err_msg = "Missing FIRECRAWL_API_KEY"
        output["firecrawl_data"] = {"error": err_msg}
        output["telemetry"]["primary_error"] = err_msg
        print(f"Firecrawl scrape skipped: {err_msg}")

    # Fallback to Jina Reader if Firecrawl failed
    if not firecrawl_success:
        if jina_key:
            print(f"Attempting Jina Reader fallback scrape for {target_url}...")
            url = f"https://r.jina.ai/{target_url}"
            headers = {
                "Authorization": f"Bearer {jina_key}",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            }
            output["telemetry"]["fallback_status"] = "attempted"

            def execute_jina_request(use_auth):
                current_headers = headers.copy()
                if not use_auth:
                    current_headers.pop("Authorization", None)
                req = urllib.request.Request(
                    url,
                    headers=current_headers,
                    method='GET'
                )
                with urllib.request.urlopen(req, timeout=20) as response:
                    return json.loads(response.read().decode('utf-8'))

            try:
                jina_res = execute_jina_request(use_auth=True)
                output["jina_data"] = jina_res
                output["telemetry"]["fallback_status"] = "success"
                print("[SUCCESS] Jina Reader fallback scrape completed with credentials.")
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    print("Jina Reader key returned 403 Forbidden. Retrying anonymously...")
                    try:
                        jina_res = execute_jina_request(use_auth=False)
                        output["jina_data"] = jina_res
                        output["telemetry"]["fallback_status"] = "success_anonymous"
                        print("[SUCCESS] Jina Reader fallback scrape completed anonymously.")
                    except Exception as retry_err:
                        err_msg = f"Anonymous retry failed: {retry_err}"
                        output["jina_data"] = {"error": err_msg}
                        output["telemetry"]["fallback_status"] = "failed"
                        output["telemetry"]["fallback_error"] = err_msg
                        print(f"Jina Reader anonymous fallback failed: {retry_err}")
                else:
                    err_msg = f"HTTP Error {e.code}: {e.reason}"
                    output["jina_data"] = {"error": err_msg}
                    output["telemetry"]["fallback_status"] = "failed"
                    output["telemetry"]["fallback_error"] = err_msg
                    print(f"Jina Reader fallback failed with HTTP Error {e.code}: {e.reason}")
            except Exception as e:
                err_msg = f"Unexpected Jina exception: {str(e)}"
                output["jina_data"] = {"error": err_msg}
                output["telemetry"]["fallback_status"] = "failed"
                output["telemetry"]["fallback_error"] = err_msg
                print(f"Jina Reader fallback failed: {e}")
        else:
            err_msg = "Missing JINA_API_KEY and Firecrawl failed."
            output["jina_data"] = {"error": err_msg}
            output["telemetry"]["fallback_status"] = "skipped"
            output["telemetry"]["fallback_error"] = err_msg
            print(f"Jina Reader fallback skipped: {err_msg}")

    # 2. Tavily Search
    if tavily_key:
        query = f"top long-tail transactional intent prompts and search queries for {industry} industry"
        print(f"Initiating Tavily search for: {query}...")
        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": tavily_key,
            "query": query,
            "search_depth": "basic"
        }
        res, err = post_request(url, headers, payload)
        output["tavily_data"] = res
        if not err and "error" not in res:
            output["telemetry"]["tavily_status"] = "success"
            print("[SUCCESS] Tavily search completed.")
        else:
            output["telemetry"]["tavily_status"] = "failed"
            output["telemetry"]["tavily_error"] = err or res.get("error")
            print(f"Tavily search failed: {err or res.get('error')}")
    else:
        err_msg = "Missing TAVILY_API_KEY"
        output["tavily_data"] = {"error": err_msg}
        output["telemetry"]["tavily_status"] = "failed"
        output["telemetry"]["tavily_error"] = err_msg
        print(f"Tavily search skipped: {err_msg}")

    # 3. Serper Search
    if serper_key:
        query = f"{industry} industry transactional intent keywords gap analysis AI SEO"
        print(f"Initiating Serper search for: {query}...")
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": serper_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query}
        res, err = post_request(url, headers, payload)
        output["serper_data"] = res
        if not err and "error" not in res:
            output["telemetry"]["serper_status"] = "success"
            print("[SUCCESS] Serper search completed.")
        else:
            output["telemetry"]["serper_status"] = "failed"
            output["telemetry"]["serper_error"] = err or res.get("error")
            print(f"Serper search failed: {err or res.get('error')}")
    else:
        err_msg = "Missing SERPER_API_KEY"
        output["serper_data"] = {"error": err_msg}
        output["telemetry"]["serper_status"] = "failed"
        output["telemetry"]["serper_error"] = err_msg
        print(f"Serper search skipped: {err_msg}")

    # Save outputs to file
    exports_path = config.get("storage_routing", {}).get("exports_path", "./production_exports")
    base_dir = os.path.dirname(os.path.dirname(__file__))
    resolved_exports_path = os.path.normpath(os.path.join(base_dir, exports_path))
    os.makedirs(resolved_exports_path, exist_ok=True)

    output_file = os.path.join(resolved_exports_path, "raw_crawl.json")
    try:
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
        print(f"[SUCCESS] Ingestion data saved to {output_file}")
    except Exception as e:
        print(f"Error saving outputs: {e}")

    return output

def main():
    parser = argparse.ArgumentParser(description="Mechanical Ingestion Engine for AEO Core Systems")
    parser.add_argument("--url", default="https://example.com", help="Target URL to scrape")
    parser.add_argument("--industry", default="Technology", help="Client's industry vertical")
    args = parser.parse_args()

    config = load_config()
    if not config:
        print("Failed to run extraction: project.config not found or invalid.")
        return

    run_ingestion(args.url, args.industry, config)

if __name__ == "__main__":
    main()
