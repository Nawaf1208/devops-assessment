import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import db, init_db
from app.models.item import Item
from app.routes import files, health, items
from app.services.storage import storage_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("app")

SEED_ITEMS = [
    {
        "name": "Tactical Communication Unit",
        "description": "Secure field communication and radio interface system",
        "status": "active",
    },
    {
        "name": "Navigation Control Module",
        "description": "Integrated navigation and positioning control unit",
        "status": "active",
    },
    {
        "name": "Radar Signal Processor",
        "description": "Signal processing module for surveillance radar systems",
        "status": "active",
    },
    {
        "name": "Electro-Optical Sensor Unit",
        "description": "Long-range electro-optical observation and tracking system",
        "status": "active",
    },
    {
        "name": "Power Distribution Assembly",
        "description": "Auxiliary power distribution and protection assembly",
        "status": "inactive",
    },
    {
        "name": "Secure Data Interface",
        "description": "Protected interface for mission data exchange between subsystems",
        "status": "inactive",
    },
    {
        "name": "Target Tracking Module",
        "description": "Subsystem for tracking and maintaining designated objects within sensor range",
        "status": "active",
    },
]


def seed_items() -> None:
    with db.Session() as session:
        existing = session.execute(select(Item.id)).first()
        if existing is not None:
            return
        for item in SEED_ITEMS:
            session.add(Item(**item))
        session.commit()
        logger.info("Seeded %d items", len(SEED_ITEMS))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)

    init_db()
    seed_items()

    try:
        storage_service.ensure_bucket()
    except Exception as exc:  # noqa: BLE001 - startup must not crash on S3 issues
        logger.error("S3 bucket setup failed during startup: %s", exc)

    yield

    logger.info("Application shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    description="Service & File Management Dashboard backend API.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Accept",
        "Authorization",
        "Content-Type",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=[
        "Content-Length",
        "Content-Disposition",
    ],
    max_age=600,
)

app.include_router(health.router, prefix="/api")
app.include_router(items.router, prefix="/api")
app.include_router(files.router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    return {"service": settings.APP_NAME, "docs": "/docs"}
