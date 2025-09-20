# scripts/test.py
import os, time, joblib
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

test_counter = Counter("model_test_runs", "Number of times model testing executed")
test_accuracy = Gauge("model_test_accuracy", "Model accuracy from last test run")
test_duration = Histogram("test_duration_seconds", "Time taken to run evaluation")
build_info = Gauge("model_build_info", "Build info as labels", ["version", "git_sha"])

VERSION = os.getenv("VERSION", "dev")
GIT_SHA = os.getenv("GIT_SHA", "local")
MODEL_PATH = os.path.join(os.getenv("MODEL_DIR", "model"), "random_forest_model.pkl")

def run_test_once():
    start = time.perf_counter()
    if not os.path.exists(MODEL_PATH):
        print(f"[WARN] Model not found at {MODEL_PATH}. Waiting for trainer...")
        return

    model = joblib.load(MODEL_PATH)
    iris = load_iris()
    _, X_test, _, y_test = train_test_split(iris.data, iris.target, test_size=0.2, random_state=42)
    acc = accuracy_score(y_test, model.predict(X_test))

    test_counter.inc()
    test_accuracy.set(acc)
    test_duration.observe(time.perf_counter() - start)
    build_info.labels(version=VERSION, git_sha=GIT_SHA).set(1)
    print(f"[INFO] Test accuracy: {acc:.2f}")

if __name__ == "__main__":
    start_http_server(8001)
    print("[INFO] Prometheus test metrics on :8001 (/metrics)")
    while True:
        run_test_once()
        time.sleep(60)