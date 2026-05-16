"""
Churn Prediction API

Run with:
    litestar --app main:app run --reload
Then open:
    http://localhost:8000/schema/swagger
"""

import time
import uuid
from typing import Dict, Any
from litestar import Litestar, get, post
from litestar.connection import Request
from pydantic import BaseModel
from litestar.exceptions import HTTPException
from app.logger_setup import setup_logging
from app.model_utils import predict_churn
from app.axiom_logger import get_axiom_logger
from dotenv import load_dotenv

load_dotenv()
logger = setup_logging()
axiom = get_axiom_logger()


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
def predict(request: Request, data: ChurnRequest) -> dict:
    """
    Predict customer churn.
    
    Logs:
    - Incoming request data (features, headers)
    - Model predictions (predicted class)
    - Server metrics (response time, status code)
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        features = data.model_dump()
        
        # Extract relevant headers
        headers = {
            "content-type": request.headers.get("content-type", "unknown"),
            "user-agent": request.headers.get("user-agent", "unknown"),
        }
        
        # Log incoming request
        axiom.log_request(features, headers, request_id)
        logger.info(f"[{request_id}] Input features: {features}")
        
        # Make prediction
        prediction = predict_churn(features)
        
        # Log prediction details
        axiom.log_prediction(features, prediction, probability=None, request_id=request_id)
        logger.info(
            f"[{request_id}] Prediction: {prediction}"
        )
        
        # Calculate response time and log metrics
        response_time_ms = (time.time() - start_time) * 1000
        axiom.log_metrics(200, response_time_ms, "/predict", request_id)
        logger.info(
            f"[{request_id}] Response time: {response_time_ms:.2f}ms, "
            f"Status: 200"
        )
        
        return {
            "request_id": request_id,
            "prediction": prediction,
            "prediction_label": "Will Churn" if prediction == 1 else "Will Not Churn",
        }
    
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        error_message = str(e)
        
        # Log error
        axiom.log_error(error_message, type(e).__name__, "/predict", request_id)
        axiom.log_metrics(500, response_time_ms, "/predict", request_id, error_message)
        logger.error(
            f"[{request_id}] Prediction failed: {error_message}, "
            f"Response time: {response_time_ms:.2f}ms"
        )
        
        raise HTTPException(
            status_code=500,
            detail={"request_id": request_id, "error": error_message}
            )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = Litestar(
    route_handlers=[home, health, predict],
)
