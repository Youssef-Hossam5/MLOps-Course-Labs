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
from litestar.exceptions import HTTPException, ValidationException
from app.logger_setup import setup_logging
from app.model_utils import predict_churn, predict_churn_with_confidence
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

def handle_validation_exception(request: Request, exception: ValidationException) -> Any:
    request_id = str(uuid.uuid4())
    endpoint = request.url.path
    
    # Track the bad input metric in Axiom
    axiom.log_invalid_input(
        endpoint=endpoint,
        error_details=exception.detail,
        request_id=request_id
    )
    
    logger.warning(f"[{request_id}] Invalid input attempt on {endpoint}: {exception.detail}")
    
    # Re-raise it for Litestar to return a standard 400 response
    raise HTTPException(
        status_code=400,
        detail={"request_id": request_id, "error": "Invalid input format", "details": exception.detail}
    )
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
    - Model predictions (predicted class, confidence)
    - Server metrics (response time, status code)
    - Server latency details
    - Model confidence metrics
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
        
        # Make prediction with confidence
        model_start = time.time()
        prediction, confidence = predict_churn_with_confidence(features)
        model_time_ms = (time.time() - model_start) * 1000
        
        # Log prediction details
        axiom.log_prediction(features, prediction, confidence, request_id=request_id)
        confidence_str = f"{confidence:.4f}" if confidence is not None else "N/A"

        logger.info(
            f"[{request_id}] Prediction: {prediction}, Confidence: {confidence_str}"
        )       
        
        # Log model confidence separately
        if confidence is not None:
            axiom.log_model_confidence(prediction, confidence, request_id=request_id)
        
        # Calculate response time and log metrics
        response_time_ms = (time.time() - start_time) * 1000
        axiom.log_metrics(200, response_time_ms, "/predict", request_id)
        
        # Log detailed server latency
        axiom.log_server_latency(response_time_ms, "/predict", request_id)
        logger.info(
            f"[{request_id}] Response time: {response_time_ms:.2f}ms, "
            f"Model time: {model_time_ms:.2f}ms, Status: 200"
        )
        
        return {
            "request_id": request_id,
            "prediction": prediction,
            "prediction_label": "Will Churn" if prediction == 1 else "Will Not Churn",
            "confidence": confidence,
            "response_time_ms": round(response_time_ms, 2),
        }
    
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        error_message = str(e)
        
        # Log error
        axiom.log_error(error_message, type(e).__name__, "/predict", request_id)
        axiom.log_metrics(500, response_time_ms, "/predict", request_id, error_message)
        axiom.log_server_latency(response_time_ms, "/predict", request_id)
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
    exception_handlers={ValidationException: handle_validation_exception} 
)
