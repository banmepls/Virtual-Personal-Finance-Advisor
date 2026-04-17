# Virtual Personal Finance Advisor

# Introducere și Justificare

## Introducere

Contextul actual al piețelor financiare este marcat de o democratizare fără precedent a accesului la investiții pentru utilizatorii de retail. Lansarea eToro Public APIs în 2025 a marcat tranziția către o „economie a constructorilor" (builders' economy), permițând dezvoltatorilor să creeze unelte personalizate de analiză care anterior erau accesibile doar fondurilor de investiții de tip „quantitative hedge funds".  
Proiectul Virtual-Personal-Finance-Advisor propune dezvoltarea unui asistent inteligent care utilizează aceste fluxuri de date pentru a oferi utilizatorului o perspectivă clară asupra sănătății sale financiare. Spre deosebire de platformele de tranzacționare clasice, acest advisor funcționează ca o entitate agentică capabilă să prelucreze volume masive de date în timp real, transformându-le în insight-uri acționabile prin intermediul unei interfețe conversaționale și vizuale intuitive.

## Problema actuală

Investitorii de retail se confruntă adesea cu „zgomotul informațional" și cu dificultatea de a monitoriza simultan active volatile din diverse clase (acțiuni, crypto, forex). Principalele provocări identificate sunt:

* Complexitatea analizei tehnice: Indicatorii macroeconomici și sentimentul pieței sunt greu de corelat manual cu evoluția unui portofoliu specific.  
* Lipsa proactivității: Majoritatea aplicațiilor actuale sunt dashboard-uri pasive; ele nu avertizează utilizatorul asupra anomaliilor comportamentale sau a riscurilor emergente înainte ca acestea să producă pierderi.  
* Barierele tehnice: Integrarea directă cu API-uri financiare complexe (precum cele de la eToro sau Alpha Vantage) necesită infrastructuri de backend robuste care să gestioneze restricțiile de tip CORS și latența ridicată.

## Justificarea soluției propuse

Justificarea acestui proiect de licență rezidă în necesitatea unui instrument care să pună „oamenii în centrul buclei de control" (Keep Humans in the Loop), oferindu-le suport decizional fără a prelua controlul total asupra execuției.  
Alegerea ecosistemului tehnologic:

* FastAPI & Python: Utilizarea framework-ului FastAPI împreună cu biblioteca uvloop este justificată de necesitatea unei performanțe I/O ridicate. Această combinație oferă o viteză de 2-4 ori mai mare în gestionarea cererilor concurente către API-urile eToro față de implementările Python standard.  
* Flutter: Alegerea acestui framework cross-platform asigură o interfață fluidă (60 FPS) și posibilitatea de a utiliza pachete de vizualizare financiară enterprise-grade esențiale pentru redarea graficelor de performanță (OHLC prin `fl_chart`).  
* Arhitectura de tip Agent (Agentic Workflow): Sistemul este proiectat pe modelul Sourcing, Reasoning, and Streaming, permițând advisor-ului să colecteze date, să le analizeze contextual și să livreze răspunsuri în timp real prin intermediul agentului Tori construit cu LangGraph ReAct și Gemini 2.5 Flash.

## Obiective și Limite

Obiectivul principal este crearea unui partener strategic de informare care să replice și să extindă funcționalitățile asistentului Tori de la eToro.  
Important: Aplicația este definită strict ca un instrument de consiliere, monitorizare și educație. Aceasta nu oferă execuție programatică a ordinelor, eliminând astfel riscurile asociate trading-ului automatizat nesupravegheat și asigurând conformitatea cu principiile de siguranță financiară.

# Analiza Pieței și Benchmark

## Situația actuală a aplicațiilor FinTech

Piața aplicațiilor financiare pentru utilizatorii de retail a evoluat de la simple platforme de execuție la ecosisteme complexe de analiză. Tranziția către „The Builders Economy"  permite acum dezvoltatorilor să integreze date de portofoliu live în unelte personalizate prin intermediul Public APIs. Proiectul de față se poziționează ca un punct de convergență între platformele de social trading și asistenții bazați pe Inteligență Artificială.

## Analiză Comparativă

Aplicația propusă a fost comparată cu principalii jucători din piață, evaluând capacitățile de analiză, accesul la date (APIs) și costurile asociate.

| Caracteristică | eToro (Tori) | Robinhood | Revolut | Virtual Advisor |
| :---- | :---- | :---- | :---- | :---- |
| Focus Principal | Social Trading | Simplitate/Zero Taxe | Banking Integrat | Analiză Predictivă |
| Acces API | Public APIs (2025)  | Limitat/Proprietar | Business API (limitat) | Deschidere totală (MCP) |
| Asistență AI | Tori (Informațional) | Limitată | Analiză cheltuieli de bază | Agentic RAG \+ Modele ML |
| Execuție | Da | Da | Da | Nu (Safety First) |
| Analiză Sentiment | Da | Nu | Nu | Da (Alpha Vantage) |

