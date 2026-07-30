# SecurePipe

> A web-based DevSecOps security scanner that performs concurrent security checks on public source-code repositories and presents consolidated results in one dashboard.

SecurePipe helps developers identify security issues early in the software-development lifecycle. Submit a public GitHub, GitLab, or Bitbucket repository URL and SecurePipe coordinates multiple scanning tools, normalises their results, calculates a severity-based security score, stores scan history, and provides AI-assisted remediation guidance for selected high-priority findings.

> **Academic project:** IU International University of Applied Sciences  
> **Course:** DLMCSPSE01 – Project: Software Engineering  
> **Author:** Akhil Thoppil Shabu  
> **Matriculation number:** 4250982

---

## Live Application

- **Frontend:** `<YOUR-VERCEL-OR-FRONTEND-URL>`
- **Backend API:** `<YOUR-RENDER-OR-BACKEND-URL>`
- **Health check:** `<YOUR-BACKEND-URL>/api/v1/health`

No login is required. To test the application, submit a valid **public** repository URL.

---

## Features

- Scan public GitHub, GitLab, and Bitbucket repositories
- Run seven security tools concurrently
- Detect code weaknesses, vulnerable dependencies, exposed secrets, IaC configuration risks, and container/filesystem issues
- Consolidate scanner output into a normalised finding format
- Calculate a 0–100 repository Security Score
- Display severity summaries, findings, source locations, and remediation information
- Store completed scans and findings in Supabase PostgreSQL
- Show a scan-history view
- Generate AI-assisted remediation guidance for up to five Critical or High findings
- Use fallback guidance when AI assistance is unavailable
- Support a basic GitHub webhook endpoint for prototype automated scan initiation
- Protect selected API endpoints through API-key authentication
- Continue returning available results if an individual scanner fails

---

## Security Scanner Coverage

| Tool | Primary purpose |
|---|---|
| Bandit | Python static application security testing (SAST) |
| Safety | Python dependency vulnerability detection |
| TruffleHog | Hardcoded secret and credential detection |
| Checkov | Infrastructure-as-Code (IaC) misconfiguration detection |
| npm audit | Node.js dependency vulnerability detection |
| Semgrep | Multi-language, pattern-based static analysis |
| Trivy | Container image and filesystem vulnerability scanning |

---

## Architecture

```text
Browser
   |
   v
React + Vite + Tailwind CSS frontend
   |
   v
FastAPI backend
   |
   +--> Repository manager: clone, validate, limit size, clean up
   |
   +--> Parallel scanner orchestration
   |      +--> Bandit
   |      +--> Safety
   |      +--> TruffleHog
   |      +--> Checkov
   |      +--> npm audit
   |      +--> Semgrep
   |      +--> Trivy
   |
   +--> Google Gemini AI remediation service
   |
   +--> Supabase PostgreSQL scan history and findings
```

The backend uses `asyncio.gather()` to run independent scanners concurrently. Each scanner is executed through a `safe()` wrapper so an individual tool failure can be logged without necessarily terminating the full scan workflow.

---

## Security Score

SecurePipe calculates a score from 0 to 100 using weighted severity deductions:

```text
score = max(0, 100 - (20 × Critical + 10 × High + 5 × Medium + 2 × Low))
```

A higher score indicates fewer severe findings. The score is intended as a quick prioritisation indicator and does not replace professional vulnerability assessment.

### Example

```text
0 Critical + 6 High + 3 Medium
score = 100 - (0 + 60 + 15) = 25
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | Supabase PostgreSQL |
| AI remediation | Google Gemini API via `google-genai` |
| Security tools | Bandit, Safety, TruffleHog, Checkov, npm audit, Semgrep, Trivy |
| Containerisation | Docker and Docker Compose |
| Frontend deployment | Vercel |
| Backend deployment | Render |

---

## Prerequisites

Install the following before running SecurePipe locally:

- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Docker Compose v2 (`docker compose`)
- A Supabase project
- A Google Gemini API key, if AI remediation is required

For manual, non-containerised development, you also need:

- Python 3.11 or later
- Node.js 20 or later
- npm

---

## Quick Start with Docker Compose

### 1. Clone the repository

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd Securepipe
```

### 2. Create your environment file

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Update `.env` with your own values. Never commit this file.

### 3. Build and start the services

```bash
docker compose up --build
```

### 4. Open SecurePipe

After the containers have started, open:

```text
Frontend: http://localhost:5173
Backend API documentation: http://localhost:8000/docs
Health endpoint: http://localhost:8000/api/v1/health
```

> The exact local frontend port can differ if your `docker-compose.yml` specifies a different port. Use the port configured in your compose file.

### 5. Stop the services

```bash
docker compose down
```

To remove containers and volumes:

```bash
docker compose down -v
```

---

## Environment Variables

Create a `.env` file based on `.env.example`.

```env
# Backend protection
API_KEY=replace-with-a-strong-local-api-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=replace-with-your-supabase-key

# Google Gemini
GEMINI_API_KEY=replace-with-your-gemini-api-key

# Application configuration
CORS_ORIGINS=http://localhost:5173
MAX_REPOSITORY_SIZE_MB=50
SCAN_TIMEOUT_SECONDS=120

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=replace-with-your-local-api-key
```

