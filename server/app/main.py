from fastapi import FastAPI

from api.endpoints import router as endpoints_router

app = FastAPI()

app.include_router(endpoints_router, prefix='/task')
