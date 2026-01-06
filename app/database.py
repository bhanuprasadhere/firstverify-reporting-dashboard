"""
Database connection and utilities for MS SQL Server.
"""
import os
import pyodbc
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    """Handles MS SQL Server connections and queries."""

    def __init__(self):
        """Initialize database connection parameters."""
        self.server = os.getenv("DB_SERVER")
        self.database = os.getenv("DB_DATABASE")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

    def get_connection(self):
        """Create and return a database connection."""
        connection_string = (
            f"Driver={{{self.driver}}};"
            f"Server={self.server};"
            f"Database={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
        )
        return pyodbc.connect(connection_string)

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
        Fetch all unique QuestionText values from PrequalificationEMRStatsValues.

        Returns:
            List of unique question texts
        """
        query = """
        SELECT DISTINCT LEFT(q.QuestionText, 120) AS QuestionText
        FROM PrequalificationEMRStatsValues pesv
        JOIN Questions q ON q.QuestionID = pesv.QuestionId
        WHERE q.QuestionText IS NOT NULL
        ORDER BY QuestionText
        """
        results = self.execute_query(query)
        return [row['QuestionText'] for row in results]
