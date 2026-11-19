from sqlalchemy import select,func
from fastapi import HTTPException
from .models import Audit,Lot,Accession

def pack(x):return {c.name:getattr(x,c.name) for c in x.__table__.columns}
def lock(s,cls,id):
    x=s.scalar(select(cls).where(cls.id==id).with_for_update().execution_options(populate_existing=True))
    if not x:raise HTTPException(404,'业务记录不存在')
    return x
def audit(s,u,message):s.add(Audit(actor=u.email,action=message))
def add(s,x):s.add(x);s.flush();return pack(x)
def reserve(s,lot,quantity):
    a=lock(s,Accession,lot.accession_id)
    current=lock(s,Lot,lot.id)
    total=int(s.scalar(select(func.sum(Lot.available)).where(Lot.accession_id==a.id)) or 0)
    if quantity>current.available:raise HTTPException(409,'本批种子不足')
    if total-quantity<a.minimum:raise HTTPException(409,'扣种后低于本种质最低保底量')
    current.available-=quantity
    return {'accession_code':a.code,'before_total':total,'after_total':total-quantity,'minimum':a.minimum,'lot_before':current.available+quantity}