## Benchmarkingul Capacităților de Consiliere AI

Referința principală pentru acest proiect este agentul Tori dezvoltat de eToro. Tori funcționează ca un însoțitor conversațional care utilizează date publice, profiluri de active și portofolii publice pentru a răspunde la întrebări de tipul „Compară NVIDIA cu Tesla".  
Spre deosebire de Tori, care are limitări de acces (ex: limită de 3 întrebări pe săptămână pentru conturile Bronze) , advisor-ul virtual implementat în acest proiect oferă o arhitectură deschisă bazată pe Model Context Protocol (MCP). Această tehnologie permite agentului să interogheze peste 60 de indicatori tehnici și date fundamentale în timp real, oferind un nivel de detaliu analitic superior variantelor comerciale de bază.

## Metrici de Evaluare și Validare

Pentru a asigura rigoarea științifică, performanța advisor-ului este măsurată folosind metrici standardizate pentru două componente critice:

1. Înțelegerea Limbajului Natural (NLU):  
   Eficacitatea agentului în identificarea intențiilor utilizatorului este evaluată prin scorul F1, care reprezintă media armonică între precizie (P) și rapel (R):  
   F1 \= 2 \* (P \* R) / (P \+ R)  
   Ținta proiectului este un scor F1 de peste 0.82 pentru a minimiza riscul de interpretare eronată a interogărilor financiare.  
2. Acuratețea Predicțiilor Financiare:  
   Pentru evaluarea modelelor de prognoză a portofoliului (LSTM vs. Prophet), se utilizează MAPE (Mean Absolute Percentage Error).  
   Studiile comparative arată că modelele de tip LSTM tind să obțină o eroare MAPE mai scăzută (3-8%) în scenarii complexe de serii temporale față de modelele statistice tradiționale.

## Justificarea Modelului „Fără Execuție"

Absența funcționalității de execuție este o decizie arhitecturală strategică fundamentată pe principiul „Keep Humans in the Loop". Aceasta elimină riscurile asociate „halucinațiilor financiare" ale modelelor LLM, unde un agent ar putea inventa recomandări sau date financiare eronate. Astfel, aplicația rămâne un partener de suport decizional pur, protejând capitalul utilizatorului de erori algoritmice nesupravegheate.

# Arhitectura și Structuri Tolerante la Defecte

## Concepte Fundamentale

Toleranța la defecte reprezintă capacitatea unui sistem de a continua operarea corectă chiar și în prezența erorilor sau a defectelor unor componente. În contextul unei aplicații financiare, unde datele de portofoliu și prețurile de piață sunt critice, arhitectura trebuie să distingă clar între:

* Defect (Fault): O anomalie fizică sau logică în sistem (ex: un API terț care nu răspunde).  
* Eroare (Error): Starea activată de un defect care afectează datele (ex: un preț de activ care figurează ca fiind nul).  
* Eșec (Failure): Deviația sistemului de la comportamentul specificat (ex: dashboard-ul nu se încarcă).

Importanța acestei structuri este justificată de necesitatea de a evita eșecurile în cascadă. Într-un sistem distribuit modern, costurile de downtime pot fi semnificative, motiv pentru care se implementează strategii de detectare, izolare și recuperare.

## Diagrama Bloc a Sistemului

Arhitectura este organizată pe straturi, asigurând o decuplare completă a componentelor pentru a preveni punctele unice de eșec (Single Points of Failure).

```
Flutter Mobile UI
       │ HTTP/REST + JWT
       ▼
FastAPI Backend (uvloop)
  ├── /api/v1/etoro     → EtoroService
  ├── /api/v1/market    → MarketDataService
  ├── /api/v1/anomaly   → AnomalyService (ML Ensemble)
  ├── /api/v1/agent     → Tori Agent (LangGraph + Gemini)
  └── /api/v1/health    → CircuitBreaker status
       │
  ┌────┴─────────────────────────┐
  │   MCP Server (FastMCP)       │
  │  - get_my_portfolio()        │
  │  - get_stock_price()         │
  │  - get_market_sentiment()    │
  └────┬──────────┬──────────────┘
       │          │
  eToro API   Alpha Vantage API
       │
  ┌────┴──────────────────────┐
  │  Circuit Breaker Layer    │
  │  LRU Cache (256 entries)  │
  │  PostgreSQL (asyncpg)     │
  │  HashiCorp Vault (AES256) │
  └───────────────────────────┘
```

