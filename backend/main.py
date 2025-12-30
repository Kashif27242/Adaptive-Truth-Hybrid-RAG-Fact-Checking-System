from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent import verify_claim
from models import ClaimRequest, VerificationResult

load_dotenv()

app = FastAPI(title="Adaptive Truth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Adaptive Truth API is running"}

@app.post("/verify", response_model=VerificationResult)
async def verify(request: ClaimRequest):
    result = await verify_claim(request.claim)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
