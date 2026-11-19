import os,logging
from contextlib import asynccontextmanager
import redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import FastAPI,Depends,HTTPException
from fastapi.responses import JSONResponse
from .db import Base,engine,session
from .models import *
from .schemas import *
from .auth import current,writer,supervisor,verify,token
from .common import pack,lock,add,audit
from . import renewal_service as renewal,isolation_service as isolation,harvest_service as harvest,sharing_service as sharing
from .middleware import Trace,Burst
queue=redis.Redis.from_url(os.environ['REDIS_URL'],decode_responses=True)
@asynccontextmanager
async def lifespan(app):
    from .seed_service import seed
    seed();yield
app=FastAPI(title='青禾种质站 · 复壮与授粉隔离',lifespan=lifespan);app.add_middleware(Trace);app.add_middleware(Burst)
@app.exception_handler(IntegrityError)
async def conflict(request,error):return JSONResponse({'detail':'编号、袋签或业务关联已存在，请核对后重试'},409)
@app.get('/health')
def health(s=Depends(session)):s.execute(select(1));queue.ping();return {'status':'ok'}
@app.post('/auth/login')
def login(d:Login,s=Depends(session)):
    u=s.scalar(select(User).where(User.email==d.email))
    if not u or not verify(d.password,u.password_hash):raise HTTPException(401,'邮箱或口令不正确')
    return {'token':token(u),'user':{'email':u.email,'role':u.role}}
@app.get('/me')
def me(u=Depends(current)):return {'email':u.email,'role':u.role}
@app.get('/archive')
def archive(s=Depends(session),u=Depends(current)):
    return {cls.__tablename__:[pack(x)for x in s.scalars(select(cls).order_by(cls.id))]for cls in (Accession,Lot,GerminationTest,Regeneration,Plot,Flowering,Pollination,Harvest,Distribution)}
@app.get('/audits')
def audits(s=Depends(session),u=Depends(current)):return [pack(x)for x in s.scalars(select(Audit).order_by(Audit.id.desc()).limit(50))]
@app.post('/accessions')
def accession(d:AccessionInput,s=Depends(session),u=Depends(writer)):
    x=add(s,Accession(**d.model_dump()));audit(s,u,'入藏种质 '+d.code);s.commit();return x
@app.put('/accessions/{id}')
def accession_note(id:int,d:AccessionInput,s=Depends(session),u=Depends(supervisor)):
    x=lock(s,Accession,id)
    if x.code!=d.code or x.crop!=d.crop or x.minimum!=d.minimum:raise HTTPException(409,'种质身份和保底量不可覆盖，仅可修订名称来源说明')
    x.name=d.name;x.origin=d.origin;audit(s,u,'修订种质来源 '+d.code);s.commit();return pack(x)
@app.post('/lots')
def lot(d:LotInput,s=Depends(session),u=Depends(writer)):
    lock(s,Accession,d.accession_id)
    if s.scalar(select(Lot.id).where(Lot.accession_id==d.accession_id)):raise HTTPException(409,'已有种质新代次必须经授粉收获回库建立，不能手工扩库存')
    x=add(s,Lot(**d.model_dump()));audit(s,u,'首批种子入库 '+d.code);s.commit();return x
@app.post('/germination-tests')
def test(d:TestInput,s=Depends(session),u=Depends(writer)):
    x=renewal.create_test(s,d,u);s.commit();return x
@app.post('/germination-tests/{id}/estimate')
def estimate(id:int,s=Depends(session),u=Depends(writer)):
    x=lock(s,GerminationTest,id)
    if x.state not in ('recorded','failed'):raise HTTPException(409,'仅新复测或失败评估可入队')
    x.state='queued';x.error=None;s.commit()
    try:queue.rpush('seed-vitality',id)
    except Exception:x.state='failed';x.error='队列不可用，请恢复后重试';s.commit();raise HTTPException(503,x.error)
    return pack(x)
@app.post('/regenerations')
def regeneration(d:RegenerationInput,s=Depends(session),u=Depends(writer)):
    x=renewal.request(s,d,u);s.commit();return x
@app.post('/regenerations/{id}/issue')
def issue(id:int,s=Depends(session),u=Depends(supervisor)):
    x=renewal.issue(s,id,u);s.commit();return x
@app.post('/regenerations/{id}/cancel')
def cancel(id:int,s=Depends(session),u=Depends(supervisor)):
    x=renewal.cancel(s,id,u);s.commit();return x
@app.post('/flowerings')
def flowering(d:FlowerInput,s=Depends(session),u=Depends(writer)):
    x=isolation.save(s,d,u);s.commit();return x
@app.put('/flowerings/{id}')
def edit_flowering(id:int,d:FlowerInput,s=Depends(session),u=Depends(writer)):
    x=isolation.save(s,d,u,id);s.commit();return x
@app.post('/flowerings/{id}/assign')
def assign(id:int,s=Depends(session),u=Depends(supervisor)):
    x=isolation.assign(s,id,u);s.commit();return x
@app.post('/pollinations')
def pollen(d:PollenInput,s=Depends(session),u=Depends(writer)):
    x=isolation.prepare(s,d,u);s.commit();return x
@app.put('/pollinations/{id}')
def edit_pollen(id:int,d:PollenInput,s=Depends(session),u=Depends(writer)):
    x=isolation.prepare(s,d,u,id);s.commit();return x
@app.post('/pollinations/{id}/pollinate')
def pollinate(id:int,s=Depends(session),u=Depends(supervisor)):
    x=isolation.pollinate(s,id,u);s.commit();return x
@app.post('/harvests')
def harvested(d:HarvestInput,s=Depends(session),u=Depends(writer)):
    x=harvest.save(s,d,u);s.commit();return x
@app.put('/harvests/{id}')
def edit_harvest(id:int,d:HarvestInput,s=Depends(session),u=Depends(writer)):
    x=harvest.save(s,d,u,id);s.commit();return x
@app.post('/harvests/{id}/store')
def store(id:int,s=Depends(session),u=Depends(supervisor)):
    x=harvest.store(s,id,u);s.commit();return x
@app.post('/distributions')
def distribution(d:DistributionInput,s=Depends(session),u=Depends(writer)):
    x=sharing.request(s,d,u);s.commit();return x
@app.post('/distributions/{id}/approve')
def approve(id:int,s=Depends(session),u=Depends(supervisor)):
    x=sharing.approve(s,id,u);s.commit();return x
@app.post('/distributions/{id}/receive')
def receive(id:int,s=Depends(session),u=Depends(writer)):
    x=sharing.receive(s,id,u);s.commit();return x
