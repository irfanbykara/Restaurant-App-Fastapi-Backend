from passlib.context import CryptContext
from fastapi import Depends
from . import oauth2

pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash(password:str):
    return pwd_context.hash(password)

def verify(plain_password,hashed_password):
    return pwd_context.verify(plain_password,
                              hashed_password)


def provider_validator(current_user:int=Depends(oauth2.get_current_user)):
    if current_user.is_provider == True:
        return True
    else:
        return False