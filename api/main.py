from fastapi import FastAPI
from app.routes.mobile_weapons import router as mobile_weapons_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(mobile_weapons_router)
