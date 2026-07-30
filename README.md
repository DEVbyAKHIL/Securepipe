# Securepipe
1. Purpose
SecurePipe is an automated DevSecOps orchestration platform designed to facilitate "shift-left" security by detecting vulnerabilities in public source-code repositories
. It integrates seven specialised scanners to audit applications, dependencies, secrets, and infrastructure configurations before production deployment
.
2. Prerequisites
Python 3.x: Required for the FastAPI backend and core scanning engine
.
Node.js: Required to support the npm audit scanner module
.
Git: Necessary for the repo_manager.py to perform shallow cloning of target repositories
.
Docker: Required for containerised deployment
.
3. Required Accounts and Services
GitHub Account: Necessary for hosting the project repository and utilizing webhooks
.
Supabase: A cloud-hosted PostgreSQL service used to persist scan metadata, findings, and historical records
.
Google Gemini API: Access to the Gemini 2.0 Flash model via the google-genai SDK for AI-powered remediation
.
Render: Target platform for hosting the FastAPI backend service
.
Vercel: Target platform for hosting the React frontend
.
4. Environment Configuration
Create a .env file in the root directory. MANDATORY SECURITY NOTE: Do not commit secrets, API keys, Supabase credentials, or Gemini keys to GitHub; ensure the .env file is included in your .gitignore
.
The configuration must include:
X-API-Key: A secret token for authenticating platform requests
.
Google Gemini API Key: [TO CONFIRM EXACT ENV VAR NAME].
Supabase URL: [TO CONFIRM EXACT ENV VAR NAME].
Supabase Service Key: [TO CONFIRM EXACT ENV VAR NAME].
5. Backend Installation and Start-up
Clone the Repository: [TO CONFIRM EXACT COMMAND] from the public GitHub URL
.
Navigate to Backend: Access the backend/ directory
.
Install Dependencies: [TO CONFIRM EXACT COMMAND, e.g., pip install -r requirements.txt]. The backend requires the fastapi and google-genai libraries
.
Local Execution: Start the FastAPI server using the asynchronous configuration
. [TO CONFIRM START COMMAND, e.g., uvicorn app.main:app].
Docker Deployment: Build and run the service using the provided Dockerfile
.
6. Frontend Installation and Start-up
Navigate to Frontend: Access the frontend/ directory
.
Install Dependencies: [TO CONFIRM EXACT COMMAND, e.g., npm install]. The frontend is built on React 19 and Vite
.
Styling: The UI utilizes Tailwind CSS for utility-first styling
.
Start Development Server: Start the application using Vite
. [TO CONFIRM START COMMAND, e.g., npm run dev].
7. Running a Security Scan
Submit Repository: Enter a valid public GitHub, GitLab, or Bitbucket URL into the web interface
.
Orchestration: The system will trigger asyncio.gather() to run seven scanners (Bandit, Safety, TruffleHog, Checkov, npm audit, Semgrep, and Trivy) concurrently
.
Progress Monitoring: View the real-time progress stages: repository cloning, multi-tool analysis, and AI enrichment
.
Review Results: Inspect the severity-classified findings and the quantitative Security Score (0–100)
.
AI Remediation: For the top five Critical/High findings, review the Gemini-generated remediation insights
. Note that other findings will display separate static fallback guidance
.
8. Verifying the Installation
Backend Connectivity: The dashboard should display "Backend connected - v2.0.0" upon successful initialisation
.
Health Check: Access the GET /api/v1/health endpoint for a status report
.
Score Calculation Test: Submit a repository with known counts. For example, a repo with 0 Critical, 6 High, and 3 Medium findings must result in an exact score of 25
.
History Persistence: Confirm that completed scans appear in the Scan History view, indicating successful Supabase integration
.
9. Troubleshooting
Cold Starts: If the backend is on Render's free tier, the first request after inactivity may face high latency
.
Scanner Failures: If an individual tool fails, the safe() wrapper ensures the rest of the scan continues; check backend logs for tool-specific exceptions
.
AI API Limits: If Gemini returns an HTTP 429 (Rate Limit) error, the system will automatically retry with exponential backoff
.
Safety Filtering: If a remediation suggestion is missing for a High finding, check if the AI response was empty due to content safety filtering
.
10. Security Notes
Public Scope: The current prototype is restricted to public repositories; private repository scanning requiring OAuth is not supported
.
API Protection: All protected endpoints require a valid X-API-Key in the request header
.
Webhook Limitations: The basic GitHub webhook endpoint does not currently support signature verification or replay prevention

