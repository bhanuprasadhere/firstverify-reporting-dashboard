"""
Database connection and utilities for MS SQL Server.
"""
import os
import pyodbc
from typing import List, Dict, Any


class DatabaseConnection:
    """Handles MS SQL Server connections and queries."""

    def __init__(self):
        """Initialize database connection parameters."""
        self.server = os.getenv("DB_SERVER")
        self.database = os.getenv("DB_DATABASE")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

        # Validate configuration on initialization
        if not self.server or not self.database:
            raise ValueError(
                "Database configuration missing in .env file. "
                "Please ensure DB_SERVER and DB_DATABASE are set."
            )

    def get_connection(self):
        """Create and return a database connection.

        Raises:
            ValueError: If database configuration is incomplete
            pyodbc.Error: If connection fails
        """
        if not self.server or not self.database:
            raise ValueError(
                "Database configuration missing. "
                "Ensure DB_SERVER and DB_DATABASE are set in .env file."
            )

        try:
            # Build connection string
            # Server value may contain backslash (e.g., localhost\SQLEXPRESS)
            if self.username and self.password:
                # SQL Server authentication
                conn_str = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                )
            else:
                # Windows authentication (Trusted Connection)
                conn_str = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server};"
                    f"DATABASE={self.database};"
                    f"Trusted_Connection=yes;"
                )

            return pyodbc.connect(conn_str)
        except pyodbc.Error as e:
            raise ValueError(
                f"Failed to connect to database server '{self.server}', "
                f"database '{self.database}'. Error: {str(e)}"
            )

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dictionaries.

        Args:
            query: SQL query string
            params: Optional tuple of query parameters

        Returns:
            List of dictionaries representing rows
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Get column names
            columns = [description[0] for description in cursor.description]

            # Fetch all rows and convert to dictionaries
            rows = cursor.fetchall()
            results = [dict(zip(columns, row)) for row in rows]

            cursor.close()
            connection.close()

            return results
        except Exception as e:
            print(f"Database error: {str(e)}")
            raise

    def get_metadata(self) -> List[str]:
        """
        Fetch all unique QuestionText values that have actual data.

        Only returns questions that exist in PrequalificationEMRStatsValues,
        ensuring no empty questions are shown.

        Returns:
            List of unique question texts (ordered alphabetically)
        """
        query = """
        SELECT DISTINCT LEFT(q.QuestionText, 120) AS QuestionText
        FROM dbo.Questions q
        INNER JOIN dbo.PrequalificationEMRStatsValues pesv 
            ON q.QuestionID = pesv.QuestionId
        WHERE q.QuestionText IS NOT NULL 
            AND LEN(TRIM(q.QuestionText)) > 0
        ORDER BY QuestionText ASC
        """
        try:
            results = self.execute_query(query)
            questions = [row['QuestionText'] for row in results]
            return questions
        except Exception as e:
            print(f"Error fetching metadata: {str(e)}")
            raise
