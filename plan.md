Yes, that exact mindset—treating the workspace as a highly controlled, deterministic data pipeline—is exactly how we will lock this system down. We are not building general AI chatbot prompts here. We are configuring a strict, automated Data Orchestration Machine inside your Google Antigravity IDE.
Let's rebuild it from scratch with absolute technical precision, mapping out the exact file parameters, explicit data schemas, and strict data constraints.
------------------------------
## 📁 Technical Directory Architecture
Initialize a clean project workspace in the Google Antigravity IDE and create this exact directory layout:

📁 aeo_systems_root/
│
├── 📄 project.config               <-- Runtime execution parameters
│
├── 📂 agent_hooks/
│   └── 📄 aeo_pipeline.md          <-- Deterministic processing hook
│
├── 📂 blueprints/
│   ├── 📄 llms.txt                 <-- Dense markdown directory model
│   └── 📄 corporate.jsonld         <-- Strongly typed JSON-LD schema
│
└── 📂 production_exports/          <-- Validated client delivery packages

------------------------------
## ⚙️ Runtime Environment Configuration (project.config)
Create your master configuration file at the root directory. This bridges your free-tier API endpoints and sets exact environment permissions:

{
  "antigravity_spec": "2.0.0",
  "project_profile": {
    "workspace_id": "aeo-core-systems-matrix",
    "core_engine": "Gemini-3.6-Flash",
    "permissions": ["browser_loop", "filesystem_write", "network_fetch"]
  },
  "free_tier_integrations": {
    "FIRECRAWL_API_KEY": "YOUR_FREE_FIRECRAWL_API_KEY_HERE",
    "TAVILY_API_KEY": "YOUR_FREE_TAVILY_API_KEY_HERE",
    "SERPER_API_KEY": "YOUR_FREE_SERPER_API_KEY_HERE"
  },
  "storage_routing": {
    "hooks_path": "./agent_hooks",
    "exports_path": "./production_exports"
  }
}

------------------------------
## 📜 Automated Subagent Protocol (aeo_pipeline.md)
Create this execution hook inside your /agent_hooks/ folder. This enforces strict operational constraints on how the Antigravity agent manages ingestion and formatting.

---agent_hook: aeo_pipeline
role: AEO & Semantic Systems Architect
execution_priority: absoluteunattended_routing: allowed
---# 🤖 System Execution Directives
You are the execution agent for AEO Core Systems. Your operational directive is to run an end-to-end technical diagnostic on a target company URL and compile their machine-readable index assets for human review.
## 🧭 Operational Execution Loop### Phase 1: Structured API-Driven Extraction- Initialize the Firecrawl API to run a markdown crawl of the target domain.- Strip away all raw HTML layout elements, CSS styles, UI buttons, and cookie prompts.
- Verify if the domain root folder returns a 404 error page on `://targeturl.com`.
### Phase 2: Algorithmic Gap Analysis- Query the Tavily and Serper APIs to extract the top 10 long-tail transactional intent prompts for the client's specific industry vertical.- Cross-reference the client's current site text against search-intent queries to evaluate keyword relevance, entity representation, and completeness.- Flag missing core definitions causing a live AI citation deficit.
### Phase 3: High-Density File Export- Ingest the extracted and optimized business facts directly into our blueprint layouts.- Output a finalized, machine-readable /llms.txt page using dense markdown structures (#, >, -).- Output a pristine, schema-validated JSON-LD organization block.
- Auto-save both files directly into the `./production_exports/` directory.

------------------------------
## 📊 Production Data Blueprints
Create these two standardized template sheets inside your /blueprints/ folder. Your agents will inject their parsed data directly into these structures:
## 📄 Template 1: Root Markdown Map (llms.txt)

# [Enterprise Brand Name] Information Core> High-density plain-text index optimized for LLM crawlers, automated web-scrapers, and RAG architectures.
## Core Products & Features- [Product Architecture](/features) - System parameters, feature limitations, and performance boundaries.
- [Commercial Packaging](/pricing) - Tiers, contractual boundaries, and SLA structures.
## Verification & Trust Layer- [Audited Case Studies](/case-studies) - Verbatim customer utility reports with explicit performance metrics.
## Core Frequently Asked Questions### What core problem does this platform solve?[The Antigravity subagent will autonomously inject a clean, keyword-dense solution summary block here for AI models to parse].

## 📄 Template 2: Validated JSON-LD Structural Graph (corporate.jsonld)

{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "[Client Brand Name]",
  "url": "[Client Home URL]",
  "logo": "[Client Vector Logo URL]",
  "description": "[AI-optimized brand bio description entirely free of filler words]",
  "knowsAbout": ["Enterprise Software Architecture", "Data Infrastructure", "Systems Integration"]
}

------------------------------
