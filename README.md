# Virtual-Personal-Finance-Advisor

A state-of-the-art platform that helps users manage their finances by tracking expenses, suggesting investments via AI, and detecting portfolio anomalies.

## Features
- **Tori AI Agent**: Personalized financial advice using Model Context Protocol (MCP) to access live data.
- **ML Anomaly Detection**: Ensemble voting (Isolation Forest, Autoencoder, SVM) to identify unusual portfolio activity.
- **Fault Tolerant Architecture**: Integrated Circuit Breakers and 2-tier caching.
- **Modern UI**: Dark-themed Flutter dashboard with real-time charts and AI chat.

## Quick Start (Development Mode)

### 1. Backend Setup
```bash
cd finance_advisor_backend
# Ensure .env is populated with mock mode on:
# USE_MOCK_DATA=true
pip install -r ../requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --loop uvloop
```

### 2. Flutter App Setup
```bash
cd flutter_app
flutter pub get
flutter run -d [linux|windows|android]
```

## Deployment (Production)

The project is containerized using Docker for easy deployment of both backend and frontend.

### 1. Configure Environment
Create a `.env` file in the root directory with the following variables:
```env
# Backend Keys
ETORO_API_KEY=your_etoro_api_key
ETORO_USER_KEY=your_etoro_user_key
ETORO_BASE_URL=https://api.etoro.com
ETORO_ENV=demo
ETORO_USERNAME=your_username
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
SECRET_KEY=your_generated_secret_key
GOOGLE_API_KEY=your_gemini_api_key

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=finance_advisor

# Mock Data (Set to true to run without API keys)
USE_MOCK_DATA=true

# Frontend
API_BASE_URL=http://localhost:8000/api/v1
```

### 2. Deploy with Docker Compose
```bash
docker-compose up --build -d
```
This will:
- Spin up a PostgreSQL 16 database.
- Build and run the FastAPI backend (available at `http://localhost:8000`).
- Build the Flutter Web app and serve it via Nginx (available at `http://localhost`).

## Security
- **AES-256-GCM**: Field-level encryption for sensitive user keys.
- **JWT**: Secure session management.

## API Documentation
Once the backend is running, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Status: `http://127.0.0.1:8000/api/v1/health`
