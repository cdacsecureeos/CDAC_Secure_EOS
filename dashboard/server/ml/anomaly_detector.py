# server/ml/anomaly_detector.py

import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib, os

MODEL_PATH = "server/ml/model.joblib"

# Features used should match what client sends and DB stores
FEATURE_COLUMNS = ["cpu_percent", "mem_percent", "virt", "res", "shr", "nice"]

def train_model(df: pd.DataFrame, contamination: float = 0.01):
    if df.empty:
        raise ValueError("No data provided for training")

    # ensure only numeric columns used
    features = df[FEATURE_COLUMNS].fillna(0).astype(float)
    clf = IsolationForest(contamination=contamination, random_state=42)
    clf.fit(features)
    os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    return clf

def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    return joblib.load(MODEL_PATH)

def detect_anomaly(record: dict, model):
    if model is None:
        return False, 0.0
    df = pd.DataFrame([record])
    features = df[FEATURE_COLUMNS].fillna(0).astype(float)
    pred = model.predict(features)[0]   # -1 anomaly, 1 normal
    score = float(model.decision_function(features)[0])
    return (pred == -1), score
