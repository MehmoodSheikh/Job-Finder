# Services Folder - Job Finder

This folder contains the job searching and AI-based job matching functionalities.

---

## Contents

- **`ai_relevance_filtering.py`** — Advanced AI-based relevance filtering service
- **`search_service.py`** — Orchestration service to perform multi-platform job searching

---

## 1. `ai_relevance_filtering.py`
### Purpose:
- Filters and ranks job search results based on how well they match a candidate's preferences using **Google Gemini** models via **LangChain**.
- Falls back to a **rule-based matching system** if AI is not available.

### Key Functionalities:
- **AI Filtering**:
  - Uses **ChatGoogleGenerativeAI** (`gemini-2.0-flash`) to analyze the match between a candidate’s request and a job posting.
  - Factors considered:
    1. **Job Nature** (onsite/remote/hybrid) – strict match needed.
    2. **Job Title** relevance.
    3. **Skills** match.
    4. **Experience** match.
    5. **Location** match.
- **Fallback Filtering**:
  - If AI is not available or fails, a **custom rule-based scoring** system is used to estimate relevance.

### Implementation Details:
- **Prompting**: 
  - A special system prompt guides Gemini to score the match and give an explanation.
- **Batch Processing**:
  - Jobs are scored in **small batches** for faster processing.
- **Score Caching**:
  - Reduces re-scoring the same job-candidate pair.
- **Error Handling**:
  - If parsing Gemini's response fails, the fallback rule-based scoring is automatically applied.

### Output:
- Each job is assigned:
  - `relevance_score` (between 0.0 and 1.0)
  - `relevance_percentage` (e.g., "85%")
  - Short `explanation` for the assigned score.

---

## 2. `search_service.py`
### Purpose:
- Searches jobs **across multiple platforms simultaneously**.
- Integrates results from all scrapers and applies post-processing (like job nature filtering).

### Key Functionalities:
- **Multi-Platform Job Searching**:
  - Uses the `ScraperFactory` to initialize and orchestrate scraping jobs across:
    - LinkedIn
    - Indeed
    - Google Jobs
    - Rozee.pk
    - Glassdoor
- **Safe Concurrent Searching**:
  - Uses **asyncio tasks** to scrape all platforms at the same time.
  - **Exception Handling**: Each scraper is safely wrapped so that a failure in one doesn't crash the others.
- **Standardize Job Natures**:
  - Each job is processed to infer its `jobNature` (Remote, Hybrid, Onsite) based on title, description, etc.
- **Fallback Logic**:
  - If not enough jobs are found after strict filtering, broader results are used.

### Implementation Details:
- **Logging**:
  - Detailed logging to debug which scrapers succeed or fail.
- **Post-Processing**:
  - Standardizes and filters jobs based on `jobNature` if the user specifies.
- **Extensible**:
  - Easily add new scrapers without modifying the core search logic.

