# API Reference - FirstVerify Dynamic Reporting Engine

## Base URL
```
http://127.0.0.1:8000
```

## Authentication
None (will be added in V2.0)

---

## Endpoints

### 1. Dashboard
Get the main HTML dashboard

**Request:**
```http
GET / HTTP/1.1
Host: 127.0.0.1:8000
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>...</html>
```

---

### 2. Metadata
Fetch all available questions from the database

**Request:**
```http
GET /api/metadata HTTP/1.1
Host: 127.0.0.1:8000
```

**Response:**
```json
{
  "questions": [
    "TRIR:",
    "EMR:",
    "Experience Modification Rate (EMR):",
    "Total Recordable Incident Rate (TRIR):",
    "Days Away Restricted or Job Transfer (DART):",
    "Near Miss Reports:",
    "Safety Training Hours:",
    "Incident Rate Trend:",
    "Compliance Score:",
    "Risk Assessment Total:"
  ],
  "count": 10
}
```

**Status Codes:**
- `200` - Success
- `500` - Database error

**Example cURL:**
```bash
curl -X GET http://127.0.0.1:8000/api/metadata
```

**Example JavaScript:**
```javascript
fetch('/api/metadata')
  .then(response => response.json())
  .then(data => console.log(data.questions))
  .catch(error => console.error('Error:', error));
```

---

### 3. Generate Report
Generate a PIVOT report based on selected questions

**Request:**
```http
POST /api/generate-report HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "selected_questions": [
    "TRIR:",
    "EMR:",
    "Days Away Restricted or Job Transfer (DART):"
  ]
}
```

**Response:**
```json
{
  "columns": [
    "Vendor",
    "EMRStatsYear",
    "EMR",
    "TRIR:",
    "Days Away Restricted or Job Transfer (DART):"
  ],
  "column_aliases": {
    "TRIR:": "TRIR",
    "EMR:": "EMR",
    "Days Away Restricted or Job Transfer (DART):": "DART"
  },
  "rows": [
    {
      "Vendor": "Company A",
      "EMRStatsYear": "2023",
      "EMR": "0.85",
      "TRIR:": "2.5",
      "Days Away Restricted or Job Transfer (DART):": "1.2"
    },
    {
      "Vendor": "Company A",
      "EMRStatsYear": "2022",
      "EMR": "0.92",
      "TRIR:": "2.8",
      "Days Away Restricted or Job Transfer (DART):": "1.5"
    },
    {
      "Vendor": "Company B",
      "EMRStatsYear": "2023",
      "EMR": "0.78",
      "TRIR:": "2.1",
      "Days Away Restricted or Job Transfer (DART):": "0.9"
    }
  ],
  "total_rows": 3
}
```

**Status Codes:**
- `200` - Report generated successfully
- `400` - Bad request (no questions selected, invalid input)
- `500` - Database error (SQL error, connection timeout)

**Error Response Example:**
```json
{
  "detail": "At least one question must be selected"
}
```

**Constraints:**
- Minimum 1 question, no maximum limit (recommended <20 for performance)
- Question text must match exactly what's in metadata
- Will be truncated to 120 characters in PIVOT

**Example cURL:**
```bash
curl -X POST http://127.0.0.1:8000/api/generate-report \
  -H "Content-Type: application/json" \
  -d '{
    "selected_questions": ["TRIR:", "EMR:"]
  }'
```

**Example JavaScript:**
```javascript
const questions = ["TRIR:", "EMR:"];

fetch('/api/generate-report', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    selected_questions: questions
  })
})
  .then(response => response.json())
  .then(data => {
    console.log(`Report has ${data.total_rows} rows`);
    console.log(data.rows);
  })
  .catch(error => console.error('Error:', error));
```

**Example Python:**
```python
import requests

url = "http://127.0.0.1:8000/api/generate-report"
payload = {
    "selected_questions": ["TRIR:", "EMR:"]
}

response = requests.post(url, json=payload)
report_data = response.json()

print(f"Total rows: {report_data['total_rows']}")
for row in report_data['rows']:
    print(row)
```

---

### 4. Health Check
Verify API and database connectivity

**Request:**
```http
GET /api/health HTTP/1.1
Host: 127.0.0.1:8000
```

**Response (Success):**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

