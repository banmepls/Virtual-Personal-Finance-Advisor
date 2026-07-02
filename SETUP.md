# Virtual Personal Finance Advisor — Compilare, instalare și lansare

Repo: https://github.com/banmepls/Virtual-Personal-Finance-Advisor

Proiectul are 2 componente:
- Backend: FastAPI (Python 3.11) + PostgreSQL 16 — `finance_advisor_backend/`
- Aplicație mobilă/web: Flutter (Dart SDK >= 3.0) — `flutter_app/`

## Cerințe
- Docker + Docker Compose (varianta recomandată)
- Pentru dezvoltare locală: Python 3.11, Flutter SDK 3.x + Dart >= 3.0, Android SDK / Chrome

## Varianta A: Docker (întreg stack-ul)

Un singur `docker-compose.yaml` (în rădăcina repo-ului) pornește baza de date, backend-ul și aplicația Flutter web.

```bash
docker compose up --build
```

Servicii expuse:
- Aplicație Flutter (web, nginx): http://localhost:80
- Backend API: http://localhost:8001
- Swagger: http://localhost:8001/docs
- PostgreSQL: localhost:5432

Note:
- Migrarea/inițializarea bazei de date rulează automat la pornirea backend-ului (entrypoint → `scripts.init_db`).
- Frontend-ul se compilează cu `API_BASE_URL=http://localhost:8001/api/v1` (build arg în `flutter_app/Dockerfile`). Pentru alt backend:
  ```bash
  API_BASE_URL=http://host:port/api/v1 docker compose up --build
  ```
- Oprire: `docker compose down` (adaugă `-v` pentru a șterge și volumul bazei de date).

## Varianta B: Rulare locală (dezvoltare)

### Backend
```bash
cd finance_advisor_backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate       # Linux/macOS
pip install -r ../requirements.txt

docker compose up -d db           # doar PostgreSQL
alembic upgrade head              # migrări

python main.py
# sau: uvicorn main:app --host 0.0.0.0 --port 8000 --reload --loop uvloop
```
Backend pe http://localhost:8000 (docs la `/docs`, health la `/api/v1/health`).

### Aplicația Flutter
```bash
cd flutter_app
flutter pub get
```

Compilare:
```bash
flutter build apk           # Android
flutter build web           # Web
flutter build windows       # Windows desktop
```

Lansare (URL-ul backend-ului se transmite prin --dart-define=API_BASE_URL):
```bash
# Web
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000/api/v1

# Emulator Android
flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1

# Dispozitiv fizic Android
flutter run -d <device_id> --dart-define=API_BASE_URL=http://<IP_PC>:8000/api/v1
```
