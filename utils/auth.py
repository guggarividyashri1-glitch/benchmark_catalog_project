from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

SECRET = "benchmark_secret"
ALGORITHM = "HS256"

security = HTTPBearer()
def create_token(role: str):

    payload = {"role": role}

    token = jwt.encode(payload, SECRET, algorithm=ALGORITHM)

    return token


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload

    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")

def admin_only(user=Depends(verify_token)):

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return user

def user_or_admin(user=Depends(verify_token)):

    if user["role"] not in ["user", "admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return user


def user_only(user=Depends(verify_token)):

    if user["role"] != "user":
        raise HTTPException(status_code=403, detail="User access required")

    return user