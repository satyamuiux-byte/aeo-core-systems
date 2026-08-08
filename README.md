# AEO Core Systems: Automated Data Orchestration Machine

A deterministic, machine-readable AI Engine Optimization (AEO) extraction, crawl, and schema synthesis system built to run inside the Google Antigravity IDE workspace.

This system follows the strict **80/15/5 rule** of No-Code Agentic Systems:
- **80% Markdown (Rules & Logic):** Instructions and processing loops are defined in plain-English schemas (`agent_hooks/aeo_pipeline.md`).
- **15% JSON (Data Storage):** Environment profiles, storage routing, and search parameters are stored in structured JSON structures (`project.config`).
- **5% Mechanical Arms (Tools):** API fetch actions are executed by a lightweight, zero-decision Python scraper (`scripts/fetch_data.py`).

---

## 📁 Workspace Directory Layout

```text
📁 aeo_systems_root/
│
├── 📄 project.config               <-- Master configuration and API integrations
├── 📄 README.md                    <-- Operations manual
│
├── 📂 agent_hooks/
│   └── 📄 aeo_pipeline.md          <-- Processing directive loop and constraints
│
├── 📂 blueprints/
│   ├── 📄 llms.txt                 <-- Structural map for RAG and AI search crawlers
│   └── 📄 corporate.jsonld         <-- JSON-LD organization blueprint template
│
├── 📂 scripts/
│   └── 📄 fetch_data.py            <-- Mechanical ingestion script (urllib)
│
└── 📂 production_exports/          <-- Pipeline outputs and generated assets
    ├── 📄 raw_crawl.json           <-- Scraped website content and search intent gaps
    ├── 📄 llms.txt                 <-- Generated high-density index mapping
    └── 📄 corporate.jsonld         <-- Generated schema-validated graph
```

---

## ⚙️ Configuration (`project.config`)

Configure your API integrations and storage boundaries at the root level:

```json
{
  "antigravity_spec": "2.0.0",
  "project_profile": {
    "workspace_id": "aeo-core-systems-matrix",
    "core_engine": "Gemini-3.6-Flash",
    "permissions": ["browser_loop", "filesystem_write", "network_fetch"]
  },
  "free_tier_integrations": {
    "FIRECRAWL_API_KEY": "fc-your-api-key",
    "TAVILY_API_KEY": "tvly-your-api-key",
    "SERPER_API_KEY": "serper-your-api-key",
    "JINA_API_KEY": "jina-your-api-key"
  },
  "storage_routing": {
    "hooks_path": "./agent_hooks",
    "exports_path": "./production_exports"
  }
}
```

---

## 🚀 Execution Guide

### 1. Ingestion (Mechanical Arm)
To scrape a target URL and query relevant search intents, run the mechanical ingestion script using Python 3:

```powershell
python scripts/fetch_data.py --url <TARGET_URL> --industry "<INDUSTRY>"
```

#### Options:
- `--url`: The website address to extract (default: `https://example.com`).
- `--industry`: The industry vertical for transactional query generation (default: `Technology`).

**Example:**
```powershell
python scripts/fetch_data.py --url https://stripe.com --industry "SaaS"
```

#### Scraper Fallback Architecture (Self-Healing):
1. **Primary Scraper:** The script connects to the Firecrawl API (`https://api.firecrawl.dev/v1/scrape`).
2. **Secondary Scraper (Fallback):** If the Firecrawl API key is unauthorized, rate-limited, or blocked, the script automatically catches the exception and falls back to **Jina Reader** (`https://r.jina.ai/`).
3. **Third-Tier Scraper (Anonymous Fallback):** If Jina Reader returns a credential authorization error, the script retries anonymously using free-tier rates.

The raw results are saved to `production_exports/raw_crawl.json`.

---

## 🤖 Processing Loop (Agent-Driven)

Once the raw data is saved:
1. **Fact Extraction:** The AI agent reads the raw results inside `production_exports/raw_crawl.json`.
2. **Gap Analysis:** The agent cross-references the extracted site text against target industry transactional intents and keyword density structures (Princeton KDD guidelines).
3. **Blueprint Mapping:** The agent populates:
   - `production_exports/llms.txt`: A dense markdown RAG map mapping key products, pricing tiers, and trust layers.
   - `production_exports/corporate.jsonld`: A fully formatted, schema-compliant JSON-LD Graph for Google/Bing crawlers.
