import os,time,json,logging
from pathlib import Path
import redis
from .db import Session
from .models import GerminationTest,Lot
from .common import lock
from .vitality import predict
queue=redis.Redis.from_url(os.environ['REDIS_URL'],decode_responses=True)
while True:
    Path('/tmp/seed-heartbeat').touch()
    try:
        item=queue.blpop('seed-vitality',timeout=2)
        if not item:continue
        id=int(item[1])
        with Session() as s:
            test=lock(s,GerminationTest,id)
            if test.state!='queued':continue
            test.state='running';s.commit()
            try:
                lot=s.get(Lot,test.lot_id);result=predict(lot,test);test.prediction=result;test.state='ready';test.error=None
                Path('/artifacts').mkdir(exist_ok=True);Path(f'/artifacts/vitality-{id}.json').write_text(json.dumps(result,ensure_ascii=False));s.commit()
            except Exception as ex:test.state='failed';test.error=str(ex)[:450];s.commit();logging.exception('vitality failed')
    except Exception:logging.exception('worker queue error');time.sleep(1)
