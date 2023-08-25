#!/usr/bin/env python

from fastapi import FastAPI, Request, Response, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from starlette.middleware.cors import CORSMiddleware
import time
import uvicorn


from src.routes import auth, contacts, users
from src.conf.config import settings


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')
app.include_router(users.router, prefix='/api')


@app.on_event("startup")
async def startup():
    rds = await redis.Redis(host=settings.redis_host, port=settings.redis_port,
                            db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(rds)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    '''
    Middleware that measures request handling time and adds header
    "X-Process-Time" with measured value to the response.

    :param request: Incoming HTTP request.
    :type request: Request
    :param call_next: Next middleware handler.
    :type call_next: function
    :return: Response with added header.
    :rtype: Response
    '''
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
def read_root():
    '''
    Returns short description what this API to do.

    :return: Message.
    :rtype: dict
    '''
    return {"message": "Contacts API"}


if __name__ == '__main__':
    uvicorn.run("main:app", host="localhost", reload=True, log_level="info")
