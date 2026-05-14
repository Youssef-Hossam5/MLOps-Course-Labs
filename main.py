"""
Churn Prediction API

Run with:
    litestar --app main:app run --reload
Then open:
    http://localhost:8000/schema/swagger
"""

from litestar import Litestar, get, post
from pydantic import BaseModel

from app.logger_setup import setup_logging
from app.model_utils import predict_churn

logger = setup_logging()


# ---------------------------------------------------------------------------
# Request Schema
# ---------------------------------------------------------------------------
class ChurnRequest(BaseModel):
    CreditScore: float
    Geography: str
    Gender: str
    Age: int
    Tenure: float
    Balance: float
    NumOfProducts: int
    HasCrCard: int
    IsActiveMember: int
    EstimatedSalary: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@get("/")
def home() -> dict:
    logger.info("Home endpoint accessed")
    return {"message": "Welcome to Churn Prediction API"}


@get("/health")
def health() -> dict:
    return {"status": "healthy"}


@post("/predict")
def predict(data: ChurnRequest) -> dict:
    features = data.model_dump()
    logger.info(f"Input features: {features}")
    prediction = predict_churn(features)
    logger.info(f"Prediction result: {prediction}")
    return {"prediction": prediction}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = Litestar(
    route_handlers=[home, health, predict],
)