| Componentă | Tehnologie | Rol în Reziliență |
| :---- | :---- | :---- |
| Frontend (Mobile/Desktop) | Flutter | Gestionarea stărilor offline și reconectarea asincronă la API. |
| Backend Orchestrator | FastAPI \+ uvloop | Procesare I/O rapidă; izolarea cererilor de date prin 6 routere dedicate. |
| Data Bridge (MCP) | FastMCP (Model Context Protocol) | Abstractizarea comunicării cu eToro și Alpha Vantage ca tool-uri LangChain. |
| Persistență | PostgreSQL \+ asyncpg | Stocarea asincronă a istoricului conversațiilor și a memoriei agentului AI. |
| Securitate | HashiCorp Vault \+ AES-256-GCM | Gestionarea cheilor criptografice master și criptarea câmpurilor sensibile din DB. |

Fluxul de Date: Utilizatorul (Flutter) interoghează Backend-ul \> Agentul Tori interoghează MCP Server pentru date live prin tool-uri Python \> Datele trec prin Circuit Breaker și LRU Cache \> Rezultatul este livrat înapoi în frontend prin streaming Gemini 2.5 Flash.

## Decizii Arhitecturale și Software

Pentru a asigura toleranța la defecte, au fost adoptate următoarele tipare de design (Design Patterns):

1. **Bulkhead Isolation**: Serviciul care procesează datele eToro (`EtoroService`) este izolat de cel pentru Alpha Vantage (`MarketDataService`). Dacă API-ul eToro devine indisponibil, asistentul poate oferi în continuare analize de piață generale prin Alpha Vantage.  
2. **Circuit Breaker** (`app/core/circuit_breaker.py`): Implementat ca un automat cu stări asyncio-safe cu trei stări: `CLOSED`, `OPEN`, și `HALF_OPEN`. Din starea `CLOSED`, după 5 eșecuri consecutive, trece în `OPEN` (fail-fast imediat, fără a interoga API-ul inutil). După 60 de secunde, trece în `HALF_OPEN` unde permite o singură cerere de test; dacă reușește de 2 ori consecutiv, revine în `CLOSED`. Circuit breakere independente există pentru `etoro` și `alpha_vantage`.  
3. **Cache pe două niveluri** (`app/services/cache_service.py`): Un LRU in-memory cu capacitate de 256 intrări și TTL configurabil (5 minute pentru portofoliu eToro) funcționează ca L1. Baza de date PostgreSQL funcționează ca L2, asigurând persistența datelor la reporniri. Sistemul include și un contor de cotă Alpha Vantage (25 req/zi) care blochează automat apelurile excedentare și revine la date cache-uite.  
4. **Readiness Probes (Healthchecks)**: Utilizarea utilitarului `pg_isready` în Docker Compose asigură că baza de date este complet inițializată înainte ca backend-ul să înceapă procesarea cererilor. Endpoint-ul `/api/v1/health` expune starea tuturor Circuit Breaker-elor.

## Analiza și Managementul Defectelor

Sistemul este proiectat să gestioneze proactiv o listă de defecte comune în aplicațiile FinTech:

| Defect Potențial | Mecanism de Implementare | Soluție Tehnică |
| :---- | :---- | :---- |
| Downtime API eToro | Circuit Breaker (5 eșecuri → OPEN) | Fallback la `mock_data.MOCK_ETORO_PORTFOLIO` cu flag `_fallback: "circuit_breaker_open"`. |
| Rate Limit Alpha Vantage (429) | Contor zilnic în `cache_service.py` | Servire din cache LRU sau DB la depășirea pragului de 25 req/zi. |
| Inconsecvența Datelor | Validarea prin scheme Pydantic la intrare | Respingerea payload-urilor care nu respectă tipurile de date financiare (ex: preț negativ). |
| Latență de Rețea | Timeouts asincrone `httpx` (5s portofoliu, 10s instrumente) | Întreruperea cererilor care depășesc pragul, menținând fluiditatea UI. |
| Erori de Autentificare | JWT HS256 (python-jose) + bcrypt (passlib) | Token-uri cu expirare 24h; criptare AES-256-GCM pentru chei API sensibile în DB. |
| Exfiltrare date sensibile | HashiCorp Vault (`app/core/vault.py`) | Cheia master AES-256 se generează și se stochează în Vault la prima rulare, cu fallback la cheie din env var pentru dev. |
| InstrumentId necunoscut | `instrument_resolver.py` + rezoluție dinamică | La apariția unui ID necunoscut în portofoliu, serviciul eToro interoghează automat endpoint-ul `/market-data/instruments?instrumentIds=` și populează registrul local. |

