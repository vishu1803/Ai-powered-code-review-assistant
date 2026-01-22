
# 🤖 AI Code Review Assistant

A full-stack AI-powered code review platform that analyzes GitHub repositories for code quality, security vulnerabilities, and performance issues using advanced AI models.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15.0-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🔍 Code Analysis
- **AI-Powered Reviews**: Automated code quality analysis using OpenAI GPT-4
- **Security Scanning**: Identifies security vulnerabilities and potential threats
- **Performance Analysis**: Detects performance bottlenecks and optimization opportunities
- **Code Quality Metrics**: Measures maintainability, complexity, and code standards

### 🔐 Authentication & Integration
- **GitHub OAuth**: Seamless GitHub integration for repository access
- **JWT Authentication**: Secure user authentication and session management
- **Multi-Repository Support**: Connect and analyze multiple GitHub repositories

### 📊 Dashboard & Reporting
- **Real-time Analytics**: Live dashboard with quality trends and statistics
- **Quality Trends**: Visual charts showing code quality improvements over time
- **Issue Tracking**: Categorized issues with severity levels (Critical, High, Medium, Low)
- **Detailed Reports**: Comprehensive analysis reports with actionable insights

### 🚀 Advanced Features
- **Asynchronous Processing**: Background task processing with Celery
- **Real-time Updates**: Live progress tracking during analysis
- **Export Reports**: Download analysis reports in various formats
- **Repository Management**: Easy repository connection and configuration

## 🛠 Tech Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **TailwindCSS** - Utility-first CSS framework
- **Shadcn/ui** - Beautiful, accessible UI components
- **Recharts** - Data visualization library
- **Zustand** - State management
- **React Query** - Server state management
- **Axios** - HTTP client

### Backend
- **FastAPI** - Modern Python web framework
- **Python 3.11+** - Core backend language
- **PostgreSQL** - Primary database
- **Redis** - Caching and task queue
- **SQLAlchemy 2.0** - ORM with async support
- **Celery** - Distributed task queue
- **OpenAI API** - AI-powered code analysis
- **GitHub API** - Repository integration

### DevOps & Tools
- **Docker** - Containerization
- **Git** - Version control
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **JWT** - Authentication tokens

## 🏗 Architecture

```

┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Dashboard │  │Repositories│ │  Reviews  │  │ Analysis │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
↕ REST API
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Auth   │  │   Repos  │  │  Reviews │  │   AI    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
↕
┌─────────────────────────────────────────────────────────────┐
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │PostgreSQL│  │  Redis   │  │  Celery  │  │  GitHub  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘

```

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** 18+ and npm/yarn
- **Python** 3.11+
- **PostgreSQL** 14+
- **Redis** 6+
- **Git**

## 🚀 Installation

### 1. Clone the Repository

```

git clone https://github.com/yourusername/ai-code-review-assistant.git
cd ai-code-review-assistant

```

### 2. Backend Setup

```


# Navigate to backend directory

cd backend

# Create virtual environment

python -m venv venv

# Activate virtual environment

# On Windows:

venv\Scripts\activate

# On macOS/Linux:

source venv/bin/activate

# Install dependencies

pip install -r requirements.txt

# Create .env file

cp .env.example .env

```

### 3. Frontend Setup

```


# Navigate to frontend directory

cd frontend

# Install dependencies

npm install

# or

yarn install

# Create .env.local file

cp .env.example .env.local

```

### 4. Database Setup

```


# Create PostgreSQL database

createdb ai_code_review

# Run migrations

cd backend
alembic upgrade head

```

## ⚙️ Configuration

### Backend Configuration (`.env`)

```


# Database

DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ai_code_review

# Security

SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GitHub OAuth

GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_CALLBACK_URL=http://localhost:8000/api/v1/auth/oauth/github/callback

# OpenAI

OPENAI_API_KEY=your_openai_api_key

# Redis

REDIS_URL=redis://localhost:6379/0

# CORS

CORS_ORIGINS=http://localhost:3000

# Application

APP_NAME=AI Code Review Assistant
DEBUG=True

```

### Frontend Configuration (`.env.local`)

```


# API Configuration

NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# GitHub OAuth (same as backend)

NEXT_PUBLIC_GITHUB_CLIENT_ID=your_github_client_id

# App Configuration

NEXT_PUBLIC_APP_NAME=AI Code Review Assistant
NEXT_PUBLIC_APP_URL=http://localhost:3000

```

### GitHub OAuth Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:8000/api/v1/auth/oauth/github/callback`
4. Copy Client ID and Client Secret to your `.env` files

### OpenAI API Setup

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an API key
3. Add to your backend `.env` file

## 🏃‍♂️ Running the Application

### Start Backend Server

```

cd backend

# Activate virtual environment

source venv/bin/activate  \# or venv\Scripts\activate on Windows

# Run FastAPI server

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

```

Backend will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### Start Redis (separate terminal)

```


# On macOS/Linux

redis-server

# On Windows

redis-server.exe

```

### Start Celery Worker (separate terminal)

```

cd backend
source venv/bin/activate

# Start Celery worker

celery -A app.workers.celery_worker worker --loglevel=info

```

