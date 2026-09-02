import time

from fastapi import FastAPI, Request

from api.routes import router as query_router

app = FastAPI()



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


@app.get("/")
async def root():
    return {"message": "Hello World"}
