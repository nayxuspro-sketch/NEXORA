import uuid


def parse_safe_uuid(val):
    """
    Safely validates if a value is a valid UUID string.
    Returns the parsed UUID object or string, or None if invalid or placeholder.
    """
    if not val or not isinstance(val, (str, uuid.UUID)):
        return None
    try:
        return uuid.UUID(str(val).strip())
    except (ValueError, AttributeError, TypeError):
        return None
