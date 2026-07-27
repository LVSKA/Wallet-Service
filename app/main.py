from fastapi import FastAPI

from app.api.wallets import router as wallets_router

app = FastAPI(title="Wallet Service")
app.include_router(wallets_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
