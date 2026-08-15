import unittest
from unittest.mock import patch, MagicMock
import json
import os
import shutil
import tempfile
from scripts.fetch_data import run_ingestion
from scripts.validate import validate_jsonld, validate_llmstxt, verify_traceability, run_validation
from main import run_pipeline

class TestAEOPipeline(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for output exports
        self.test_dir = tempfile.mkdtemp()
        self.config = {
            "free_tier_integrations": {
                "FIRECRAWL_API_KEY": "fake_firecrawl",
                "TAVILY_API_KEY": "fake_tavily",
                "SERPER_API_KEY": "fake_serper",
                "JINA_API_KEY": "fake_jina"
            },
            "storage_routing": {
                "exports_path": self.test_dir
            }
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('scripts.fetch_data.post_request')
    def test_ingestion_success(self, mock_post):
        # Mock successful API responses
        mock_post.return_value = ({"success": True, "data": {"markdown": "# Test Domain"}}, None)
        
        result = run_ingestion("https://test.com", "Fintech", self.config)
        
        self.assertEqual(result["target_url"], "https://test.com")
        self.assertEqual(result["telemetry"]["primary_status"], "success")
        self.assertEqual(result["telemetry"]["fallback_status"], "unused")

    @patch('scripts.fetch_data.post_request')
    @patch('urllib.request.urlopen')
    def test_ingestion_fallback_routing(self, mock_urlopen, mock_post):
        # 1. Firecrawl fails (HTTP 403)
        mock_post.return_value = ({"error": "Unauthorized"}, "HTTP Error 403: Forbidden")
        
        # 2. Jina Reader succeeds
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "code": 200,
            "data": {
                "title": "Fallback Title",
                "content": "Fallback Content Bullet Points"
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = run_ingestion("https://test.com", "Fintech", self.config)
        
        self.assertEqual(result["telemetry"]["primary_status"], "failed")
        self.assertEqual(result["telemetry"]["fallback_status"], "success")
        self.assertIn("jina_data", result)
        self.assertEqual(result["jina_data"]["data"]["title"], "Fallback Title")

    def test_jsonld_validation(self):
        # Test 1: Empty file
        fake_jsonld_path = os.path.join(self.test_dir, "corporate.jsonld")
        status, errors, data = validate_jsonld(fake_jsonld_path)
        self.assertFalse(status)
        self.assertIn("File not found", errors[0])

        # Test 2: Invalid JSON syntax
        with open(fake_jsonld_path, "w") as f:
            f.write("{ invalid json")
        status, errors, data = validate_jsonld(fake_jsonld_path)
        self.assertFalse(status)
        self.assertIn("Invalid JSON format", errors[0])

        # Test 3: Missing required key
        bad_jsonld = {"@context": "https://schema.org", "@type": "Organization"}
        with open(fake_jsonld_path, "w") as f:
            json.dump(bad_jsonld, f)
        status, errors, data = validate_jsonld(fake_jsonld_path)
        self.assertFalse(status)
        self.assertTrue(any("Missing mandatory" in err for err in errors))

        # Test 4: Fully Valid Schema
        valid_jsonld = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Verified Brand",
            "url": "https://verified.com"
        }
        with open(fake_jsonld_path, "w") as f:
            json.dump(valid_jsonld, f)
        status, errors, data = validate_jsonld(fake_jsonld_path)
        self.assertTrue(status)
        self.assertEqual(len(errors), 0)

    def test_llmstxt_validation(self):
        fake_llms_path = os.path.join(self.test_dir, "llms.txt")

        # Test 1: Missing section
        bad_llms = "# Brand Core\n\nSome text here without headers."
        with open(fake_llms_path, "w") as f:
            f.write(bad_llms)
        status, errors, content = validate_llmstxt(fake_llms_path)
        self.assertFalse(status)
        self.assertTrue(any("Missing required section header" in err for err in errors))

        # Test 2: Valid
        valid_llms = "# Brand Core\n\n## Core Products & Features\n- Bullet\n## Verification & Trust Layer\n- Bullet"
        with open(fake_llms_path, "w") as f:
            f.write(valid_llms)
        status, errors, content = validate_llmstxt(fake_llms_path)
        self.assertTrue(status)

    def test_evidence_traceability_check(self):
        # 1. Setup outputs
        jsonld_data = {"name": "Test Brand", "url": "https://testbrand.com"}
        llms_content = "# Test Brand\n- [Test Brand Feature](/features)\n## Core Products & Features\n## Verification & Trust Layer"
        
        # 2. Setup raw_crawl without Brand name (should warn)
        raw_crawl_path = os.path.join(self.test_dir, "raw_crawl.json")
        raw_crawl_data = {
            "jina_data": {
                "data": {
                    "content": "Welcome to our page. We build general software integrations."
                }
            }
        }
        with open(raw_crawl_path, "w") as f:
            json.dump(raw_crawl_data, f)

        errors, warnings = verify_traceability(jsonld_data, llms_content, raw_crawl_path)
        self.assertEqual(len(errors), 0)
        self.assertTrue(any("Fact Traceability Warning" in w for w in warnings))

        # 3. Setup raw_crawl WITH Brand name (should not warn about brand name)
        raw_crawl_data["jina_data"]["data"]["content"] += " Test Brand details here."
        with open(raw_crawl_path, "w") as f:
            json.dump(raw_crawl_data, f)
        
        errors, warnings = verify_traceability(jsonld_data, llms_content, raw_crawl_path)
        # Verify brand name warning is gone
        brand_warning_present = any("Brand name 'Test Brand'" in w for w in warnings)
        self.assertFalse(brand_warning_present)

    @patch('main.load_config')
    def test_end_to_end_mock_pipeline(self, mock_load):
        mock_load.return_value = self.config
        
        # Create dummy blueprints inside the temporary test folder mock layout
        # main.py defaults to checking ./blueprints/ relative to main.py, but we mock configuration path.
        # We run pipeline in mock_mode which simulates jina response and synthesizes files in test_dir
        report = run_pipeline("https://mockurl.com", "Education", mock_mode=True)
        
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "llms.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "corporate.jsonld")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "validation_report.json")))

if __name__ == "__main__":
    unittest.main()
