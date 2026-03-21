# Virtual Personal Finance Advisor — Fault Tolerance & Resilience Report

## Introducere și Justificare
Sistemul a fost conceput pentru a gestiona date financiare critice într-un mediu distribuit, unde dependențele externe (eToro API, Alpha Vantage) sunt puncte potențiale de eșec.

## Strategia de Gestiune a Defectelor
Am implementat o arhitectură pe mai multe niveluri pentru a asigura continuitatea serviciului:
1.  **Bulkhead Isolation**: Serviciile sunt izolate logic. Un eșec în Alpha Vantage nu blochează accesul la portofoliul eToro.
2.  **Circuit Breaker (Pattern)**: Previne eșecurile în cascadă. Dacă un API returnează erori repetate, circuitul se deschide (OPEN), respingând cererile imediat pentru a proteja resursele sistemului.
3.  **Graceful Degradation with Caching**: Cache-ul LRU și DB acționează ca un fallback. Dacă un API este indisponibil, sistemul servește ultimele date cunoscute.
4.  **Anti-Spam & Quota Enforcement**: Controlul strict al ratelor de interogare Alpha Vantage (25 req/zi) previne blocarea cheilor de API.

## Mecanisme Tehnice Implementate

### 1. Circuit Breaker (`app/core/circuit_breaker.py`)
Implementat ca un state machine asincron cu stările `CLOSED`, `OPEN`, `HALF_OPEN`.
- **Prag eșec**: 5 erori consecutive.
- **Timp recuperare**: 60 secunde.

### 2. Caching Stratificat (`app/services/cache_service.py`)
- **L1 (In-memory)**: LRU cache pentru latență minimă.
- **L2 (Database)**: `CacheEntry` pentru persistență între reporniri.

### 3. Modulul de Detecție a Anomaliilor (`app/ml/`)
Sistem de voting între 3 modele:
- **Isolation Forest**: Detectează outlieri structurali.
- **PCA Autoencoder**: Reconstrucția erorii pentru deviații de pattern.
- **One-Class SVM**: Delimitarea frontierei de date normale.

## Matricea Defectelor și Soluții

| Defect | Impact | Soluție Tehnologică |
| :--- | :--- | :--- |
| API Rate Limit (429) | Blocare temporară | Circuit Breaker + Quota Counter |
| Date Corupte/Nule | Halucinații analitice | Pydantic Schema Validation |
| Latență Rețea Ridicată | UI înghețat | Async Timeouts + Mock Fallback |
| Pierdere Conexiune DB | Crash Backend | Healthcheck Probes + Docker Restart |

## Concluzii Reziliență
Prin combinația de pattern-uri de design (Circuit Breaker, Bulkhead) și fallback-uri bazate pe date mock/cache, advisor-ul oferă o experiență stabilă utilizatorului retail, eliminând riscurile asociate dependențelor externe instabile.
