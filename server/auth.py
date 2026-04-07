"""
Authentication (verify the user) and authorisation (determines permissions of the users) logic for the backend API

-When accounts are created users passwords are hashed
-Verify passwords from user logins
-Generate JWT access tokens (user login successful)
-Client tokens validatation
-Protection for API routes through dependency functions

:User Registration:
 -> User input email address + password -> password is hashed -> store in database

:User Login: 
 -> User inputs email address + password -> verify password -> JWT token returned

:API Requests:
 Client will send request -> Authorisation: Bearer <token>

 API extracts the token -> verfiy token -> Retrieve stored user identity
 Access only allowed by a valid token

:Admin Routes: 
 Additional permisions e.g. admin role
 routes dictated by require_admin() function 
"""

#Standard Libraries
from datetime import datetime, timedelta, timezone
from typing import Optional 
#Third Party Libraries
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

#Security Configuration
SECRET_KEY = "Must-change-to-long-random-jumble"

#HS256 will be used for the crptographic algorithm for signing tokens
ALGORITHM = "HS256"

#Access token Expirey, limits how long a login token is valid
ACCESS_TOKEN_EXPIRE_MINUTES = 60

#Password hashing, argon2 will be used for hashing algorithm
password_hash = PasswordHash.recommended()

#Token Extraction, OAuth2PasswordBearer tells fast API the tokens origin, clients will send token
#FastAPI will extract the token and pass to functions with dependence from oauth2_scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#Pasword Utilities
def hash_password(password: str) -> str:
    #hashes the plain text password, when new user registers
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    #verifies if the login password matches the stored hash
    return password_hash.verify(plain_password, hashed_password)

#token creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    #creates signed JWT access token (User identity, role info, expiration)
    
    #copy input data from original dictionary
    to_encode = data.copy()
    #Determine token expiration time
    expire= datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    #add expiration to token
    to_encode.update({"exp": expire})
    #encode and sign the token using our key
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

#Token Validation 
def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
#Current User Dependency
def get_current_user(token: str = Depends(oauth2_scheme)):
    #All routes which include current_user = Depends(get_current_user) will require a valid token by default
    payload = decode_access_token(token)
    #sub should contain the user identifier
    email = payload.get("sub")

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user identifier",
            headers={"WWW-Authenticate": "Bearer"}
        )
    #REMINDER IN FUTURE WILL QUERY THE DATABASE FOR NOW SIMPLE DICTIONARY

    user = {
        "email": email,
        "role": payload.get("role", "user")
    }
    
    return user

#Admin authorisation check
def require_admin(current_user: dict = Depends(get_current_user)):
    #Check if current user has admin perms
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    
    return current_user 