## Modulul de Detecție a Anomaliilor: Sistemul de Voting

Pentru a monitoriza comportamentul portofoliului eToro și a detecta evoluții neobișnuite, aplicația utilizează un ansamblu hibrid (Ensemble Learning) format din trei modele independente, orchestrate de `app/ml/anomaly_service.py`.

**Extragerea caracteristicilor** (`_portfolio_to_features`): Pozițiile din portofoliu sunt transformate într-un vector numpy de dimensiune fixă (max. 10 poziții × 4 caracteristici = 40 valori), unde fiecare poziție contribuie cu: `[quantity, avgBuyPrice, currentValue, unrealizedPnL]`. Antrenamentul inițial se realizează pe date sintetice generate prin perturbarea vectorului curent cu zgomot aleatoriu de ±5%.

Cele 3 Modele utilizate:

1. **Isolation Forest** (`app/ml/isolation_forest.py`): Utilizează implementarea `scikit-learn` cu 100 de estimatori și `contamination=0.1`. Scorurile brute negative sklearn sunt normalizate la `[0, 1]` prin formula `clip(-raw * 2.0, 0, 1)`.  
2. **PCA Autoencoder** (`app/ml/autoencoder.py`): Un autoencoder linear implementat cu numpy prin descompunere SVD (`n_components=3`). La inferență, calculează MSE-ul de reconstrucție față de spațiul latent al datelor normale; o eroare MSE ridicată semnalează o deviație bruscă față de comportamentul normal al portofoliului.  
3. **One-Class SVM** (`app/ml/one_class_svm.py`): Definește o frontieră de decizie în jurul datelor „normale" cu `nu=0.1`. Orice punct din afara hipersferei este marcat ca anomalie structurală.

Mecanismul de Voting — Calibrated Soft Majority Voting (`app/ml/voting_ensemble.py`):  
Fiecare model generează un scor de anomalie `Si(x)` normalizat în `[0, 1]`. Decizia finală este luată pe baza unui sistem de voting ponderat:

> `S_weighted = (0.35 * S_IF + 0.40 * S_AE + 0.25 * S_SVM)`

Dacă `S_weighted > 0.5`, sistemul marchează anomalia ca „certificată". Nivelul de încredere (`LOW/MEDIUM/HIGH`) se determină din numărul de modele individuale care depășesc pragul (1/3, 2/3, respectiv 3/3). Sistemul notifică agentul Tori prin istoricul de memorie al conversației.

# Analiza și Documentația Defectelor

## Strategia de Gestiune a Defectelor (Why?)

Decizia de a investi în mecanisme robuste de toleranță la defecte este fundamentată pe structura specifică a mediului de execuție al aplicației. Sistemul se bazează pe trei surse de date externe: API-ul eToro (cu autentificare API Key + User Key), API-ul Alpha Vantage (cu limită draconiană de 25 req/zi la contul free tiered) și modelul LLM Google Gemini 2.5 Flash. Fiecare dintre aceste dependențe este un potențial punct de eșec pe care aplicația nu îl controlează.

Principala motivație arhitecturală este **degradarea grațioasă** (Graceful Degradation): în loc să arunce erori brute utilizatorului, sistemul încearcă întotdeauna să returneze un răspuns parțial valid, însoțit de un flag de status (ex: `_fallback: "circuit_breaker_open"`), permițând frontend-ului Flutter să afișeze un mesaj informativ în loc de un ecran gol.

## Clasificarea și Lista Defectelor Identificate

| ID | Tip | Componentă Afectată | Probabilitate | Severitate |
| :---- | :---- | :---- | :---- | :---- |
| F-01 | External Fault | eToro API (downtime, timeout) | Medie | Critică |
| F-02 | Rate Limit Fault | Alpha Vantage API (429) | Ridicată | Medie |
| F-03 | Security Fault | Scurgere eToro API Key din DB | Scăzută | Critică |
| F-04 | Data Integrity Error | Instrument ID necunoscut în portofoliu | Medie | Medie |
| F-05 | Infrastructure Fault | Postgres down la startup | Scăzută | Critică |
| F-06 | Network Error | Latență httpx > 5s | Medie | Medie |
| F-07 | ML Drift | Modele ML antrenate pe date sintetice | Ridicată | Scăzută |

## Documentația și Analiza Defectelor (Case Studies)

### F-01: eToro API Downtime

**Descriere**: API-ul eToro returnează erori HTTP 500/503 sau nu răspunde în limita de 5 secunde (timeout httpx).

