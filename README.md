# InsightFlow AI — Autonomous Business Intelligence Platform

InsightFlow AI is a modern, enterprise-grade Autonomous Business Intelligence (BI) frontend engineered with Next.js App Router, TypeScript, Tailwind CSS, Recharts, and Lucide React.

It orchestrates a specialized multi-agent swarm:
1. **Data Analyst Agent**: Ingestion, schema validation, statistical distribution, and automated EDA.
2. **Root Cause Agent**: Metric decomposition, factor attribution, and anomaly diagnostics.
3. **Forecasting Agent**: Prophet/Bayesian rolling projections, scenarios, and confidence intervals.
4. **Report Agent**: Executive narrative synthesis and multi-format brief compilation.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```
Set the FastAPI backend URL (defaults to `http://localhost:8000`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Build for Production
```bash
npm run build
npm start
```

---

## 🌟 Pages and Key Features

| Page | Route | Description |
|---|---|---|
| **Dashboard** | `/` | Executive AI briefing, 4 primary KPI cards with period trends & sparkline telemetry, interactive Revenue Area Chart with range filters (7D/30D/90D/1Y), Sales by Category progress bars, and recent agent actions feed. |
| **AI Analytics** | `/analytics` | Natural language business inquiry console ("Why did sales decrease last month?"). Renders diagnostic findings, impact charts, tabular comparisons, and suggested follow-ups. |
| **Data Upload** | `/upload` | Drag-and-drop CSV/Excel file ingestion with in-browser schema detection, outlier validation, progress tracking, and sample dataset one-click loader. |
| **AI Agents** | `/agents` | Status dashboard for the 4 autonomous agents. Includes pipeline visualizer, honest backend connectivity status, simulation toggle, and real-time execution log terminal. |
| **Reports** | `/reports` | Filterable executive intelligence report gallery with keyword search, interactive modal preview, and multi-format export (JSON, Text/Markdown). |
| **Settings** | `/settings` | User profile configuration, default currency, LLM reasoning backbone selection, and live FastAPI backend ping test tool. |

---

## 🔌 FastAPI Backend Integration

All API calls are cleanly abstracted inside [`src/services/api.ts`](./src/services/api.ts).

### Endpoints Contract
When your FastAPI backend is online, the frontend automatically routes to these endpoints:
- `GET /health` -> `{ "status": "ok", "version": "1.0.0", "database": "connected" }`
- `GET /api/dashboard/kpis?range={range}` -> Returns array of `KpiMetric` from MySQL
- `GET /api/agents` -> Returns array of `AgentInfo` from MySQL
- `POST /api/analytics/ask` -> Body: `{ "query": string, "range": "30d" }` -> Returns grounded `AnalyticsAskResponse` with Gemini reasoning, KPI metrics, chart data, and data source telemetry.

---

## 🤖 Milestone 4: Gemini-Powered AI Analytics

InsightFlow AI pairs Google Gemini with strict deterministic data boundaries to generate trustworthy, grounded business intelligence:

### Architecture & Request Flow
```text
Frontend (AI Analytics Page)
       │
       ▼  POST /api/analytics/ask
FastAPI Endpoint (Pydantic validation)
       │
       ▼  Read-only analytical retrieval (NO arbitrary SQL from LLM)
MySQL Database (insightflow_db: kpi_metrics, ai_agents)
       │
       ▼  Grounded business context + User prompt
Google Gemini API (google-genai SDK, gemini-2.5-flash)
       │
       ▼  Structured JSON synthesis (findings, metrics, charts, follow-ups)
FastAPI Backend (source attribution + latency telemetry)
       │
       ▼  AnalyticsAskResponse
Frontend (Live/Mock pill, metric pills, interactive charts, follow-up chips)
```

### Security & Safety Rules
1. **Zero Model SQL Execution:** The LLM is never allowed to generate or execute arbitrary SQL statements. Only approved, read-only Python/SQLAlchemy functions retrieve database metrics.
2. **Key Isolation:** `GEMINI_API_KEY` is maintained strictly inside `backend/.env` and is never transmitted or exposed to the client-side Next.js bundle.
3. **Resilient Fallback:** If `GEMINI_API_KEY` is missing or the external API is unreachable, the system gracefully falls back to deterministic rule-based grounding without crashing.

---

## 🐍 Backend Setup (FastAPI & MySQL 8)

