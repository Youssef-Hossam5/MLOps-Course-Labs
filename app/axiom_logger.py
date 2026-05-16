import os
import json
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AxiomLogger:
    def __init__(self):
            # Axiom's Python SDK natively looks for AXIOM_TOKEN
            self.api_token = os.getenv("AXIOM_TOKEN")
            self.dataset = os.getenv("AXIOM_DATASET", "churn-prediction-api")

            try:
                from axiom_py import Client

                if not self.api_token:
                    logger.warning("AXIOM_TOKEN missing → Axiom disabled")
                    self.client = None
                    return

                # FIX: Initialize the client without passing token explicitly.
                # The SDK will automatically fetch the AXIOM_TOKEN from the environment.
                self.client = Client()

                logger.info(f"Axiom enabled → dataset: {self.dataset}")

            except ImportError:
                logger.warning("axiom package not installed")
                self.client = None

    def _send_event(self, event: Dict[str, Any]):
        if not self.client:
            logger.info(json.dumps(event))
            return

        try:
            event["timestamp"] = event.get(
                "timestamp",
                datetime.utcnow().isoformat()
            )

            # FIXED METHOD
            self.client.ingest_events(
                dataset=self.dataset,
                events=[event]
            )

        except Exception as e:
            logger.error(f"Axiom ingest failed: {e}")
            logger.info(json.dumps(event))

    # -------------------------
    # Logging functions
    # -------------------------
    def log_request(self, features, headers=None, request_id=None):
        self._send_event({
            "event_type": "api_request",
            "request_id": request_id,
            "features": features,
            "headers": headers
        })

    def log_prediction(self, features, prediction, probability, request_id=None):
        self._send_event({
            "event_type": "model_prediction",
            "request_id": request_id,
            "prediction": prediction,
            "probability": probability,
            "features": features
        })

    def log_metrics(self, status_code, response_time_ms, endpoint, request_id=None, error=None):
        self._send_event({
            "event_type": "metrics",
            "request_id": request_id,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "endpoint": endpoint,
            "error": error
        })

    def log_server_latency(self, response_time_ms, endpoint, request_id=None):
        """Log detailed server-side latency metrics."""
        self._send_event({
            "event_type": "server_latency",
            "request_id": request_id,
            "response_time_ms": response_time_ms,
            "endpoint": endpoint,
            "latency_category": self._categorize_latency(response_time_ms),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _categorize_latency(self, response_time_ms: float) -> str:
        """Categorize response time into performance tiers."""
        if response_time_ms < 100:
            return "excellent"
        elif response_time_ms < 250:
            return "good"
        elif response_time_ms < 500:
            return "acceptable"
        elif response_time_ms < 1000:
            return "slow"
        else:
            return "very_slow"

    def log_error(self, message, error_type, endpoint, request_id=None):
        self._send_event({
            "event_type": "error",
            "request_id": request_id,
            "message": message,
            "error_type": error_type,
            "endpoint": endpoint
        })

    def log_model_confidence(self, prediction, confidence, request_id=None):
        """Log model prediction confidence/probability metrics."""
        self._send_event({
            "event_type": "model_confidence",
            "request_id": request_id,
            "prediction": prediction,
            "confidence": confidence,
            "confidence_percentage": round(confidence * 100, 2) if confidence else None,
            "confidence_level": self._categorize_confidence(confidence),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _categorize_confidence(self, confidence: float) -> str:
        """Categorize model confidence into levels."""
        if confidence is None:
            return "unknown"
        elif confidence >= 0.9:
            return "very_high"
        elif confidence >= 0.75:
            return "high"
        elif confidence >= 0.6:
            return "moderate"
        elif confidence >= 0.5:
            return "low"
        else:
            return "very_low"
    
    def log_invalid_input(self, endpoint: str, error_details: Any, request_id: str = None):
        """Logs malformed or failing client payloads to Axiom."""
        self._send_event({
            "event_type": "invalid_input_attempt",
            "request_id": request_id,
            "endpoint": endpoint,
            "error_details": error_details,
            "status_code": 400
        }) 

_axiom_logger = None


def get_axiom_logger():
    global _axiom_logger
    if _axiom_logger is None:
        _axiom_logger = AxiomLogger()
    return _axiom_logger