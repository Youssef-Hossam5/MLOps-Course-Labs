"""
Load testing script for Churn Prediction API using Locust

Run with:
    locust -f locustfile.py --host=http://localhost:8000
    
Or with GUI (default):
    locust -f locustfile.py
    
Then open http://localhost:8089 in your browser and configure:
- Number of users: 10-100
- Spawn rate: 5-20 users/sec
- Host: http://your-deployed-app-url (if not localhost)
"""

from locust import HttpUser, task, between
import random


class ChurnPredictionUser(HttpUser):
    """Simulates a user making predict requests to the Churn Prediction API"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a simulated user starts"""
        self.health_check()
    
    @task
    def health_check(self):
        """Check API health"""
        self.client.get("/health")
    
    @task(3)  # Weight this task 3x more than others
    def predict_churn(self):
        """Make a churn prediction request"""
        payload = {
            "CreditScore": random.uniform(300, 850),
            "Geography": random.choice(["France", "Germany", "Spain"]),
            "Gender": random.choice(["Male", "Female"]),
            "Age": random.randint(18, 92),
            "Tenure": random.uniform(0, 10),
            "Balance": random.uniform(0, 250000),
            "NumOfProducts": random.randint(1, 4),
            "HasCrCard": random.choice([0, 1]),
            "IsActiveMember": random.choice([0, 1]),
            "EstimatedSalary": random.uniform(10000, 200000),
        }
        self.client.post(
            "/predict",
            json=payload,
            name="/predict"
        )
    
    @task
    def home(self):
        """Access home endpoint"""
        self.client.get("/")
