from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """Returnează hash-ul parolei."""
    return generate_password_hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    """Verifică parola primita fata de hash."""
    return check_password_hash(password_hash, password)
