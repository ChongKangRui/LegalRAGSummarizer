import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import FRONTEND_ORIGIN

from app.api.summarization import router as query_router
from app.api.documents import router as document_router
from app.api.eval_dashboard import router as eval_router
from app.api.inspector import router as inspector_router
from app.api.compare import router as compare_router
from app.api.rate_limit import check_rate_limiting, get_route_limit
app = FastAPI()

ALLOWED_ORIGINS = {"http://localhost:5173", FRONTEND_ORIGIN}
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["*"], allow_headers=["*"])

# ---- Middleware: runs on EVERY request, like Express `app.use((req, res, next) => ...)` ----
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # everything BEFORE `call_next` == code before you call next() in Express
    start = time.perf_counter()
    print(f"--> {request.method} {request.url.path}")

    response = await call_next(request)  # hand control to the next middleware / the route

    # everything AFTER `call_next` == code after next() resolves (you now have the response)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"<-- {request.method} {request.url.path} {response.status_code} ({elapsed_ms:.1f} ms)")
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    return response


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    route_limit = get_route_limit(request.url.path)

    if route_limit is not None:
        bucket, limit = route_limit
        ip = request.client.host
        key = f"{ip}:{bucket}"

        if not check_rate_limiting(key, limit):
            response = JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded for '{bucket}'. Try again later."},
            )
            origin = request.headers.get("origin")
            if origin in ALLOWED_ORIGINS:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                
            return response

    return await call_next(request)


# ---- Routing: mount a router, like Express `app.use('/query', queryRouter)` ----
app.include_router(query_router)
app.include_router(document_router)
app.include_router(eval_router)
app.include_router(inspector_router)
app.include_router(compare_router)
@app.get("/")
async def root():
    return {"message": "Hello World"}