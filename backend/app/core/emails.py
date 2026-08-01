"""Email normalization helpers."""


def normalize_email(email: str) -> str:
    """Strip + lowercase so login/register/reset agree on one identity."""
    return email.strip().lower()
