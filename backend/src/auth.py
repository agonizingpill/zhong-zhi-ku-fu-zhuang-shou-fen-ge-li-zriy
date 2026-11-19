import os,hashlib,hmac,secrets,time
import jwt
from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy import select
from .db import session
from .models import User
bearer=HTTPBearer(auto_error=False)
def hashed(value,salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+':'+hashlib.pbkdf2_hmac('sha256',value.encode(),salt.encode(),100000).hex()
def verify(value,stored):return hmac.compare_digest(hashed(value,stored.split(':')[0]),stored)
def current(auth=Depends(bearer),s=Depends(session)):
    try:
        claim=jwt.decode(auth.credentials,os.environ['JWT_SECRET'],algorithms=['HS256']);u=s.scalar(select(User).where(User.email==claim['sub']))
        if not u:raise ValueError()
        return u
    except Exception:raise HTTPException(401,'请使用岗位账号登录')
def writer(u=Depends(current)):
    if u.role not in ('operator','supervisor'):raise HTTPException(403,'观察员只能读取')
    return u
def supervisor(u=Depends(current)):
    if u.role!='supervisor':raise HTTPException(403,'此动作需要育种主管签署')
    return u
def token(u):return jwt.encode({'sub':u.email,'exp':int(time.time())+28800},os.environ['JWT_SECRET'],algorithm='HS256')
