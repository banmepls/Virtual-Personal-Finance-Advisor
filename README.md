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
uvicorn main:app --reload --loop uvloop
```

### 2. Flutter App Setup
```bash
cd flutter_app
flutter pub get
flutter run -d [linux|windows|android]
```

## Security
- **AES-256-GCM**: Field-level encryption for sensitive user keys.
- **JWT**: Secure session management.

## API Documentation
Once the backend is running, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Status: `http://127.0.0.1:8000/api/v1/health`
