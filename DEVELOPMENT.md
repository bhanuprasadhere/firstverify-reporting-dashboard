# Development Notes

## Architecture

### Backend Architecture
```
FastAPI Server
├── Route: GET /
│   └── Returns static/index.html
├── Route: GET /api/metadata
│   └── DatabaseConnection.get_metadata()
│       └── SELECT DISTINCT QuestionText FROM...
├── Route: POST /api/generate-report
│   ├── PivotSQLGenerator.generate_sql(questions)
│   └── DatabaseConnection.execute_query(sql)
└── Route: GET /api/health
    └── Test database connection
```

### Frontend Architecture
```
ReportingApp (Main Controller)
├── init()
│   ├── setupEventListeners()
│   ├── loadMetadata()
│   └── renderQuestions()
├── generateReport()
│   ├── Validate selections
│   ├── POST /api/generate-report
│   └── renderTable()
├── renderTable()
│   ├── Paginate rows
│   └── Build HTML table
├── exportToExcel()
│   └── XLSX.writeFile()
└── Pagination controls
```

## Key Design Decisions

### 1. PIVOT SQL Generation
- **Client-side selection** → Server-side SQL generation
- **Avoids** storing pre-built report combinations
- **Flexible** - adds new questions automatically
- **Secure** - brackets prevent SQL injection

### 2. Column Aliases
- Stored in `HEADER_ALIASES` dictionary
- Separates database names from UI display
- Easy to maintain and extend

### 3. Pagination
- **Client-side** pagination (not database OFFSET/FETCH)
- All data loaded from API once
- Better UX, simpler implementation
- ⚠️ **Note**: For datasets >10k rows, switch to server-side pagination

### 4. Vanilla JavaScript
- No build tool required
- Simple frontend logic
- Bootstrap 5 for styling
- SheetJS CDN for Excel export

## Error Handling Flow

```
User Action
    ↓
JavaScript Try/Catch
    ↓
    ├─ Error? → showAlert() → setTimeout(remove, 5s)
    └─ Success? → update UI
    
Server Exception
    ├─ Validation (400)
    │   └── "At least one question must be selected"
    ├─ Database (500)
    │   └── Connection, timeout, SQL errors
    └─ HTTP (500)
        └── Server errors, unhandled exceptions
```

## Database Schema Requirements

### Required Tables
```sql
-- Main prequalification records
CREATE TABLE Prequalification (
    PrequalificationId INT PRIMARY KEY,
    VendorId INT,
    PrequalificationStatusId INT
);

-- Vendors/Organizations
CREATE TABLE Organizations (
    OrganizationID INT PRIMARY KEY,
    Name VARCHAR(255)
);

-- Question definitions
CREATE TABLE Questions (
    QuestionID INT PRIMARY KEY,
    QuestionText VARCHAR(MAX)
);

-- Question responses (EAV pattern)
CREATE TABLE PrequalificationEMRStatsValues (
    PrequalEMRStatsValueId INT PRIMARY KEY,
    PrequalEMRStatsYearId INT,
    QuestionId INT,
    QuestionColumnIdValue DECIMAL(18,2)
);

-- Year tracking
CREATE TABLE PrequalificationEMRStatsYears (
    PrequalEMRStatsYearId INT PRIMARY KEY,
    PrequalificationId INT,
    EMRStatsYear VARCHAR(4)
);

-- Optional: User EMR values
CREATE TABLE PrequalificationUserInput (
    PrequalificationUserInputId INT PRIMARY KEY,
    PreQualificationId INT,
    QuestionColumnId INT,
    UserInput DECIMAL(18,2)
);

-- Optional: Question column mapping
CREATE TABLE QuestionColumnDetails (
    QuestionColumnId INT PRIMARY KEY,
    QuestionId INT
);
```

## Testing

### Manual API Testing
```bash
# Test metadata endpoint
curl -X GET http://127.0.0.1:8000/api/metadata | jq

# Test report generation
curl -X POST http://127.0.0.1:8000/api/generate-report \
  -H "Content-Type: application/json" \
  -d '{"selected_questions": ["TRIR:", "EMR:"]}' | jq

# Test health
curl -X GET http://127.0.0.1:8000/api/health | jq
```

### Frontend Testing
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network tab for API calls
4. Test pagination with different page sizes
5. Test export functionality

### Database Testing
```python
from app.database import DatabaseConnection

db = DatabaseConnection()

# Test metadata
questions = db.get_metadata()
print(f"Found {len(questions)} questions")

# Test report
from app.pivot_generator import PivotSQLGenerator
sql = PivotSQLGenerator.generate_sql(["TRIR:", "EMR:"])
results = db.execute_query(sql)
print(f"Report rows: {len(results)}")
```

## Performance Optimization Strategies

### 1. Query Optimization
- Add index on PrequalificationEMRStatsValues(QuestionId, PrequalEMRStatsYearId)
- Add index on Questions(QuestionID, QuestionText)
- Consider materialized view for frequently used combinations

### 2. Caching
- Cache metadata for 1 hour (rarely changes)
- Store recently generated reports in memory
- Implement Redis for distributed caching

### 3. Server-Side Pagination
For datasets >10,000 rows:
```python
@app.post("/api/generate-report")
async def generate_report(request: ReportRequest, page: int = 1, page_size: int = 10):
    # Calculate OFFSET/FETCH in SQL
    # Return paginated results + total_rows
    pass
```

### 4. Frontend Optimization
- Lazy-load question checkboxes if >1000 questions
- Implement virtual scrolling for large tables
- Debounce search/filter operations

## Security Considerations

### ✅ Current Protections
- Brackets around column names prevent SQL injection
- Pydantic validation on inputs
- CORS can be added if needed
- Environment variables for credentials

### ⚠️ Future Security
- Add user authentication (OAuth2/JWT)
- Implement role-based access control
- Add request rate limiting
- Log all report generations (audit trail)
- Validate user access to specific vendors
- Use SQL Server encryption (TDE)

## Deployment Checklist

- [ ] Create production `.env` with real credentials
- [ ] Test database connection from production server
- [ ] Run `pip install --upgrade pip`
- [ ] Create requirements.txt lock file: `pip freeze > requirements.txt`
- [ ] Test all API endpoints
- [ ] Load test with concurrent users
- [ ] Setup monitoring/logging
- [ ] Configure SSL/TLS
- [ ] Setup automated backups
- [ ] Create runbook for common issues

## Monitoring

### Metrics to Track
- API response time (target: <2s for typical report)
- Database query execution time
- Error rate (target: <0.1%)
- Active users
- Report generation frequency

### Logging
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Metadata fetched: 42 questions")
logger.error(f"Database connection failed: {error}")
```

Configure in production with ELK stack or Application Insights.

## Roadmap (V2.0+)

### Q1 2026
- Authentication system
- Saved reports/favorites
- Advanced filtering UI

### Q2 2026
- Multi-vendor comparison
- Charts and visualizations
- Scheduled report delivery

### Q3 2026
- Mobile-responsive improvements
- Performance optimization
- Caching layer

### Q4 2026
- Report templates
- Custom calculations/formulas
- API rate limiting

---

Last Updated: January 2026
