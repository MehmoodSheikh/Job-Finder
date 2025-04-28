# 📄 Tests Module - Job Finder

This folder contains **unit tests**, **integration tests**, and **mock data** to ensure the reliability, correctness, and production-format alignment of the Job Finder API.

---

## 📂 Files and Explanation

| File Name | Purpose |
|:---|:---|
| **test_api.py** | Full **integration test** for the entire API pipeline — from search input to AI filtering output, formatted exactly like production API responses. |
| **test_scraper.py** | Tests the scraping modules independently for all platforms (LinkedIn, Indeed, Rozee.pk, etc.) and validates their outputs against the production API format. |
| **test_ai_filtering.py** | Focuses specifically on **unit testing** the AI relevance filtering service using mock jobs and sample requests. |
| **simple_test.py** | Basic sanity test to quickly validate that scraping, filtering, and formatting pipelines are working with minimal setup. |
| **api_test_results.json** | Saved JSON output of `test_api.py` matching the production API format (useful for validation or front-end testing). |
| **scraper_test_results.json** | Saved JSON output of `test_scraper.py`, showing the results of scraping jobs without AI filtering. |
| **ai_filtering_test_results.json** | Saved JSON output from `test_ai_filtering.py`, showing relevance scoring for different jobs. |
| **simple_test_results.json** | Output file containing results of the `simple_test.py`. Helps ensure minimal tests pass after major changes. |

---

## ⚙️ Logic & Implementation Details

### 1. **Integration Test (`test_api.py`)**
- **Simulates** a full request to the production API.
- Initializes the **SearchService** to scrape jobs.
- If no jobs found → **injects mock jobs** to avoid breaking the pipeline.
- Passes results to the **AIRelevanceFilteringService**.
- Saves final API output in exact structure (important for front-end or API testing).

### 2. **Scraper Testing (`test_scraper.py`)**
- Initializes **all available scrapers** dynamically via `ScraperFactory`.
- Fetches jobs **individually** using the same inputs as production (e.g., "Full Stack Engineer" in "Pakistan").
- Catches individual scraper failures and continues others (no test crash).
- Ensures that even if one scraper fails (e.g., LinkedIn bans, 403 errors), others still work.
- Formats all scraper results to match production API output (critical for uniformity).

### 3. **AI Relevance Testing (`test_ai_filtering.py`)**
- Loads a set of **mock jobs** manually.
- Applies **AI scoring** to jobs based on a **mock JobRequest**.
- Verifies if scores and final filtering are logically correct (jobs matching skills/experience/nature).

### 4. **Simple Sanity Test (`simple_test.py`)**
- Quick basic script:
  - Fetch sample jobs.
  - Pass through AI filtering.
  - Save results.
- Useful for **smoke tests** after major refactors.

---

## 🛠️ Technologies Used
- **Python 3.11**
- **FastAPI** (for core API)
- **Pydantic** (models for Job and JobRequest)
- **LangChain** + **Google Gemini API** (for AI relevance filtering)
- **asyncio** (for asynchronous scraping and filtering)
- **httpx** (for async web requests)

---

## 📸 Example Outputs
- ✅ **`api_test_results.json`** — Full API production-like output with jobs and relevance scores.
- ✅ **`scraper_test_results.json`** — Scraped jobs without AI filtering.
- ✅ **`ai_filtering_test_results.json`** — Only AI scoring results for mock jobs.
- ✅ **`simple_test_results.json`** — Minimal end-to-end pipeline output.

---

## 📑 How to Run the Tests

```bash
# Run full API integration test
python app/tests/test_api.py

# Run all scraper tests
python app/tests/test_scraper.py

# Run AI relevance test
python app/tests/test_ai_filtering.py

# Run simple minimal test
python app/tests/simple_test.py
```