> **Important:** Environment-variable names must match the names used in your code. If your project uses names such as `GOOGLE_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, or `VITE_API_URL`, use those names instead.

---

## Running Without Docker

Use this option only if all scanner dependencies are installed on your operating system.

### Backend

```bash
cd backend

python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS / Linux
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install dependencies and start FastAPI:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open the URL displayed by Vite, normally:

```text
http://localhost:5173
```

---

## How to Use

1. Open the SecurePipe frontend.
2. Enter a valid public repository URL.
3. Start the scan.
4. Wait for the configured scanners to complete.
5. Review the Security Score, severity totals, and detailed findings.
6. Open Scan History to review stored completed scans.
7. Review the remediation guidance for Critical and High findings.

### Example Repository URLs

```text
https://github.com/owner/repository
https://gitlab.com/owner/repository
https://bitbucket.org/owner/repository
```

Only publicly accessible repositories are supported in this prototype.

---

## API Overview

> Endpoint paths may differ slightly depending on the final router configuration. Confirm them in the interactive API documentation at `/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Check backend availability |
| `POST` | `/api/v1/scan` | Start a repository scan |
| `GET` | `/api/v1/scans` | Retrieve scan-history records |
| `POST` | `/api/v1/webhook/github` | Receive prototype GitHub webhook events |

Protected endpoints require the configured API key:

```text
X-API-Key: <your-api-key>
```

### Example Health Request

```bash
curl http://localhost:8000/api/v1/health
```

### Example Scan Request

```bash
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{
    "repository_url": "https://github.com/owner/repository"
  }'
```

---

## Project Structure

```text
Securepipe/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # Configuration, logging, authentication, models
│   │   ├── db/               # Supabase persistence
│   │   ├── scanners/         # Independent scanner adapters
│   │   └── services/         # Scan orchestration and AI remediation
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable interface components
│   │   ├── pages/            # Scan, results, dashboard and history pages
│   │   └── api.js            # API client configuration
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Testing Evidence

Targeted end-to-end tests were performed against public repositories.

| Test area | Result |
|---|---|
| Repository submission and scan start | Passed |
| Multi-tool scan and severity output | Passed |
| Score validation: 0 Critical, 6 High, 3 Medium | Score 25, passed |
| Score validation: 0 Critical, 1 High | Score 90, passed |
| Scan-history persistence | Passed |
| Gemini and fallback-label distinction | Passed |
| Backend connectivity | Passed |
| Nodejs-goof scan performance | 77.56 seconds; conditional pass because the repository size was not independently recorded |

These results validate the main integration paths but do not prove all possible scanner, network, cloud-hosting, or repository failure conditions.

---

## Known Limitations

SecurePipe is a functional academic prototype. The following limitations are known:

- Only public repositories are supported; private repositories require OAuth, secure token storage, and access-control design.
- GitHub webhook support is foundational only and does not include signature verification, replay prevention, durable retry queues, or multi-provider support.
- Free-tier backend hosting can cause cold-start latency.
- AI guidance is limited to the first five Critical or High findings to control API usage and rate limits.
- AI guidance can be unavailable, empty, or safety-filtered; SecurePipe displays clearly labelled fallback guidance in such cases.
- Scanner output can vary by operating system, repository language, dependency ecosystem, network availability, and external tool version.
- Further automated tests are required to simulate a wider range of individual scanner failures.
- The Security Score is a prioritisation aid, not a formal risk rating or security guarantee.

---

## Security Notes

- Do not commit `.env` files, API keys, tokens, passwords, or Supabase service-role keys.
- Use `.env.example` to document required variables without exposing secrets.
- Scan only repositories that you are authorised to access and assess.
- Scanner findings can contain sensitive paths, dependency information, or secret-like content. Handle scan data carefully.
- This project is an academic prototype and should not be relied upon as the only security control for production systems.

---

## Future Improvements

- OAuth-based private repository scanning
- Signed GitHub webhook verification and replay protection
- Durable scan queues, retries, and dead-letter queues
- Real-time scan progress using WebSockets
- More comprehensive automated unit, integration, and failure-path testing
- Scheduled scans and scan comparisons
- Software Bill of Materials (SBOM) generation
- Jira, GitHub Issues, or ServiceNow ticket creation
- Organisation accounts and role-based access control
- Always-on or paid backend hosting to reduce cold starts

---

## Academic Documentation

This repository accompanies the following portfolio project:

```text
IU International University of Applied Sciences
Course: DLMCSPSE01 – Project: Software Engineering
Project: SecurePipe – AI-Powered CI/CD Security Scanner
Student: Akhil Thoppil Shabu
Matriculation Number: 4250982
```

The repository contains the final source-code snapshot for the project. Additional academic documentation, including requirements, architecture, test evidence, technical debt, and final reflection, is provided in the associated portfolio submission.

---

## License

This project was created for academic assessment. No production warranty is provided.
