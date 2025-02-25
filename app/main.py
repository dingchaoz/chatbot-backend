import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
import pickle
from contextlib import asynccontextmanager
import os

from app.api.router import api_router
from app.core.config import settings

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load preprocessed data and index during startup
    artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
    try:
        with open(os.path.join(artifacts_dir, "index.pkl"), "rb") as f:
            app.state.index = pickle.load(f)
        with open(os.path.join(artifacts_dir, "llm.pkl"), "rb") as f:
            app.state.llm = pickle.load(f)
    except (FileNotFoundError, pickle.UnpicklingError) as e:
        raise RuntimeError("Failed to load preprocessed data and index") from e

    yield
    # Perform any necessary cleanup during shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)