**Fluxul de execuție protejat**:
1. `EtoroService.get_live_portfolio()` apelează `self._cb.call(self._fetch_from_api)`.
2. Dacă apelul eșuează, `CircuitBreaker._on_failure()` incrementează contorul de eșecuri.
3. La 5 eșecuri consecutive, starea trece din `CLOSED` → `OPEN`.
4. Apelurile ulterioare ridică imediat `CircuitBreakerOpen` fără a mai contacta API-ul.
5. Serviciul revine la `mock_data.MOCK_ETORO_PORTFOLIO` și adaugă flag-ul `_fallback`.
6. Flutter afișează datele mock cu un indicator vizual de „date offline".
7. După 60 de secunde, circuitul trece în `HALF_OPEN` și permite un singur apel de test.

### F-02: Rate Limit Alpha Vantage (25 req/zi)

**Descriere**: Planul gratuit Alpha Vantage impune o limită de 25 cereri per zi. La depășire, API-ul returnează un răspuns JSON cu mesaj de eroare în loc de date.

**Fluxul de execuție protejat**:
1. `MarketDataService.get_stock_quote()` apelează `cache_service.av_quota_exceeded()` înainte de orice call HTTP.
2. Dacă cota este epuizată, se returnează ultima cotație valabilă din cache-ul LRU sau din PostgreSQL.
3. `cache_service.av_increment_counter()` este chemat după fiecare apel reușit, cu cheia `"YYYY-MM-DD"` resetată zilnic.

### F-03: Scurgere de Date Sensibile (eToro API Key)

**Descriere**: Cheile API stocate plain-text în baza de date pot fi exfiltrate printr-un atac de tip SQL Injection sau acces neautorizat la server.

**Soluția implementată** (`app/core/security.py` + `app/core/vault.py`):
- Cheia master AES-256 este generată și stocată exclusiv în **HashiCorp Vault** la path-ul `secret/finance_advisor/master_key`.
- La fiecare scriere în DB a unui câmp sensibil, `encrypt_field()` aplicaă **AES-256-GCM** cu nonce de 96 biți generat random, returnând un payload JSON base64: `{n: <nonce>, c: <ciphertext>}`.
- La citire, `decrypt_field()` extrage cheia din Vault și decriptează payload-ul; autenticitatea este garantată de tag-ul GCM (protecție anti-tampering).

### F-04: Instrument ID Necunoscut

**Descriere**: API-ul eToro returnează `instrumentId` numerice (ex: 13375) care nu există în registrul local de instrumente. Afișarea unui ID brut în UI degradează experiența utilizatorului.

**Soluția implementată** (`app/services/instrument_resolver.py` + `EtoroService._enrich_positions()`):
- La procesarea fiecărei poziții, `instrument_resolver.is_seen(iid)` verifică dacă ID-ul a fost deja rezolvat în sesiunea curentă.
- ID-urile nevăzute sunt colectate în batch și trimise la endpoint-ul `/market-data/instruments?instrumentIds=id1,id2,...`.
- Răspunsul este parsat pentru a extrage `instrumentDisplayName`, `symbolFull`, și `instrumentTypeID` (mapat la clase de active: 1=Forex, 2=Commodities, 5=Stocks, 6=ETF, 10=Crypto).
- Informațiile rezolvate sunt înregistrate în `instrument_resolver`, prevenind re-interogarea în apeluri ulterioare.

### F-05: PostgreSQL Unavailable la Startup

**Descriere**: Stack-ul Docker pornit cu `docker compose up` poate iniția BackEnd-ul înainte ca Postgres să fie gata, ducând la erori de conexiune la inițializare.

**Soluția implementată** (`docker-compose.yaml`):
- Serviciul backend are condiția `depends_on: db: condition: service_healthy`.
- Healthcheck-ul DB este configurat cu `pg_isready -U user -d financedb` cu interval de 5 secunde, garantând pornirea secvențială corectă.

## Mecanisme și Soluții Tehnice Implementate

| Mecanism | Fișier Implementat | Descriere |
| :---- | :---- | :---- |
| Circuit Breaker (3 stări) | `app/core/circuit_breaker.py` | Automat asyncio-safe: CLOSED → OPEN (5 eșecuri) → HALF_OPEN (60s) → CLOSED (2 succese). |
| LRU Cache cu TTL | `app/services/cache_service.py` | `OrderedDict`-based, 256 intrări, TTL per-entry verificat la `get()`. |
| Cota Alpha Vantage | `app/services/cache_service.py` | Contor zilnic `{YYYY-MM-DD: count}`, resetat automat. Blocaj la 25/zi. |
| AES-256-GCM Field Encryption | `app/core/security.py` | Criptare simetrică cu nonce random 96-bit; autenticitate garantată de GCM tag. |
| HashiCorp Vault Integration | `app/core/vault.py` | Client `hvac`, generare automată cheie master la prima rulare, fallback env var. |
| JWT Authentication | `app/core/security.py` | HS256, expirare 24h, verificare prin `python-jose`. |
| Mock Data Fallback | `app/services/mock_data.py` | Date statice complete de portofoliu și citate, activate prin `USE_MOCK_DATA=true`. |
| Instrument Resolver | `app/services/instrument_resolver.py` | Registru in-memory de instrumente cu rezoluție dinamică prin API eToro. |
| Pydantic Validation | Toate schemele din `app/schemas/` | Validare strictă a tipurilor la intrarea datelor din API-uri externe. |