### Start Frontend Server (separate terminal)

```

cd frontend

# Development mode

npm run dev

# or

yarn dev

# Production build

npm run build
npm start

```

Frontend will be available at: `http://localhost:3000`

## 📁 Project Structure

```

ai-code-review-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies/
│   │   │   ├── middlewares/
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── repositories.py
│   │   │       ├── reviews.py
│   │   │       └── analytics.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── database/
│   │   │   └── schemas/
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── repository_service.py
│   │   │   ├── review_service.py
│   │   │   ├── integration_service.py
│   │   │   └── ai_analysis_service.py
│   │   └── workers/
│   │       └── celery_tasks.py
│   ├── alembic/
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── app/
│   │   ├── (auth)/
│   │   │   └── auth/
│   │   │       └── login/
│   │   ├── dashboard/
│   │   ├── repositories/
│   │   ├── reviews/
│   │   ├── analysis/
│   │   └── settings/
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   ├── dashboard/
│   │   ├── repositories/
│   │   └── reviews/
│   ├── lib/
│   │   ├── api/
│   │   ├── store/
│   │   ├── hooks/
│   │   └── utils.ts
│   ├── public/
│   ├── package.json
│   └── .env.local
└── README.md

```

## 📚 API Documentation

### Authentication

```

POST   /api/v1/auth/register          - Register new user
POST   /api/v1/auth/login             - Login user
GET    /api/v1/auth/me                - Get current user
GET    /api/v1/auth/oauth/github      - GitHub OAuth login
GET    /api/v1/auth/oauth/github/callback - GitHub OAuth callback

```

### Repositories

```

GET    /api/v1/repositories           - List user repositories
POST   /api/v1/repositories           - Create repository
GET    /api/v1/repositories/{id}      - Get repository details
PUT    /api/v1/repositories/{id}      - Update repository
DELETE /api/v1/repositories/{id}      - Delete repository
GET    /api/v1/repositories/github/available - List GitHub repos
POST   /api/v1/repositories/github/connect - Connect GitHub repo

```

### Reviews

```

GET    /api/v1/reviews                - List reviews
POST   /api/v1/reviews                - Create review
GET    /api/v1/reviews/{id}           - Get review details
PUT    /api/v1/reviews/{id}           - Update review
DELETE /api/v1/reviews/{id}           - Delete review
GET    /api/v1/reviews/{id}/issues    - Get review issues
GET    /api/v1/reviews/{id}/progress  - Get analysis progress
POST   /api/v1/reviews/{id}/summary   - Generate AI summary

```

### Analytics

```

GET    /api/v1/analytics/overview     - Get analytics overview
GET    /api/v1/analytics/trends       - Get quality trends

```

## 📖 Usage Guide

### 1. **User Registration/Login**
   - Navigate to `http://localhost:3000`
   - Click "Sign In" or register a new account
   - Or use GitHub OAuth for quick login

### 2. **Connect GitHub Repository**
   - Go to Dashboard
   - Click "Connect Repository"
   - Authorize GitHub access
   - Select repositories to connect

### 3. **Start Code Analysis**
   - Navigate to "Code Analysis" page
   - Select a repository
   - Choose analysis type (Full, Security, Performance, Quality)
   - Click "Start Analysis"

### 4. **View Results**
   - Monitor real-time progress
   - View detailed analysis results
   - Check code quality scores
   - Review identified issues
   - Read AI-generated summary

### 5. **Track Improvements**
   - View quality trends over time
   - Compare analysis results
   - Export reports
   - Manage issues

## 🔧 Troubleshooting

### Common Issues

**1. PostgreSQL Connection Error**
```


# Check if PostgreSQL is running

pg_isready

# Verify connection string in .env

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

```

**2. Redis Connection Error**
```


# Check if Redis is running

redis-cli ping

# Should return: PONG

```

**3. GitHub OAuth Issues**
- Verify Client ID and Secret in `.env`
- Check callback URL matches GitHub app settings
- Ensure `http://localhost:8000` is accessible

**4. OpenAI API Errors**
- Verify API key is valid
- Check API quota/billing
- Review rate limits

**5. Celery Worker Not Starting**
```


# Ensure Redis is running

# Check Celery configuration

celery -A app.workers.celery_worker inspect active

```

### Logs

**Backend Logs:**
```


# Check FastAPI logs in terminal

# Or check log files if configured

```

**Frontend Logs:**
```


# Check browser console

# Check Next.js terminal output

```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint/Prettier for TypeScript/React code
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed



## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/vishu1803)

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- GitHub for repository integration
- FastAPI community
- Next.js team
- All contributors

## 📞 Support

For support, email support@aicodereview.com or open an issue on GitHub.

## 🗺 Roadmap

- [ ] GitLab integration
- [ ] Bitbucket support
- [ ] Custom AI models
- [ ] Team collaboration features
- [ ] Advanced reporting
- [ ] CI/CD integration
- [ ] Mobile app
- [ ] VS Code extension

---

**Built with ❤️ using Next.js, FastAPI, and OpenAI**



