# Virtual Personal Finance Advisor

# Introducere și Justificare

## Introducere

Contextul actual al piețelor financiare este marcat de o democratizare fără precedent a accesului la investiții pentru utilizatorii de retail. Lansarea eToro Public APIs în 2025 a marcat tranziția către o „economie a constructorilor” (builders' economy), permițând dezvoltatorilor să creeze unelte personalizate de analiză care anterior erau accesibile doar fondurilor de investiții de tip „quantitative hedge funds”.  
Proiectul Virtual-Personal-Finance-Advisor propune dezvoltarea unui asistent inteligent care utilizează aceste fluxuri de date pentru a oferi utilizatorului o perspectivă clară asupra sănătății sale financiare. Spre deosebire de platformele de tranzacționare clasice, acest advisor funcționează ca o entitate agentică capabilă să prelucreze volume masive de date în timp real, transformându-le în insight-uri acționabile prin intermediul unei interfețe conversaționale și vizuale intuitive.

## Problema actuală

Investitorii de retail se confruntă adesea cu „zgomotul informațional” și cu dificultatea de a monitoriza simultan active volatile din diverse clase (acțiuni, crypto, forex). Principalele provocări identificate sunt:

* Complexitatea analizei tehnice: Indicatorii macroeconomici și sentimentul pieței sunt greu de corelat manual cu evoluția unui portofoliu specific.  
* Lipsa proactivității: Majoritatea aplicațiilor actuale sunt dashboard-uri pasive; ele nu avertizează utilizatorul asupra anomaliilor comportamentale sau a riscurilor emergente înainte ca acestea să producă pierderi.  
* Barierele tehnice: Integrarea directă cu API-uri financiare complexe (precum cele de la eToro sau Alpha Vantage) necesită infrastructuri de backend robuste care să gestioneze restricțiile de tip CORS și latența ridicată.

## Justificarea soluției propuse

Justificarea acestui proiect de licență rezidă în necesitatea unui instrument care să pună „oamenii în centrul buclei de control” (Keep Humans in the Loop), oferindu-le suport decizional fără a prelua controlul total asupra execuției.  
Alegerea ecosistemului tehnologic:

* FastAPI & Python: Utilizarea framework-ului FastAPI împreună cu biblioteca uvloop este justificată de necesitatea unei performanțe I/O ridicate. Această combinație oferă o viteză de 2-4 ori mai mare în gestionarea cererilor concurente către API-urile eToro față de implementările Python standard.  
* Flutter: Alegerea acestui framework cross-platform asigură o interfață fluidă (60 FPS) și posibilitatea de a utiliza Syncfusion Flutter Charts, o librărie enterprise-grade esențială pentru vizualizarea datelor financiare complexe (candlestick, OHLC).  
* Arhitectura de tip Agent (Agentic Workflow): Sistemul este proiectat pe modelul Sourcing, Reasoning, and Streaming, permițând advisor-ului să colecteze date, să le analizeze contextual și să livreze răspunsuri în timp real.

## Obiective și Limite

Obiectivul principal este crearea unui partener strategic de informare care să replice și să extindă funcționalitățile asistentului Tori de la eToro.  
Important: Aplicația este definită strict ca un instrument de consiliere, monitorizare și educație. Aceasta nu oferă execuție programatică a ordinelor, eliminând astfel riscurile asociate trading-ului automatizat nesupravegheat și asigurând conformitatea cu principiile de siguranță financiară.

# Analiza Pieței și Benchmark

## Peisajul actual al aplicațiilor FinTech

Piața aplicațiilor financiare pentru utilizatorii de retail a evoluat de la simple platforme de execuție la ecosisteme complexe de analiză. Tranziția către „The Builders Economy”  permite acum dezvoltatorilor să integreze date de portofoliu live în unelte personalizate prin intermediul Public APIs. Proiectul de față se poziționează ca un punct de convergență între platformele de social trading și asistenții bazați pe Inteligență Artificială.

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

Referința principală pentru acest proiect este agentul Tori dezvoltat de eToro. Tori funcționează ca un însoțitor conversațional care utilizează date publice, profiluri de active și portofolii publice pentru a răspunde la întrebări de tipul „Compară NVIDIA cu Tesla”.  
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

## Justificarea Modelului „Fără Execuție”

Absența funcționalității de execuție este o decizie arhitecturală strategică fundamentată pe principiul „Keep Humans in the Loop”. Aceasta elimină riscurile asociate „halucinațiilor financiare” ale modelelor LLM, unde un agent ar putea inventa recomandări sau date financiare eronate. Astfel, aplicația rămâne un partener de suport decizional pur, protejând capitalul utilizatorului de erori algoritmice nesupravegheate.

# Arhitectura și Structuri Tolerante la Defecte

## Concepte Fundamentale

Toleranța la defecte reprezintă capacitatea unui sistem de a continua operarea corectă chiar și în prezența erorilor sau a defectelor unor componente. În contextul unei aplicații financiare, unde datele de portofoliu și prețurile de piață sunt critice, arhitectura trebuie să distingă clar între:

* Defect (Fault): O anomalie fizică sau logică în sistem (ex: un API terț care nu răspunde).  
* Eroare (Error): Starea activată de un defect care afectează datele (ex: un preț de activ care figurează ca fiind nul).  
* Eșec (Failure): Deviația sistemului de la comportamentul specificat (ex: dashboard-ul nu se încarcă).

Importanța acestei structuri este justificată de necesitatea de a evita eșecurile în cascadă. Într-un sistem distribuit modern, costurile de downtime pot fi semnificative, motiv pentru care se implementează strategii de detectare, izolare și recuperare.

## Diagrama Bloc a Sistemului

Arhitectura este organizată pe straturi, asigurând o decuplare completă a componentelor pentru a preveni punctele unice de eșec (Single Points of Failure).

| Componentă | Tehnologie | Rol în Reziliență |
| :---- | :---- | :---- |
| Frontend (Mobile) | Flutter | Gestionarea stărilor offline și reconectarea asincronă la API. |
| Backend Orchestrator | FastAPI \+ uvloop | Procesare I/O rapidă; izolarea cererilor de date prin WebSockets. |
| Data Bridge (MCP) | Model Context Protocol | Abstractizarea comunicării cu eToro și Alpha Vantage. |
| Persistență | PostgreSQL \+ asyncpg | Stocarea asincronă a istoricului și a memoriei agentului AI. |

Fluxul de Date: Utilizatorul (Flutter) interoghează Backend-ul \> Agentul AI interoghează MCP Server pentru date live \> Datele sunt procesate de modulele ML \> Rezultatul este livrat înapoi în frontend prin streaming.

## Decizii Arhitecturale și Software

Pentru a asigura toleranța la defecte, au fost adoptate următoarele tipare de design (Design Patterns):

1. Bulkhead Isolation: Serviciul care procesează datele eToro este izolat de cel pentru Alpha Vantage. Dacă API-ul eToro devine indisponibil, asistentul poate oferi în continuare analize de piață generale.  
2. Circuit Breaker: Implementat în FastAPI pentru a opri temporar cererile către furnizorii de date care returnează erori repetate (ex: cod 429 \- Rate Limit), prevenind blocarea întregului event loop.  
3. Readiness Probes (Healthchecks): Utilizarea utilitarului pg\_isready în Docker Compose pentru a asigura că baza de date este complet inițializată înainte ca backend-ul să înceapă procesarea cererilor.

## Analiza și Managementul Defectelor

Sistemul este proiectat să gestioneze proactiv o listă de defecte comune în aplicațiile FinTech:

| Defect Potențial | Mecanism de Implementare | Soluție Tehnică |
| :---- | :---- | :---- |
| Downtime API Terț | Monitorizarea codurilor de stare HTTP. | Fallback la date cache-uite anterior sau mesaje informative către utilizator. |
| Inconsecvența Datelor | Validarea prin scheme Pydantic la intrare. | Respingerea payload-urilor care nu respectă tipurile de date financiare (ex: preț negativ). |
| Latență de Rețea | Timeouts asincrone în httpx. | Întreruperea cererilor care depășesc pragul de 5s pentru a menține fluiditatea UI. |
| Erori de Autentificare | Gestiunea securizată prin Secrets module. | Generarea de chei criptografice unice și rotația automată a token-urilor JWT. |

## Modulul de Detecție a Anomaliilor: Sistemul de Voting

Pentru a monitoriza comportamentul portofoliului eToro și a detecta evoluții neobișnuite, aplicația utilizează un ansamblu hibrid (Ensemble Learning) format din trei modele independente.  
Cele 3 Modele utilizate:

1. Isolation Forest: Un algoritm bazat pe arbori care izolează punctele de date atipice. Are complexitate liniară și este ideal pentru detectarea tranzacțiilor suspicioase în seturi mari de date.  
2. LSTM Autoencoder: O rețea neuronală care învață tiparul normal al activității financiare (reconstrucție). O eroare de reconstrucție (MSE) mare semnalează o deviație temporală.  
3. One-Class SVM: Definește o frontieră de decizie în jurul datelor "normale". Orice punct situat în afara hipersferei este marcat ca anomalie structurală.

Mecanismul de Voting (Calibrated Soft Majority Voting):  
Fiecare model generează un scor de anomalie Si(x) normalizat între . Decizia finală este luată pe baza unui sistem de voting ponderat.

# Analiza și Documentația Defectelor

## Strategia de Gestiune a Defectelor (Why?)

## Clasificarea și Lista Defectelor Identificate

## Documentația și Analiza Defectelor (Case Studies)

## Mecanisme și Soluții Tehnice Implementate

## Partea de Studiu: Evaluarea Rezilienței

# Modele de Predicție și Sistem de Voting

## Abordarea Ensemble Learning în Finanțe

## Prognoza Sănătății Portofoliului (LSTM vs. Prophet)

## Modulul de Anomali: Sistemul de Voting între 3 Modele

## Validarea Performanței NLU

# Implementare Software și Securitate

# Parte de Studiu și Concluzii

