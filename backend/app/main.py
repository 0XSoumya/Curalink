from fastapi import FastAPI
from app.api.routes import router
from app.core.database import connect_to_mongo, close_mongo_connection
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Medical Research Assistant")

# 🔹 CORS (keep before routes ideally)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Include routes ONLY ONCE
app.include_router(router)

# 🔹 Startup & Shutdown
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# 🔹 Health
@app.get("/health")
async def health_check():
    return {"status": "ok"}