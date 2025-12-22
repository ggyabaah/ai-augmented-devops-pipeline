# scripts/train.py
# scripts/train.py
import os
import time
import argparse
import joblib
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ----------------------------
# Prometheus metrics
# ----------------------------
train_counter = Counter("model_training_runs_total", "Number of times model training executed")
train_accuracy = Gauge("model_training_accuracy", "Model accuracy from last training run")
train_duration = Histogram("train_duration_seconds", "Time taken to train a model")
build_info = Gauge("model_build_info", "Build info as labels", ["version", "git_sha"])

# Extra metrics (align with Grafana dashboard)
train_requests = Counter("model_training_requests_total", "Number of training requests")
train_errors = Counter("model_training_errors_total", "Number of failed training runs")
request_latency = Histogram("request_latency_seconds", "Training request latency in seconds")

# ----------------------------
# Metadata / configuration
# ----------------------------
VERSION = os.getenv("VERSION", "dev")
GIT_SHA = os.getenv("GIT_SHA", "local")

MODEL_DIR = os.getenv("MODEL_DIR", "model")
MODEL_FILENAME = os.getenv("MODEL_FILENAME", "random_forest_model.pkl")
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)

DEFAULT_INTERVAL_SECONDS = int(os.getenv("TRAIN_INTERVAL_SECONDS", "60"))
DEFAULT_PORT = int(os.getenv("TRAIN_METRICS_PORT", "8000"))
N_ESTIMATORS = int(os.getenv("RF_N_ESTIMATORS", "100"))
RANDOM_STATE = int(os.getenv("RF_RANDOM_STATE", "42"))


def train_and_save_model() -> None:
    """
    Train a RandomForest model on Iris dataset, save it to disk,
    and expose metrics for Prometheus/Grafana.
    """
    start = time.perf_counter()
    train_requests.inc()

    try:
        with train_duration.time():
            print("[INFO] Loading dataset...")
            iris = load_iris()
            X_train, X_test, y_train, y_test = train_test_split(
                iris.data, iris.target, test_size=0.2, random_state=RANDOM_STATE
            )

            print("[INFO] Training RandomForest model...")
            model = RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE)
            model.fit(X_train, y_train)

            acc = accuracy_score(y_test, model.predict(X_test))
            print(f"[INFO] Training completed with accuracy: {acc:.2f}")

            # Update metrics
            train_counter.inc()
            train_accuracy.set(acc)

            # Save model
            os.makedirs(MODEL_DIR, exist_ok=True)
            joblib.dump(model, MODEL_PATH)
            print(f"[INFO] Model saved at: {MODEL_PATH}")

        # Build info labels
        build_info.labels(version=VERSION, git_sha=GIT_SHA).set(1)

    except Exception as e:
        print(f"[ERROR] Training failed: {e}")
        train_errors.inc()

    finally:
        request_latency.observe(time.perf_counter() - start)


def main() -> None:
    parser = argparse.ArgumentParser(description="Model trainer service with Prometheus metrics")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single training cycle and exit (useful for Jenkins CI).",
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="Do not start the Prometheus HTTP server (useful for CI runs).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL_SECONDS,
        help=f"Seconds to wait between training cycles (default: {DEFAULT_INTERVAL_SECONDS}).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port for Prometheus metrics server (default: {DEFAULT_PORT}).",
    )
    args = parser.parse_args()

    if not args.no_server:
        start_http_server(args.port)
        print(f"[INFO] Prometheus metrics exposed on port {args.port} (/metrics)")

    print(f"[INFO] Build info: VERSION={VERSION}, GIT_SHA={GIT_SHA}")
    print(f"[INFO] Model path: {MODEL_PATH}")

    if args.once:
        train_and_save_model()
        return

    while True:
        train_and_save_model()
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    main()