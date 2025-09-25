# scripts/train.py
import os
import time
import joblib
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# --- Prometheus metrics ---
train_counter = Counter("model_training_runs_total", "Number of times model training executed")
train_accuracy = Gauge("model_training_accuracy", "Model accuracy from last training run")
train_duration = Histogram("train_duration_seconds", "Time taken to train a model")
build_info = Gauge("model_build_info", "Build info as labels", ["version", "git_sha"])

# Extra metrics (to align with Grafana dashboard)
train_requests = Counter("model_training_requests_total", "Number of training requests")
train_errors = Counter("model_training_errors_total", "Number of failed training runs")
request_latency = Histogram("request_latency_seconds", "Training request latency in seconds")

# Metadata (injected via environment variables / Jenkins / docker-compose)
VERSION = os.getenv("VERSION", "dev")
GIT_SHA = os.getenv("GIT_SHA", "local")

def train_and_save_model():
    start = time.perf_counter()
    train_requests.inc()  # mark a new training request

    try:
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

            # Update metrics
            train_counter.inc()
            train_accuracy.set(accuracy)

            # Save model
            os.makedirs("model", exist_ok=True)
            model_path = os.path.join("model", "random_forest_model.pkl")
            joblib.dump(model, model_path)
            print(f"[INFO] Model saved at: {model_path}")

        # Build info → set once
        build_info.labels(version=VERSION, git_sha=GIT_SHA).set(1)

    except Exception as e:
        print(f"[ERROR] Training failed: {e}")
        train_errors.inc()   # increment error counter

    finally:
        duration = time.perf_counter() - start
        request_latency.observe(duration)

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8000)
    print("[INFO] Prometheus metrics exposed on port 8000 (/metrics)")
    print(f"[INFO] Build info → VERSION={VERSION}, GIT_SHA={GIT_SHA}")

    # Continuous loop
    while True:
        train_and_save_model()
        time.sleep(60)  # retrain every 1 minute