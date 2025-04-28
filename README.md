# Job Finder API

A scalable, AI-powered FastAPI backend that scrapes multiple job platforms, applies intelligent relevance scoring using Google Gemini + LangChain, and returns the most relevant job matches with fallback mechanisms.

🔗 **Live Deployment:** [job-finder.up.railway.app](https://job-finder.up.railway.app)  
🔗 **Source Code:** [GitHub Repo](https://github.com/MehmoodSheikh/Job-Finder)

## Table of Contents

- [About the Project](#about-the-project)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Core Logic Details](#core-logic-details)
- [AI Relevance Matching (Deep Dive)](#ai-relevance-matching-deep-dive)
- [Fallback and Error Handling](#fallback-and-error-handling)
- [Folder Structure](#folder-structure)
- [API Usage](#api-usage)
- [Screenshots](#Screenshots)
- [Sample Request and Response](#sample-request-and-response)
- [Setup Locally](#setup-locally)
- [Important Notice](#Important-Notice)
  
---

## About the Project

Job Finder API scrapes job postings from multiple platforms such as LinkedIn, Glassdoor, Rozee.pk, Indeed, and Google Jobs.  
It intelligently applies AI-based filtering using LangChain + Gemini to prioritize the most relevant jobs based on user search queries.

This project is:
- Fully asynchronous
- Supports automatic fallback scraping
- Includes robust error handling and retries
- AI-enhanced job matching with detailed relevance scores

---

## System Architecture

```
User Request (Job Title, Location, Experience)
    ↓
FastAPI Endpoint /search_jobs/
    ↓
Scraper Factory
    ↓
Try to fetch via API , if fail falls back to
    ↓
Primary Scrapers (LinkedIn, Glassdoor, Indeed, Rozee.pk, Google Jobs)
    ↓
If Primary Scraping Fails → Fallback Scrapers (Google Search Scrapers)
    ↓
Fallback Handling + Retry Logic
    ↓
Mock Job Generation (if scraping fails completely)
    ↓
AI Relevance Matching (LangChain + Google Gemini)
    ↓
Score Calculation (0-100) + Explanation
    ↓
Sorted Relevant Jobs
    ↓
API Response (Top Matching Jobs)

```

---

## Key Features

- Scraping multiple platforms concurrently
- Automatic fallback to alternative scraping if primary scraper fails
- Retry logic with exponential backoff and random User-Agent rotation
- AI-based scoring of jobs based on user preferences
- Rule-based fallback scoring if AI service unavailable
- Mock job generation if real scraping fails
- Production-grade, scalable, modular codebase

---

## Core Logic Details

### Scraping Workflow

- Firstly, Try to fetch jobs results via official API if it fails than move to scrapping.
- Each job platform has a dedicated scraper implementing `BaseScraper`.
- Scrapers perform asynchronous scraping via `asyncio` and `httpx`.
- In case of failures due to captchas, rate limits, or structural changes:
  - Primary Attempt: Use the standard scraper for the platform.
  - Fallback 1: Switch to mobile version scraping.
  - Fallback 2: Utilize the HasData Web Scraping API as a last resort.

This multi-tiered approach ensures maximum uptime and data retrieval reliability.

### Retry Strategy

- Each HTTP request is retried up to 3 times with randomized delays if it fails.
- Different User-Agent headers are rotated for each request.
- Failing one scraper does not stop the global job search.
---

## AI Relevance Matching (Deep Dive)

- LangChain is used to orchestrate prompts sent to Google Gemini models.
- The AI model scores each job between 0-100 based on:
  - Exact match of Job Nature (Remote, Hybrid, Onsite)
  - Similarity of Position Title
  - Skill matching
  - Experience level comparison
  - Location proximity

Each job result includes:
- Relevance Score (float between 0.0 and 1.0)
- Relevance Percentage (0% - 100%)
- Short AI explanation why the job scored that relevance

![AI_EXPLANATION_SS](https://github.com/MehmoodSheikh/Job-Finder/raw/main/AI_explanation.png)
---

## Prompt Engineering

- Candidate requirements and job details are inserted into a carefully designed prompt.
- The AI then returns:
  - `SCORE`: 0-100
  - `EXPLANATION`: Why this score is appropriate

- If Gemini API fails, a fallback rule-based scoring system based on keyword matching is used instead.

---

## Fallback and Error Handling

| Problem Area        | Handling Strategy                   |
|----------------------|--------------------------------------|
| Scraper fails        | Skip, log error, continue others     |
| Request Timeout      | Retry with exponential backoff       |
| API Key Missing      | Fallback to rule-based scoring       |
| AI Model Call Failure| Fallback to rule-based scoring       |

---

## Folder Structure

```markdown
Job-Finder/
│
├── app/
│   ├── api/                  # FastAPI API routes
│   ├── core/                 # Settings and environment configs
│   ├── models/               # Pydantic models (Job, JobRequest)
│   ├── scrapers/             # Scrapers and fallback scrapers
│   ├── services/             # AI relevance filter and search service
│   ├── static/               # Static frontend (optional)
│   ├── scripts/              # Helper scripts (nltk setup etc.)
│   └── tests/                # Unit tests
│
├── server.py                 # Application entrypoint
├── requirements.txt          # Python dependencies
├── Procfile                  # Railway deployment file
├── .env.example              # Environment variables template
└── README.md                 # Project documentation

```

## API Usage

### POST /search_jobs/

### Request Payload

| Field         | Type     | Required | Description                     |
|:--------------|:---------|:---------|:--------------------------------|
| query         | string   | Yes      | Target job title or keyword     |
| location      | string   | Optional | Desired job location            |
| experience    | string   | Optional | Years of experience             |
| job_nature    | string   | Optional | Remote / Onsite / Hybrid        |
| max_results   | integer  | Optional | Maximum jobs to fetch (default 20) |

---

## Screenshots

### Sample Request and Response

| JSON Request SS | 
|:------------:|
![Request](https://github.com/MehmoodSheikh/Job-Finder/blob/main/JSON_request_TEST_API%20.png)

| JSON Response SS |
|:-------------:|
![Response](https://github.com/MehmoodSheikh/Job-Finder/raw/main/JSON_response_TEST_API%20.png) 

### Frontend Screenshots

| Homepage | 
|:------------:|
![FE_1](https://github.com/MehmoodSheikh/Job-Finder/raw/main/FE_1.png)

| Search Results | 
|:------------:|
![FE_2](https://github.com/MehmoodSheikh/Job-Finder/raw/main/FE_2.png)

---

## Setup Locally

### Clone the Repository

```bash
git clone https://github.com/MehmoodSheikh/Job-Finder.git
cd Job-Finder
```

### Create a Virtual Environment:
```
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### Install Dependencies:
```
pip install -r requirements.txt
```

### Run the Application:
```
uvicorn app.main:app --reload
```
---
## Important Notice

This project implements a **hybrid retrieval logic**:  
- **First**, it attempts to fetch job listings using **official APIs** if available.  
- **If API retrieval fails** (due to API errors, unavailability, or restrictions), it **falls back to web scraping** methods to ensure robustness and maximum data coverage.

### 📄 API Access Status per Platform:

| Platform    | Official API Availability | Access Method                             | Notes                                                                 |
|-------------|----------------------------|------------------------------------------|-----------------------------------------------------------------------|
| Indeed      | Deprecated / Third-party   | Using third-party APIs (e.g., HasData)    | Official Indeed API is not available for new developers.             |
| Rozee.pk    | No Public API               | Contact Rozee.pk for partnership         | No public access; only private/internal APIs are available.          |
| Glassdoor   | Deprecated                  | Contact Glassdoor for business partnership | Public Glassdoor API has been discontinued for general developers. |

### 📢 Current Implementation Details:

- API connection attempts have been made where possible (e.g., HasData for Indeed).
- However, **several official APIs are either deprecated or require private partnerships**, which are currently pending or unavailable.
- **LinkedIn scraping is successfully implemented** and retrieves job postings reliably.
- For platforms like **Indeed**, **Glassdoor**, and **Rozee.pk**, multiple scraping techniques were attempted (including handling Cloudflare and bot protections).  
  Despite all optimization efforts, **heavy anti-bot mechanisms** prevented consistent scraping without official access or enterprise proxies.
- Therefore, **fallback scrapers** are provided, but **may have limited results** until official API keys are approved.

### 🔥 In Summary:

- **LinkedIn search** is fully functional.
- **Other platforms** are under **API approval waiting** or require **enterprise partnerships**.
- As soon as access is granted, the system can **seamlessly auto-update** without major changes.