## Partea de Studiu: Evaluarea Rezilienței

Pe baza implementării descrise, sistemul a fost evaluat pe următoarele scenarii de defect:

**Scenariu 1: eToro API 100% Indisponibil**  
Rezultat: Circuit Breaker trece în OPEN după 5 apeluri. Utilizatorul vede date mock complete cu indicator `_fallback`. Agentul Tori continuă să funcționeze în mod limitat, bazându-se pe datele Alpha Vantage disponibile.

**Scenariu 2: Alpha Vantage Cotă Epuizată**  
Rezultat: Modulul de cache returnează cotațiile din ultima sesiune validă. Banner informativ în Flutter: „Datele de piață sunt din cache — cotă zilnică epuizată."

**Scenariu 3: HashiCorp Vault Indisponibil**  
Rezultat: `vault.py` detectează eroarea de autentificare și revine la cheia din variabila de mediu `FALLBACK_MASTER_KEY`. Un log de warning este emis. Criptarea câmpurilor sensibile continuă să funcționeze, dar cu o cheie cu nivel de securitate redus — acceptabil în mediul de dezvoltare.

**Concluzie**: Sistemul demonstrează o **disponibilitate de tier-2** în condiții adverse: niciun scenariu individual de defect nu duce la un eșec complet al aplicației. Degradarea este graduală și transparentă față de utilizator.

# Modele de Predicție și Sistem de Voting

## Abordarea Ensemble Learning în Finanțe

Motivația alegerii unui ansamblu de modele față de un singur algoritm rezidă în reducerea varianței predicției. Un singur model poate „specializa" pe tipuri specifice de anomalii, ratând altele. Prin combinarea a trei abordări fundamentale diferite — arbori de izolare, reducere dimensională prin SVD și mașini cu suport vectorial — sistemul acoperă un spectru larg de tipare de anomalii:

* **Anomalii punctuale** (outlieri izolați): detectați eficient de Isolation Forest.
* **Anomalii contextuale** (deviații față de comportamentul temporal normal): detectate de PCA Autoencoder prin eroarea de reconstrucție.
* **Anomalii structurale** (schimbări de regim în distribuția datelor): detectate de One-Class SVM prin frontiera de decizie.

## Prognoza Sănătății Portofoliului (LSTM vs. Prophet)

Arhitectura documentelor de referință ale proiectului planifică integrarea a două modele de prognoză pentru evaluarea sănătății viitoare a portofoliului:

**LSTM (Long Short-Term Memory)**: Rețele neuronale recurrente adecvate pentru serii temporale financiare cu dependențe pe termen lung. Avantajele principale includ capacitatea de a modela relații non-liniare complexe și sezonalitate multiplă. Studiile comparative indică erori MAPE de 3-8% pentru seturi de date financiare cu volatilitate medie.

**Prophet (Meta)**: Model statistic aditiv, ideal pentru serii temporale cu tendințe clare și sezonalitate anuală/săptămânală. Avantajul principal este robustețea față de valorile lipsă și interpretabilitatea componentelor (tendință + sezonalitate + efecte de vacanță). MAPE tipic: 5-12% pentru date financiare.

**Decizia de implementare**: La nivel de producție, se recomandă utilizarea LSTM pentru portofolii cu active volatile (crypto, tech stocks) și Prophet pentru active mai stabile (ETF-uri, obligațiuni), cu un mecanism de selecție automată bazat pe volatilitatea istorică a portofoliului.

## Modulul de Anomalii: Sistemul de Voting între 3 Modele

Implementat complet în modulele `app/ml/`, sistemul de voting este detaliat în secțiunea anterioară. Rezumând formulele matematice centrale:

**Formula de scoring compus**:
```
S_weighted = (w_IF * S_IF + w_AE * S_AE + w_SVM * S_SVM) / (w_IF + w_AE + w_SVM)
```
Unde ponderile calibrate sunt: `w_IF = 0.35`, `w_AE = 0.40`, `w_SVM = 0.25`.

**Pragul de decizie**: `S_weighted > 0.50` → anomalie certificată.

