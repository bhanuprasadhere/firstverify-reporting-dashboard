"""
Dynamic PIVOT SQL generator for the reporting engine.
"""
from typing import List
from datetime import datetime

# Header aliases for shorter UI display
HEADER_ALIASES = {
    "TRIR:": "TRIR",
    "EMR:": "EMR",
    "Experience Modification Rate (EMR):": "EMR",
    "Total Recordable Incident Rate (TRIR):": "TRIR",
}


class PivotSQLGenerator:
    """Generates dynamic PIVOT SQL based on user-selected questions."""

    # Template query with placeholder
    TEMPLATE_QUERY = """
SELECT Vendor, EMRStatsYear, emrVal AS EMR, _ColumnNames
FROM (
    SELECT o.Name AS Vendor, pesv.QuestionColumnIdValue, pesy.EMRStatsYear, LEFT(q.QuestionText, 120) AS QuestionText, emr.emrVal
    FROM Prequalification p 
    JOIN Organizations o ON o.OrganizationID = p.VendorId 
    JOIN PrequalificationEMRStatsYears pesy ON pesy.PrequalificationId = p.PrequalificationId 
    JOIN PrequalificationEMRStatsValues pesv ON pesy.PrequalEMRStatsYearId = pesv.PrequalEMRStatsYearId 
    JOIN Questions q ON q.QuestionID = pesv.QuestionId
    LEFT JOIN (
        SELECT PreQualificationId, MAX(UserInput) AS emrVal 
        FROM PrequalificationUserInput ui
        JOIN QuestionColumnDetails qcol ON qcol.QuestionColumnId = ui.QuestionColumnId
        JOIN Questions q ON q.QuestionID = qcol.QuestionId 
        WHERE q.QuestionText = 'EMR:' 
        GROUP BY PreQualificationId
    ) emr ON emr.PreQualificationId = p.PrequalificationId
    WHERE ISNUMERIC(pesy.EMRStatsYear) = 1 AND p.PrequalificationStatusId IN (8,9,13,26,31)
) AS SourceTable
PIVOT (
    MAX(QuestionColumnIdValue) FOR QuestionText IN (_ColumnNames)
) AS PivotTable 
WHERE CAST(EMRStatsYear AS decimal(18,2)) > 2012 
ORDER BY Vendor, EMRStatsYear;
"""

    @staticmethod
    def format_column_name(question_text: str) -> str:
        """
        Format question text as SQL column reference.

        Args:
            question_text: Raw question text from metadata

        Returns:
            SQL-safe column reference wrapped in brackets
        """
        # Truncate to 120 characters as per requirement
        truncated = question_text[:120] if len(
            question_text) > 120 else question_text
        # Wrap in brackets for SQL safety
        return f"[{truncated}]"

    @staticmethod
    def get_header_alias(question_text: str) -> str:
        """
        Get shortened header alias for UI display.

        Args:
            question_text: Raw question text

        Returns:
            Shortened alias or original text if no alias exists
        """
        for key, alias in HEADER_ALIASES.items():
            if question_text.startswith(key):
                return alias
        # Default: use original text truncated to 30 chars for display
        return question_text[:30]

    @staticmethod
    def generate_sql(selected_questions: List[str]) -> str:
        """
        Generate complete PIVOT SQL query based on selected questions.

        Args:
            selected_questions: List of QuestionText values selected by user

        Returns:
            Complete SQL query string ready for execution

        Raises:
            ValueError: If selected_questions is empty
        """
        if not selected_questions:
            raise ValueError("At least one question must be selected")

        # Format each column name
        formatted_columns = [
            PivotSQLGenerator.format_column_name(question)
            for question in selected_questions
        ]

        # Create PIVOT column list: [Col1], [Col2], ...
        pivot_columns = ", ".join(formatted_columns)

        # Replace placeholder with actual column names
        query = PivotSQLGenerator.TEMPLATE_QUERY.replace(
            "_ColumnNames", pivot_columns)

        return query

    @staticmethod
    def get_column_aliases(selected_questions: List[str]) -> dict:
        """
        Generate mapping of full column names to shortened aliases for frontend.

        Args:
            selected_questions: List of QuestionText values

        Returns:
            Dictionary mapping full names to aliases
        """
        return {
            question: PivotSQLGenerator.get_header_alias(question)
            for question in selected_questions
        }
