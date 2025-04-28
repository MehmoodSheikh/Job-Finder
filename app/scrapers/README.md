# Scrapers Module

This directory (`app/scrapers/`) contains **web scrapers** and **fallback scrapers** used to extract job listings from multiple platforms including **LinkedIn**, **Indeed**, **Glassdoor**, **Google Jobs**, and **Rozee.pk**.

It is designed to first attempt **API fetching** (if API available or usable) and then **fallback to scraping** when APIs are unavailable, fail, or face strict access barriers.

---
## 📂 Files Overview

| File Name | Purpose |
| :-------- | :------ |
| `base_scraper.py` | Base class for all scrapers (handles requests, logging, and HTTP utilities). |
| `linkedin_scraper.py` | Scraper for LinkedIn jobs (HTML parsing, fallback to LinkedIn web scraping if API fails). |
| `indeed_scraper.py` | Scraper for Indeed jobs (tries Indeed API, HasData API, then scrapes the site). |
| `glassdoor_scraper.py` | Scraper for Glassdoor jobs (tries deprecated Glassdoor API, then falls back to scraping). |
| `google_jobs_scraper.py` | Scraper for Google Jobs (scrapes Google Search's jobs widget). |
| `google_search_scraper.py` | Generic Google Search scraper to find job links when platform scrapers fail. |
| `rozee_pk_scraper.py` | Scraper for Rozee.pk (Pakistan's largest job portal). No public API available. |
| `scraper_factory.py` | Factory to create and manage scrapers dynamically and handle scraper fallbacks. |

---

## 🛠 Core Logic and Implementation Details

### `base_scraper.py`
- Defines a **BaseScraper** class.
- Common utilities for all scrapers: making requests, handling sessions, user-agent headers, random delay, and logging errors.
- Designed to be inherited by specific scrapers.
- **Asynchronous HTTP requests** using `httpx` and `asyncio`.

---

### `linkedin_scraper.py`
- Scrapes **LinkedIn** directly through job search pages when API fails.
- Extracts title, company, location, experience (where available), and job URL.
- Handles **dynamic link-based scraping** for multiple job postings.
- Smartly detects "remote", "hybrid", and "onsite" job types.

---

### `indeed_scraper.py`
- Tries to fetch jobs from:
  1. Official Indeed API (publisher ID) — deprecated for new users.
  2. **HasData API** (web scraper service that bypasses restrictions).
  3. If API fails, **scrapes Indeed's HTML pages**.
  4. If blocked again, **fallbacks to Indeed's mobile site scraping**.
- Handles **multiple fallback strategies** automatically.
- Classifies jobs based on salary, experience, location, and applies basic "onsite/remote" classification.
- Supports handling Cloudflare or Captcha challenges when encountered.

---

### `glassdoor_scraper.py`
- Same layered fallback approach as Indeed.
- Scrapes **Glassdoor job listings** directly.
- Detects **403 Forbidden errors** and falls back to scraping.
- Parses listings from job tiles.

---

### `google_jobs_scraper.py`
- Scrapes Google's native **Job Search widget** results.
- Used when direct platform scraping fails.
- Parses structured job data presented in Google's search page (`ibp=htl;jobs`).

---

### `google_search_scraper.py`
- **Generic scraper** to search jobs on any platform via Google Search.
- Especially useful if direct scraping fails (e.g., due to security or Cloudflare).
- Crawls Google Search results filtered by domain (e.g., site:linkedin.com, site:rozee.pk).
- Provides an extra fallback mechanism.

---

### `rozee_pk_scraper.py`
- Scrapes **Rozee.pk** directly since no public API exists.
- Maps **experience levels** (e.g., "0-1 years", "1-3 years") and **job nature** ("onsite", "remote", "hybrid") into Rozee’s search parameters.
- Parses job cards and fallback JSON embedded in script tags.
- Special focus on Pakistan job seekers.

---

### `scraper_factory.py`
- Implements a **Scraper Factory Pattern**:
  - Dynamically initialize any scraper by platform name.
  - Handles fallback variants via Google Search scrapers.
- Also provides:
  - List of all available scrapers.
  - Async closing of scraper sessions to save memory.
  - Random User-Agent injection to prevent scraping blocks.

---

## ⚡ Features of Scrapers

- ✅ **Asynchronous** scraping for high speed (`async/await`).
- ✅ **Multiple fallback layers** (Official API → HasData API → HTML Scraping → Google Scraping).
- ✅ **User-Agent Rotation** to avoid IP bans.
- ✅ **Error handling** and auto-retries.
- ✅ **Dynamic experience level mapping**.
- ✅ **Hybrid, Remote, Onsite classification** support.
- ✅ **Efficient parsing** with BeautifulSoup.
- ✅ **Minimal dependencies** (only essential libraries used).

---

## 🚀 Scraping Strategy

```plaintext
For each platform:

    1. Try fetching using platform’s API (if available).
    2. If API fails (403, 422, or data error), fallback to direct HTML scraping.
    3. If direct scraping fails (blocked, Cloudflare), fallback to Google Search-based scraping.
    4. Parse and standardize data for relevance matching.
```