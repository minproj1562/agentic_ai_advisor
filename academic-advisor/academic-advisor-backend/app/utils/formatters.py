# app/utils/formatters.py
from typing import Any, Dict

class DataFormatter:
    """
    Utility class for formatting data structures for output or storage.
    """

    @staticmethod
    def to_title_case(text: str) -> str:
        """Convert a string to Title Case."""
        return text.title() if text else text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Trim and collapse multiple spaces into one."""
        return " ".join(text.split()) if text else text

    @staticmethod
    def format_student_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Example: normalize and clean up a student record dict.
        """
        return {
            "id": record.get("id"),
            "name": DataFormatter.to_title_case(record.get("name", "")),
            "email": record.get("email", "").lower().strip(),
            "course": DataFormatter.normalize_whitespace(record.get("course", "")),
        }
