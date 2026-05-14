"""
Model loading and prediction logic.

The model must be loaded ONCE at module level, NOT inside the predict function.
"""
import pickle
import joblib
import pandas as pd
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
# app/model_utils.py -> go up one level to project root
PROJECT_ROOT = Path(__file__).parent.parent
MODEL_PATH = PROJECT_ROOT / "data" / "model.pkl"
TRANSFORMER_PATH = PROJECT_ROOT / "data" / "column_transformer.joblib"

# ---------------------------------------------------------------------------
# Model Loading with Error Handling
# ---------------------------------------------------------------------------
def load_model_and_transformer():
    """Load model and transformer with proper error handling."""
    try:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        if not TRANSFORMER_PATH.exists():
            raise FileNotFoundError(f"Transformer file not found: {TRANSFORMER_PATH}")
        
        logger.info(f"Loading model from {MODEL_PATH}")
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        
        logger.info(f"Loading transformer from {TRANSFORMER_PATH}")
        transformer = joblib.load(TRANSFORMER_PATH)
        
        logger.info("Model and transformer loaded successfully")
        return model, transformer
    
    except Exception as e:
        logger.error(f"Failed to load model or transformer: {str(e)}")
        raise

# Load once at module level (happens when app starts)
model, transformer = load_model_and_transformer()

# ---------------------------------------------------------------------------
# Prediction Function
# ---------------------------------------------------------------------------
def predict_churn(features: Dict) -> int:
    """Predict churn for a customer."""
    try:
        df = pd.DataFrame([features])
        
        # Transform features
        X = transformer.transform(df)
        
        # Convert back to DataFrame with feature names (suppresses warning)
        if hasattr(transformer, 'get_feature_names_out'):
            feature_names = transformer.get_feature_names_out()
            X = pd.DataFrame(X, columns=feature_names)
        
        # Predict
        prediction = model.predict(X)
        
        return int(prediction[0])
    
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = {
        "CreditScore": 600,
        "Geography": "Germany",
        "Gender": "Male",
        "Age": 35,
        "Tenure": 5,
        "Balance": 50000,
        "NumOfProducts": 2,
        "HasCrCard": 1,
        "IsActiveMember": 1,
        "EstimatedSalary": 60000
    }

    print("Input:", sample)
    print("Prediction:", predict_churn(sample))