### 1. Requirements & Virtual Environment
- Python 3.10+
- MySQL 8.0 running on `localhost:3306` with database `insightflow_db`
- `google-genai` Python SDK

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `backend/.env.example` to `backend/.env` and update your MySQL and Gemini credentials:
```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=insightflow_db
DATABASE_URL=mysql+pymysql://root:your_mysql_password@127.0.0.1:3306/insightflow_db
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 3. Start the Backend Server
```bash
# From workspace root
backend\.venv\Scripts\uvicorn app.main:app --app-dir backend --reload --port 8000
```
API Documentation will be live at [http://localhost:8000/docs](http://localhost:8000/docs).

### 4. Run the Test Suite
Tests run completely isolated using in-memory SQLite and mocked Gemini client, requiring zero live API keys:
```bash
backend\.venv\Scripts\pytest backend/tests -v
```

---

## 📚 Milestone 7: Production-Ready RAG Pipeline

InsightFlow AI includes a production-ready Retrieval-Augmented Generation (RAG) pipeline designed for business knowledge management (SLAs, contracts, financial policies, regional sales data).

### RAG Architecture & Data Flow

```text
[ Business Documents ] (PDF, TXT, CSV)
          │
          ▼
1. Validation & Safe Ingestion (MIME / Ext check, safe filename, 20MB limit)
          │
          ▼
2. Text & Metadata Extraction (TextExtractor: page numbers for PDF, row ranges for CSV)
          │
          ▼
3. Boundary Chunking (DocumentChunker: sliding window 500 chars, 50 chars overlap)
          │
          ▼
4. Vector Embeddings (Gemini text-embedding-004 / 384-dim Dense Hashing Fallback)
          │
          ▼
5. Persistent Vector Store (SqlVectorStore: DocumentModel + DocumentChunkModel in MySQL/SQLite)
          │
     ┌────┴───────────────────────────────┐
     │                                    │
     ▼                                    ▼
[ Standalone RAG Query ]         [ LangGraph Analytics Workflow ]
POST /api/rag/ask                POST /api/analytics/ask
  │                                │
  ▼                                ▼
Cosine Vector Ranking            Stage 1: KPI Analyst (Retrieves docs if query asks)
  │                                │
  ▼                                ▼
Gemini 2.0 / Rule Fallback       Stage 2: Anomaly Detection
  │                                │
  ▼                                ▼
Grounded Answer + Citations      Stage 3: Grounded Recommendations + Citations
```

### RAG Features & Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | Ingests `.pdf`, `.txt`, `.csv` document, splits into chunks, and indexes vectors. |
| `GET` | `/api/documents` | Lists all indexed documents, status, chunk counts, and file sizes. |
| `DELETE` | `/api/documents/{document_id}` | Cascading deletion removing document and all associated chunk vectors. |
| `POST` | `/api/rag/ask` | Accepts natural language question; retrieves top-k chunks and returns grounded answer with citations. |
| `GET` | `/api/rag/health` | Returns RAG component readiness, vector store type, and indexed chunk counts. |

### API Usage Examples

#### 1. Ingest Document
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@terms_of_service.txt;type=text/plain"
```
**Response:**
```json
{
  "documentId": "doc_a1b2c3d4e5f6",
  "filename": "terms_of_service.txt",
  "contentType": "text/plain",
  "fileSize": 1024,
  "chunkCount": 3,
  "status": "indexed",
  "message": "Document 'terms_of_service.txt' successfully ingested and indexed into 3 vector chunks."
}
```

#### 2. Query Knowledge Base with Citations
```bash
curl -X POST "http://localhost:8000/api/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are our payment terms and SLA credits?",
    "topK": 4,
    "includeKpiContext": true
  }'
```
**Response:**
```json
{
  "id": "rag_98a72b10",
  "query": "What are our payment terms and SLA credits?",
  "answer": "According to the Service Level Agreement, invoices are payable net 30 days...",
  "citations": [
    {
      "documentId": "doc_a1b2c3d4e5f6",
      "documentName": "terms_of_service.txt",
      "pageNumber": 1,
      "chunkIndex": 0,
      "snippet": "Invoices are payable net 30 days from billing date...",
      "relevanceScore": 0.884
    }
  ],
  "grounded": true,
  "model": "gemini-2.5-flash",
  "latencyMs": 185.4
}
```

### Supported Document Formats & Limitations
- **PDF (`.pdf`)**: Extracts page text via `pypdf`. Citations reference exact page numbers.
- **TXT (`.txt`)**: Extracts UTF-8 raw policy/documentation text.
- **CSV (`.csv`)**: Parses tabular records with row range metadata.
- **Max File Size**: 20MB per document.
- **Security**: Uploaded content is wrapped in `<document_evidence>` XML boundaries in LLM prompts to prevent prompt injection and untrusted instruction execution.

