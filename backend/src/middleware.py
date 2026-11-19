import time,uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
class Trace(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        response=await call_next(request);response.headers['X-Request-Id']=str(uuid.uuid4());return response
class Burst(BaseHTTPMiddleware):
    buckets={}
    async def dispatch(self,request,call_next):
        key=request.client.host;now=time.monotonic();history=[t for t in self.buckets.get(key,[]) if now-t<60]
        if len(history)>=360:return JSONResponse({'detail':'请求较密集，请稍后再试'},429)
        history.append(now);self.buckets[key]=history;return await call_next(request)