**Response (Error):**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "Unable to connect to server"
}
```

**Status Codes:**
- `200` - Healthy (database connected)
- `503` - Unhealthy (database disconnected)

**Example cURL:**
```bash
curl -X GET http://127.0.0.1:8000/api/health
```

---

## Data Types

### Question Object
```typescript
interface Question {
  text: string;        // Question text as stored in database
  alias?: string;      // Short name for UI display (optional)
  count?: number;      // Number of vendors with this question
}
```

### Report Object
```typescript
interface ReportResponse {
  columns: string[];                    // Column names in order
  column_aliases: Record<string, string>;  // Maps full names to short names
  rows: Array<Record<string, any>>;    // Data rows
  total_rows: number;                  // Total number of rows
}
```

### Row Object
```typescript
interface ReportRow {
  [columnName: string]: string | number | null;
  Vendor: string;           // Organization name
  EMRStatsYear: string;     // Year (e.g., "2023")
  EMR?: number;             // Numeric EMR value
  [questionName: string]: any;  // Dynamic columns based on selection
}
```

---

## Error Handling

### Common Errors

**400 Bad Request**
```json
{
  "detail": "At least one question must be selected"
}
```
**Cause:** Empty selected_questions array
**Solution:** Select at least one question

**500 Internal Server Error - Database Connection**
```json
{
  "detail": "Unable to connect to database: (pyodbc.Error) error details"
}
```
**Cause:** Database connection failed
**Solution:** Check .env credentials and SQL Server is running

**500 Internal Server Error - SQL Error**
```json
{
  "detail": "SQL Error: Incorrect syntax near..."
}
```
**Cause:** Invalid PIVOT syntax
**Solution:** Ensure question names are correct and <120 chars

**503 Service Unavailable**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "Connection timeout"
}
```
**Cause:** Database temporarily unavailable
**Solution:** Check SQL Server status, retry in 30 seconds

---

## Rate Limiting

Currently: No rate limiting

Future (V2.0): 
- 100 requests per minute per IP
- 1000 requests per day per user

---

## Pagination

**Frontend Pagination** (Client-side):
- All data loaded from API once
- Paginated in browser
- Supports: 10, 25, 50, 100 rows per page

**Future Server-Side Pagination** (V2.0):
```json
{
  "page": 1,
  "page_size": 10,
  "total_rows": 1250,
  "total_pages": 125
}
```

---

## Filtering & Sorting

**Current Implementation:**
- Sorting: By Vendor and EMRStatsYear (SQL template)
- Filtering: By PrequalificationStatusId (8,9,13,26,31)
- Date Range: Years > 2012

**Future Features (V2.0):**
- User-defined sort order
- Vendor filtering
- Year range selection
- Custom filters

---

## Performance Considerations

### Response Times (Approximate)
| Operation | Time | Note |
|-----------|------|------|
| Load metadata | 500ms | First load, cached after |
| Small report (5Q, <100 rows) | 2s | Typical use case |
| Medium report (10Q, 500 rows) | 3-5s | Common scenario |
| Large report (20Q, 1000+ rows) | 5-10s | May need pagination |
| Excel export | <1s | Client-side only |

### Optimization Tips
1. **Limit questions**: Fewer questions = faster queries
2. **Narrow date range**: Modify SQL template WHERE clause
3. **Add indices**: On QuestionID, VendorId, EMRStatsYear
4. **Server-side pagination**: For datasets >10k rows (V2.0)

---

## CORS & Cross-Domain

**Current:** No CORS restrictions (same-origin only)

**Future (V2.0):**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
)
```

---

## Versioning

Current API Version: **1.0.0**

Breaking changes will increment major version.

---

## Webhooks & Events

Not implemented in V1.0

Planned for V2.0:
- Report generation notifications
- Scheduled report delivery
- Email integration

---

## Code Examples

### Python - Get Metadata
```python
import requests

url = "http://127.0.0.1:8000/api/metadata"
response = requests.get(url)
questions = response.json()['questions']

for question in questions:
    print(question)
```

### Python - Generate Report
```python
import requests
import pandas as pd

url = "http://127.0.0.1:8000/api/generate-report"
payload = {"selected_questions": ["TRIR:", "EMR:"]}

response = requests.post(url, json=payload)
data = response.json()

# Convert to DataFrame
df = pd.DataFrame(data['rows'])
print(df)
```

### JavaScript - Fetch with Error Handling
```javascript
async function generateReport(questions) {
  try {
    const response = await fetch('/api/generate-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selected_questions: questions })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    const report = await response.json();
    return report;
  } catch (error) {
    console.error('Report generation failed:', error.message);
    return null;
  }
}
```

### PowerShell - Test API
```powershell
$uri = "http://127.0.0.1:8000/api/metadata"
$response = Invoke-RestMethod -Uri $uri -Method Get

$response.questions | ForEach-Object { Write-Host $_ }

# Generate report
$body = @{
    selected_questions = @("TRIR:", "EMR:")
} | ConvertTo-Json

$uri = "http://127.0.0.1:8000/api/generate-report"
$response = Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/json"

Write-Host "Total rows: $($response.total_rows)"
```

---

## Testing

### Health Check
```bash
curl -I http://127.0.0.1:8000/api/health
```

### Load Testing (Apache Bench)
```bash
ab -n 1000 -c 10 http://127.0.0.1:8000/api/metadata
```

### Load Testing (Wrk)
```bash
wrk -t4 -c100 -d30s http://127.0.0.1:8000/api/metadata
```

---

## Support & Documentation

- **Full Docs**: [README.md](README.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Development**: [DEVELOPMENT.md](DEVELOPMENT.md)
- **Interactive Docs**: http://127.0.0.1:8000/docs (Swagger UI)

---

**Last Updated:** January 6, 2026  
**API Version:** 1.0.0  
**Status:** Production Ready ✅
