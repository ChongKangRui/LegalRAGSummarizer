import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.summarization import router as query_router
from app.api.documents import router as document_router

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

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


# ---- Routing: mount a router, like Express `app.use('/query', queryRouter)` ----
app.include_router(query_router)
app.include_router(document_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
