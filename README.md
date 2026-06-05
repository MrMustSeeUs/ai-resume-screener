# 📄 AI Resume Screener

🌐 **Live Demo:** https://ai-resume-screener-xwsv.onrender.com

> An AI-powered web app that analyzes resumes against job descriptions using Claude AI.
> Built as Project 1 of an AI Engineering portfolio.

## What It Does

A recruiter uploads a resume PDF and pastes a job description. The app uses Claude AI to return:

- ✅ **Match Score** — 0–100 overall compatibility rating
- 🟢 **Matched Skills** — Skills found in both the resume and job description
- 🔴 **Missing Skills** — Skills required by the job but absent from the resume
- 💡 **Improvement Suggestions** — Actionable advice for the candidate

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend / UI | Streamlit |
| AI / LLM | Anthropic Claude API |
| Input Validation | Pydantic v2 |
| PDF Reading | PyPDF2 |
| Environment Management | python-dotenv |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Hosting | Render |

## Getting Started (Local Development)

### Prerequisites
- Python 3.11+
- Docker (optional, for containerized local dev)
- An [Anthropic API key](https://console.anthropic.com)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/ai-resume-screener.git
cd ai-resume-screener

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 5. Run the app
streamlit run app/main.py
```

The app will open at **http://localhost:8501**

### Run with Docker

```bash
docker-compose up --build
```

### Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
ai-resume-screener/
├── app/
│   ├── __init__.py          # Makes app a Python package
│   ├── main.py              # Streamlit UI entry point
│   ├── models.py            # Pydantic validation models
│   ├── pdf_utils.py         # PDF file reading and validation
│   └── claude_client.py     # Anthropic API integration
├── tests/
│   ├── __init__.py
│   └── test_models.py       # Unit tests
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI/CD pipeline
├── .env.example             # Environment variable template
├── .gitignore               # Files excluded from git
├── Dockerfile               # Container definition
├── docker-compose.yml       # Local Docker dev setup
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Security

- API keys stored in `.env` (never committed to Git)
- Pydantic validates all inputs before processing
- File type and size validation on PDF uploads
- Prompt injection hardening on text inputs
- HTTPS enforced on Render deployment

## Deployment

See the deployment guide in `/docs` (Step 5 of the build).

## License

MIT
