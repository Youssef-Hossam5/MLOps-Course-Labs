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

    def log_error(self, message, error_type, endpoint, request_id=None):
        self._send_event({
            "event_type": "error",
            "request_id": request_id,
            "message": message,
            "error_type": error_type,
            "endpoint": endpoint
        })


_axiom_logger = None


def get_axiom_logger():
    global _axiom_logger
    if _axiom_logger is None:
        _axiom_logger = AxiomLogger()
    return _axiom_logger