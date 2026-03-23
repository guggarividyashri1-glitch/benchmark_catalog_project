from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from routes import (
    create_catalog,
    update_catalog,
    get_catalog,
    delete_catalog,
    update_status
)

from utils.auth import create_token

app = FastAPI(
    title="Benchmark Catalog API",
    version="1.0"
)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

    errors = exc.errors()

    field = "unknown"
    message = "Invalid input"

    if errors:
        error_data = errors[0]

        if "loc" in error_data:
            field = error_data["loc"][-1]

        if "msg" in error_data:
            message = error_data["msg"].replace("Value error, ", "")

    return JSONResponse(
        status_code=400,
        content={
            "status": "failed",
            "message": f"{field}: {message}",
            "status_code": 400,
            "data": []
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "failed",
            "message": str(exc.detail),
            "status_code": exc.status_code,
            "data": []
        }
    )
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    return JSONResponse(
        status_code=500,
        content={
            "status": "failed",
            "message": "Internal Server Error",
            "status_code": 500,
            "data": []
        }
    )
@app.get("/login/{role}")
def login(role: str):

    if role not in ["admin", "user"]:
        return {
            "status": "failed",
            "message": "Role must be admin or user",
            "status_code": 400,
            "data": []
        }

    token = create_token(role)

    return {
        "status": "success",
        "message": "Token generated successfully",
        "status_code": 200,
        "data": {
            "role": role,
            "token": token
        }
    }

app.include_router(create_catalog.router)
app.include_router(update_catalog.router)
app.include_router(get_catalog.router)
app.include_router(update_status.router)
app.include_router(delete_catalog.router)



