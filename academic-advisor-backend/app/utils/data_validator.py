from typing import Any, Dict

class DataValidator:
    """
    Utility class for validating incoming data structures.
    """

    @staticmethod
    def require_fields(data: Dict[str, Any], required_fields: list[str]) -> None:
        """
        Ensure that all required fields are present in the data dict.
        Raises ValueError if any are missing.
        """
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

    @staticmethod
    def not_empty(value: Any, field_name: str) -> None:
        """
        Ensure a field is not empty.
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"Field '{field_name}' cannot be empty")
