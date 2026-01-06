"""
FastAPI backend for FirstVerify Dynamic Reporting Engine (V1.0)
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import logging
from pathlib import Path

from app.database import DatabaseConnection
from app.pivot_generator import PivotSQLGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FirstVerify Dynamic Reporting Engine",
    description="Dynamic PIVOT report generation from MS SQL Server",
    version="1.0.0"
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Initialize database connection
db = DatabaseConnection()

# ==================== Models ====================


class ReportRequest(BaseModel):
    """Request model for report generation."""
    selected_questions: List[str]


class ReportResponse(BaseModel):
    """Response model for generated report."""
    columns: List[str]
    column_aliases: Dict[str, str]
    rows: List[Dict[str, Any]]
    total_rows: int

# ==================== Routes ====================


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard HTML."""
    index_path = Path(__file__).parent.parent / "static" / "index.html"
    if index_path.exists():
        with open(index_path, "r") as f:
            return f.read()
    return "<h1>Dashboard not found</h1>"


@app.get("/api/metadata", tags=["Metadata"])
async def get_metadata():
    """
    Fetch all unique QuestionText values from the database.

    Used by frontend to dynamically generate question checkboxes.

    Returns:
        List of unique question texts
    """
    try:
        questions = db.get_metadata()
        logger.info(f"Metadata fetched: {len(questions)} questions available")
        return {
            "questions": questions,
            "count": len(questions)
        }
    except Exception as e:
        logger.error(f"Error fetching metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-report", tags=["Reports"])
async def generate_report(request: ReportRequest):
    """
    Generate a PIVOT report based on selected questions.

    Args:
        request: ReportRequest containing selected_questions array

    Returns:
        ReportResponse with generated data and column mappings
    """
    try:
        # Validate input
        if not request.selected_questions:
            raise ValueError("At least one question must be selected")

        # Generate SQL query
        query = PivotSQLGenerator.generate_sql(request.selected_questions)
        logger.info(
            f"Generated PIVOT query for {len(request.selected_questions)} questions")

        # Execute query
        rows = db.execute_query(query)

        # Get column names from first row if available
        columns = list(rows[0].keys()) if rows else []

        # Generate column aliases for UI
        column_aliases = PivotSQLGenerator.get_column_aliases(
            request.selected_questions)

        response = ReportResponse(
            columns=columns,
            column_aliases=column_aliases,
            rows=rows,
            total_rows=len(rows)
        )

        logger.info(f"Report generated: {len(rows)} rows returned")
        return response

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Attempt database connection to verify connectivity
        db.execute_query("SELECT 1 AS test")
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }, 503

# ==================== Error Handlers ====================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )
