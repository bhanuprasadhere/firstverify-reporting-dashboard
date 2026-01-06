# FirstVerify Reporting Engine - Quick Start Guide

## 5-Minute Setup

### 1. Environment Setup (2 min)
```bash
# Copy environment template
copy .env.example .env

# Edit .env with your database details
# DB_SERVER=your-server
# DB_DATABASE=your-database
# DB_USERNAME=your-user
# DB_PASSWORD=your-password
```

### 2. Install Dependencies (1 min)
```bash
pip install -r requirements.txt
```

### 3. Run Application (1 min)
```bash
python -m uvicorn app.main:app --reload
```

### 4. Access Dashboard (1 min)
Open browser: **http://127.0.0.1:8000**

---

## Using the Dashboard

### Step 1: Select Questions
1. Check boxes for the questions you want in the report
2. Use "✓ All" to select all or "✗ Clear" to deselect

### Step 2: Generate Report
1. Click "🔄 Generate Report" button
2. Wait for data to load (loading spinner shows progress)
3. Report table appears with pagination

### Step 3: View Results
- **Scroll left/right** for more columns
- **Page through results** using Previous/Next buttons
- **Change rows per page** with dropdown (10/25/50/100)

### Step 4: Export to Excel
1. Click "📥 Export to Excel" button
2. File downloads as `FirstVerify_Report_YYYY-MM-DD.xlsx`

---

## Common Tasks

### Check API Status
```bash
curl http://127.0.0.1:8000/api/health
```

### Get Available Questions
```bash
curl http://127.0.0.1:8000/api/metadata
```

### Generate Report via API
```bash
curl -X POST http://127.0.0.1:8000/api/generate-report \
  -H "Content-Type: application/json" \
  -d '{"selected_questions": ["TRIR:", "EMR:"]}'
```

---

## Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| "Cannot connect to database" | Check .env credentials and SQL Server is running |
| "No questions appear" | Verify PrequalificationEMRStatsValues table exists |
| "Export button doesn't work" | Check browser console (F12), clear cache |
| "Slow report generation" | Try fewer questions or smaller page size |
| "PIVOT error in SQL" | Ensure question names are 120 chars or less |

---

## File Locations

| File | Purpose |
|------|---------|
| `.env` | Database credentials |
| `app/main.py` | API endpoints |
| `app/database.py` | DB connection logic |
| `app/pivot_generator.py` | SQL generation |
| `static/index.html` | Dashboard UI |
| `static/js/app.js` | Frontend logic |
| `static/css/style.css` | Styling |

---

## Production Deployment

### On Windows Server

1. **Install Python Runtime** (not development version)
2. **Copy project folder** to production server
3. **Create .env** with production credentials
4. **Install dependencies**: `pip install -r requirements.txt`
5. **Create Windows Service** or use task scheduler

### Using Gunicorn (Linux/Mac)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

### Using IIS (Windows)
1. Install Python for Windows
2. Install FastAPI on IIS with HttpPlatformHandler
3. Configure web.config with app.main:app as entry point

---

## Performance Tips

- Default loads **10 rows per page** - adjust in UI
- Keep **question count under 20** for best performance
- **Narrow date range** by modifying SQL template
- **Pre-compute** common report combinations

---

**Need Help?** Check the full [README.md](README.md) for detailed documentation.
