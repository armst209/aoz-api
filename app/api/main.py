from fastapi import FastAPI
from app.api.routes.mobile_weapons import router as mobile_weapons_router
from app.api.routes.characters import router as characters_router
from app.api.routes.support_weapons import router as support_weapons_router
from app.api.routes.model_kits import router as model_kits_router
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
app.include_router(characters_router)
app.include_router(support_weapons_router)
app.include_router(model_kits_router)