**Nivelul de încredere**:
- `HIGH` (3/3 modele depășesc pragul)
- `MEDIUM` (2/3 modele depășesc pragul)  
- `LOW` (1/3 sau niciun model depășește pragul)

Aceste ponderi reflectă sensibilitatea relativă a modelelor la datele financiare tabulare: Autoencodergerul PCA are cea mai mare sensibilitate la tipare temporale normale (0.40), urmat de Isolation Forest pentru outlieri punct (0.35) și One-Class SVM pentru frontiere structurale (0.25).

## Validarea Performanței NLU

Agentul Tori folosește modelul **Gemini 2.5 Flash** de la Google prin `langchain-google-genai`, integrat într-un agent ReAct construit cu `langgraph.prebuilt.create_react_agent`. Agentul are access la 4 unelte definite prin FastMCP:

1. `get_my_portfolio()` — date live portofoliu eToro.
2. `get_all_instruments()` — lista completă de instrumente cunoscute.
3. `get_stock_price(symbol)` — cotație în timp real Alpha Vantage.
4. `get_market_sentiment()` — sentiment de piață și știri recente.

**Promptul de sistem** al agentului Tori îl instrucționează să fie un „Senior Financial AI Advisor", să rămână orientat pe date, să nu execute tranzacții și să redirecționeze întrebările despre anomalii către dashboard-ul dedicat.

**Memoria conversației** este persitată în PostgreSQL prin `app/agent/memory.py`, permițând continuarea contextului pe parcursul mai multor sesiuni. Istoricul este recuperat asincron și convertit în structura `[(role, content)]` suportată de LangGraph.

# Implementare Software și Securitate

## Structura Proiectului

Proiectul este organizat în două componente principale:

```
Virtual-Personal-Finance-Advisor/
├── finance_advisor_backend/          # Backend Python
│   ├── main.py                       # Punctul de intrare FastAPI + uvloop
│   ├── docker-compose.yaml           # Stack: backend + PostgreSQL
│   ├── requirements.txt              # 37 dependențe Python
│   └── app/
│       ├── api/v1/endpoints/         # Routere: market, etoro, auth, anomaly, health, agent
│       ├── agent/                    # tori_agent.py + memory.py
│       ├── core/                     # circuit_breaker, config, database, security, vault
│       ├── mcp/                      # server.py (FastMCP tool definitions)
│       ├── ml/                       # isolation_forest, autoencoder, one_class_svm,
│       │                             # voting_ensemble, anomaly_service
│       ├── models/                   # SQLAlchemy ORM models
│       ├── schemas/                  # Pydantic schemas
│       └── services/                 # etoro, market_data, cache_service,
│                                     # instrument_resolver, mock_data
└── flutter_app/                      # Frontend Flutter (Mobile + Desktop)
    ├── lib/                          # Sursele Dart
    └── pubspec.yaml                  # Dependențe Flutter
```

## Stack Tehnologic Complet

| Componentă | Tehnologie | Versiune |
| :---- | :---- | :---- |
| Framework Backend | FastAPI | 0.135.1 |
| Event Loop | uvloop | 0.22.1 |
| HTTP Client | httpx | 0.28.1 |
| ORM | SQLAlchemy + asyncpg | 2.0.48 + 0.31.0 |
| Migrații DB | Alembic | 1.18.4 |
| Validare Date | Pydantic | 2.12.5 |
| Machine Learning | scikit-learn + numpy | 1.5.2 + 1.26.4 |
| Framework Agent AI | LangChain + LangGraph | ≥0.3.7 |
| Model LLM | Gemini 2.5 Flash | via langchain-google-genai |
| MCP Server | FastMCP | ≥1.26.0 |
| Autentificare | python-jose (JWT) + passlib (bcrypt) | 3.3.0 + 1.7.4 |
| Criptografie | cryptography (AES-256-GCM) | 44.0.2 |
| Secret Management | hvac (HashiCorp Vault) | 2.1.0 |
| Frontend | Flutter (Dart) | cross-platform |
| Containerizare | Docker + Docker Compose | - |
| Baza de Date | PostgreSQL | - |

## Securitate Multi-Strat

Aplicația implementează un model de securitate în adâncime (Defense in Depth) cu mai multe straturi:

**Stratul 1 — Transport**: Toate comunicările externe sunt realizate prin HTTPS. CORS este configurat în FastAPI (în producție restricționat la originile aplicației Flutter).

**Stratul 2 — Autentificare**: JWT HS256 cu expirare de 24 de ore. Parolele utilizatorilor sunt hash-uite cu bcrypt (cost factor implicit passlib). Endpoint-urile protejate necesită header `Authorization: Bearer <token>`.

