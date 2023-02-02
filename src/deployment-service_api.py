import uvicorn
from fastapi import FastAPI
# from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from deployment_service.config.settings import Settings
from deployment_service.config.logging import logger as l
from deployment_service.gateways.input.api.metrics import router as metrics_router
from deployment_service.gateways.input.api.deployments import router as deployments_router


settings = Settings()
api = FastAPI(title="SmartCLIDE deployment component API")
api.include_router(deployments_router, prefix='/api/v1')
api.include_router(metrics_router, prefix='/api/v1')

origins = ['*']

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    try:
        print(f"\n[INFO] Starting Deployment service API on  http://{settings.api['host']}:{settings.api['port']}")
        uvicorn.run(api, host=settings.api['host'], port=settings.api['port'])
    except Exception as err:
        print(f"[ERROR] Error running SmartCLIDE deployment API': {err}")