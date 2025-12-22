# scripts/test.py
import os
import time
import argparse
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
MODEL_DIR = os.getenv("MODEL_DIR", "model")
MODEL_PATH = os.path.join(MODEL_DIR, "random_forest_model.pkl")

DEFAULT_INTERVAL_SECONDS = int(os.getenv("TEST_INTERVAL_SECONDS", "60"))
DEFAULT_PORT = int(os.getenv("TEST_METRICS_PORT", "8001"))

def run_test_once():
    start = time.perf_counter()
    test_requests.inc()

    try:
        if not os.path.exists(MODEL_PATH):
            print(f"[WARN] Model not found at {MODEL_PATH}. Waiting for trainer...")
            test_errors.inc()
            return

        model = joblib.load(MODEL_PATH)

        iris = load_iris()
        _, X_test, _, y_test = train_test_split(
            iris.data, iris.target, test_size=0.2, random_state=42
        )

        acc = accuracy_score(y_test, model.predict(X_test))

        test_counter.inc()
        test_accuracy.set(acc)
        test_duration.observe(time.perf_counter() - start)
        build_info.labels(version=VERSION, git_sha=GIT_SHA).set(1)

        print(f"[INFO] Test accuracy: {acc:.2f}")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        test_errors.inc()

    finally:
        request_latency.observe(time.perf_counter() - start)

def main():
    parser = argparse.ArgumentParser(description="Model tester service with Prometheus metrics")
    parser.add_argument("--once", action="store_true", help="Run one evaluation and exit")
    parser.add_argument("--no-server", action="store_true", help="Do not start Prometheus HTTP server")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS, help="Seconds between runs")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Metrics port")
    args = parser.parse_args()

    if not args.no_server:
        start_http_server(args.port)
        print(f"[INFO] Prometheus test metrics exposed on port {args.port} (/metrics)")

    print(f"[INFO] Build info: VERSION={VERSION}, GIT_SHA={GIT_SHA}")
    print(f"[INFO] Model path: {MODEL_PATH}")

    if args.once:
        run_test_once()
        return

    while True:
        run_test_once()
        time.sleep(max(1, args.interval))

if __name__ == "__main__":
    main()