**Stratul 3 — Autorizare la nivel de câmp**: Cheile API eToro stocate în baza de date sunt criptate cu AES-256-GCM. Nonce-ul unic de 96 biți pentru fiecare criptare previne atacurile de tip known-plaintext. Tag-ul de autentificare GCM garantează integritatea datelor (anti-tampering).

**Stratul 4 — Gestiunea secretelor**: Cheia master AES-256 este administrată exclusiv de HashiCorp Vault (`app/core/vault.py`). La prima pornire în mediu de producție, `VaultManager._init_vault()` verifică existența secretului la path-ul `secret/finance_advisor/master_key`; dacă nu există, generează 32 de bytes random criptografic puternic și îi stochează în Vault. Key rotation poate fi implementată prin actualizarea secretului în Vault fără modificarea codului.

**Stratul 5 — Validare intrare**: Toate datele externe (răspunsuri API eToro/Alpha Vantage, inputul utilizatorului) sunt validate prin scheme Pydantic înainte de procesare. Câmpurile cu valori imposibile (prețuri negative, cantități NaN) sunt respinse cu eroare HTTP 422.

# Parte de Studiu și Concluzii

## Contribuții Originale

Proiectul Virtual Personal Finance Advisor aduce o serie de contribuții tehnice originale față de soluțiile comerciale existente:

1. **Sistem de Voting Calibrat pentru Anomalii Financiare**: Implementarea unui ansamblu hibrid cu ponderi diferențiate (0.40/0.35/0.25) pentru trei paradigme algoritmice diferite (reconstrucție SVD, izolare prin arbori, frontieră SVM), cu clasificare automată a nivelului de încredere.

2. **Rezoluție Dinamică de Instrumente**: Mecanismul `instrument_resolver` care detectează automat ID-uri de instrumente necunoscute și le rezolvă în timp real prin API-ul eToro, fără intervenție manuală — soluție critică pentru portabilitatea între conturi eToro cu profiluri diferite.

3. **Integrare MCP-LangGraph pentru Finanțe**: Utilizarea Model Context Protocol ca strat de abstractizare între logica de business Python și agentul LLM, permițând adăugarea de noi surse de date fără a modifica codul agentului.

4. **Cache pe Două Niveluri cu Contor de Cotă**: Soluția combinată LRU in-memory + PostgreSQL cu tracked zilnic al consumului Alpha Vantage, evitând blocarea completă a funcționalității la depășirea limitei gratuite.

## Limitări și Direcții Viitoare

**Limitări actuale**:
- Modelele ML sunt antrenate inițial pe date sintetice (±5% zgomot față de baseline). O precizie mai mare necesită acumularea de date istorice reale de portofoliu.
- Modulul `get_market_sentiment()` returnează în prezent date statice mock; integrarea completă cu un flux real de sentiment (News API + Alpha Vantage News) este planificată.
- Modelele de prognoză LSTM și Prophet nu sunt încă integrate în versiunea curentă a aplicației.

**Direcții de dezvoltare**:
- Implementarea unui pipeline de reantrenare automată a modelelor ML (`retrain()` este deja implementat în `anomaly_service.py`) declanșat la acumularea a minimum 30 de snapshot-uri reale de portofoliu.
- Extinderea MCP Server cu unelte pentru analiza tehnică (RSI, MACD, Bollinger Bands) prin integrare cu provider de date financiare istorice.
- Implementarea notificărilor push în Flutter pentru alerte de anomalii detectate de sistemul de voting.
- Adăugarea autentificării OAuth2 cu eToro pentru flux complet de onboarding automatizat.

## Concluzii

Construcția Virtual Personal Finance Advisor a demonstrat că este posibilă realizarea unei soluții de consiliere financiară inteligentă, reziliente și sigure, folosind exclusiv tehnologii open-source și API-uri publice. Sistemul îmbunătățește experiența investitorului de retail prin:

- **Transparență**: Vizualizarea completă a portofoliului cu date agregate și îmbogățite semantic.
- **Proactivitate**: Detectarea automată a anomaliilor comportamentale înainte că acestea să producă pierderi semnificative.
- **Siguranță**: Arhitectura „fără execuție" respectă principiul Human-in-the-Loop, eliminând riscurile trading-ului automatizat nesupravegheat.
- **Reziliență**: Niciun defect individual al unui serviciu extern nu duce la eșecul complet al aplicației, datorită layering-ului de circuit breakers, cache și fallback-uri.

Implementarea reprezintă o bază solidă extensibilă, cu separare clară a responsabilităților (MCP pentru date, LangGraph pentru raționament, Flutter pentru prezentare), ce poate fi extinsă cu noi surse de date și capacități analitice fără refactoring major al arhitecturii de bază.