---

## 📈 Milestone 8: Predictive Analytics and Sales Forecasting

InsightFlow AI includes an empirical, production-ready predictive analytics module that forecasts sales revenue and order volume using historical database time series without fabricating artificial predictions.

### Forecasting Architecture & Data Flow

```text
[ MySQL Database: daily_metrics ]
          │
          ▼
1. Data Preparation & Validation (ForecastingService.prepare_clean_series)
   - Checks minimum 14 daily observations threshold
   - Continuous calendar gap-filling (forward interpolation)
   - Deduplication and chronology sorting
          │
          ▼
2. Chronological Holdout Split (Strict No Data Leakage)
   - Training Set: 75% - 80% chronological history
   - Holdout Test Set: 20% - 25% (e.g. last 7 to 14 days)
          │
          ▼
3. Multi-Model Benchmark Fitting
   - Model 1: Naive Baseline (Last observed value)
   - Model 2: Moving Average (7-day SMA)
   - Model 3: Linear Trend Regression (OLS with exact prediction SE)
   - Model 4: Double Exponential Smoothing (Holt's Linear Trend)
          │
          ▼
4. Out-of-Sample Evaluation & Model Selection
   - Calculates holdout MAE, RMSE, and MAPE (zero-safeguarded)
   - Selects Champion model with lowest holdout RMSE
          │
          ▼
5. Horizon Projection & Prediction Bands
   - Refits Champion model on 100% of historical series
   - Forecasts h-day points (7, 14, 30, or 60 days)
   - Generates expanding prediction intervals (80% and 95% confidence bounds)
          │
          ▼
6. Business Recommendations & Persistence
   - Trend direction ('up', 'down', 'flat') and projected growth %
   - Grounded operational recommendations tailored to forecast slope
   - Stored in forecast_runs table for historical audit & accuracy evaluation
```

### Forecasting API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/forecast/availability?metric=revenue` | Verifies whether minimum 14 daily historical records exist for empirical modeling. |
| `POST` | `/api/forecast/generate` | Generates h-day forecast, runs multi-model holdout tournament, produces prediction intervals and recommendations. |
| `GET` | `/api/forecast/history?limit=20` | Returns logged historical forecast runs and their out-of-sample accuracy metrics. |
| `GET` | `/api/forecast/evaluate?run_id={id}` | Audits past forecast projections against subsequently observed actual values in the database. |

### API Usage Examples

#### 1. Check Data Availability
```bash
curl "http://localhost:8000/api/forecast/availability?metric=revenue"
```
**Response:**
```json
{
  "hasSufficientData": true,
  "message": "Sufficient historical data available for 'revenue': 87 daily observations from 2026-08-01 to 2026-10-26.",
  "totalObservations": 87,
  "minDate": "2026-08-01",
  "maxDate": "2026-10-26",
  "supportedMetrics": ["revenue", "orders"],
  "requiredObservations": 14
}
```

#### 2. Generate 14-Day Sales Forecast
```bash
curl -X POST "http://localhost:8000/api/forecast/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "metricName": "revenue",
    "horizonDays": 14,
    "confidenceLevel": 0.95
  }'
```
**Response:**
```json
{
  "runId": "fc_626513adb5fe",
  "metricName": "revenue",
  "horizonDays": 14,
  "selectedModel": "Holt'\''s Exponential Smoothing",
  "outOfSampleMetrics": {
    "mae": 5420.5,
    "rmse": 6840.2,
    "mape": 9.4
  },
  "trendDirection": "up",
  "projectedGrowthRate": 16.8,
  "forecastPoints": [
    {
      "date": "2026-10-27",
      "forecast": 61200.0,
      "lowerBound": 53400.0,
      "upperBound": 69000.0
    }
  ],
  "recommendations": [
    "Sustained Upward Momentum: Projected Revenue trajectory is expanding at +16.8% over the next 14 days...",
    "Infrastructure Capacity: Scale API gateway compute quotas and cloud database replicas ahead of peak load."
  ]
}
```

### Manual Verification
1. Navigate to `/forecast` in your web browser.
2. Toggle between **Revenue ($)** and **Order Volume**.
3. Choose your desired horizon (`7 Days`, `14 Days`, `30 Days`) and confidence level (`95%`, `80%`).
4. Click **Run Empirical Forecast** to view the dual-series chart, candidate model tournament metrics, and business recommendations.
5. In the **Saved Forecast Runs** table, click **Evaluate** on any past run to compare predictions against realized actuals.


#   I n s i g h t F l o w - A I  
 