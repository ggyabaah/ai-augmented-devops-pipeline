# scripts/test.py
import os
import time
import joblib
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# --- Prometheus metrics ---
test_counter = Counter("model_test_runs_total", "Number of times model testing executed")
test_accuracy = Gauge("model_test_accuracy", "Model accuracy from last test run")
test_duration = Histogram("test_duration_seconds", "Time taken to run evaluation")
build_info = Gauge("model_build_info", "Build info as labels", ["version", "git_sha"])

# Extra metrics (to align with Grafana dashboard)
test_requests = Counter("model_test_requests_total", "Number of test requests")
test_errors = Counter("model_test_errors_total", "Number of test errors")
request_latency = Histogram("request_latency_seconds", "Test request latency in seconds")

# Metadata
VERSION = os.getenv("VERSION", "dev")
GIT_SHA = os.getenv("GIT_SHA", "local")
MODEL_PATH = os.path.join(os.getenv("MODEL_DIR", "model"), "random_forest_model.pkl")

def run_test_once():
    start = time.perf_counter()
    test_requests.inc()  # increment requests counter

    try:
        if not os.path.exists(MODEL_PATH):
            print(f"[WARN] Model not found at {MODEL_PATH}. Waiting for trainer...")
            test_errors.inc()
            return

        # Load model
        model = joblib.load(MODEL_PATH)

        # Load dataset and split
        iris = load_iris()
        _, X_test, _, y_test = train_test_split(
            iris.data, iris.target, test_size=0.2, random_state=42
        )

        # Run evaluation
        acc = accuracy_score(y_test, model.predict(X_test))

        # Update metrics
        test_counter.inc()
        test_accuracy.set(acc)
        test_duration.observe(time.perf_counter() - start)
        build_info.labels(version=VERSION, git_sha=GIT_SHA).set(1)

        print(f"[INFO] Test accuracy: {acc:.2f}")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        test_errors.inc()

    finally:
        duration = time.perf_counter() - start
        request_latency.observe(duration)

if __name__ == "__main__":
    start_http_server(8001)
    print("[INFO] Prometheus test metrics exposed on port 8001 (/metrics)")
    print(f"[INFO] Build info → VERSION={VERSION}, GIT_SHA={GIT_SHA}")

    # Run test periodically
    while True:
        run_test_once()
        time.sleep(60)  # test every 1 minute