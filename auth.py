import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from jose import jwt, JWTError
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment configuration
load_dotenv()

<<<<<<< HEAD
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
=======
SECRET_KEY = os.getenv("SECRET_KEY", "dev_super_secret_key_change_in_production_32bytes_long")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
>>>>>>> de69205539d9494664d09521846b8b2bb4fe602e

def hash_password(password: str) -> str:
    """Hashes a plaintext password using Werkzeug's secure method."""
    return generate_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored hash."""
    return check_password_hash(hashed_password, plain_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token with an expiration timestamp."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
<<<<<<< HEAD
    return encoded_jwt
=======
    return encoded_jwt
>>>>>>> de69205539d9494664d09521846b8b2bb4fe602e
