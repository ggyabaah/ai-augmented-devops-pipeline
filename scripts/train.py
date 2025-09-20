import os
import time
import joblib
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# --- Prometheus metrics ---
train_counter = Counter("model_training_runs", "Number of times model training executed")
accuracy_gauge = Gauge("model_training_accuracy", "Model accuracy from last training run")
train_duration = Histogram("train_duration_seconds", "Time taken to train a model")
build_info = Gauge("model_build_info", "Build info as labels", ["version", "git_sha"])

# Metadata (injected via environment, e.g. from Jenkins or docker-compose)
VERSION = os.getenv("VERSION", "dev")
GIT_SHA = os.getenv("GIT_SHA", "local")

def train_and_save_model():
    """Train RandomForest model, evaluate, save, and update Prometheus metrics."""
    with train_duration.time():
        print("[INFO] Loading dataset...")
        iris = load_iris()
        X_train, X_test, y_train, y_test = train_test_split(
            iris.data, iris.target, test_size=0.2, random_state=42
        )

        print("[INFO] Training RandomForest model...")
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        accuracy = accuracy_score(y_test, model.predict(X_test))
        print(f"[INFO] Training completed with accuracy: {accuracy:.2f}")

        # Update Prometheus metrics
        train_counter.inc()
        accuracy_gauge.set(accuracy)

        # Save model
        os.makedirs("model", exist_ok=True)
        model_path = os.path.join("model", "random_forest_model.pkl")
        joblib.dump(model, model_path)
        print(f"[INFO] Model saved at: {model_path}")

    # Build info → shows up once in Prometheus
    build_info.labels(version=VERSION, git_sha=GIT_SHA).set(1)

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8000)
    print("[INFO] Prometheus metrics exposed on port 8000 (/metrics)")
    print(f"[INFO] Build info → VERSION={VERSION}, GIT_SHA={GIT_SHA}")

    # Continuous loop
    while True:
        train_and_save_model()
        time.sleep(60)  # retrain every 1 minute