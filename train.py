import time
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load the dataset
print("Loading dataset...")
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.2)

# Train the model
print("Training RandomForest model...")
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Evaluate the model
print("Evaluating model...")
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Model Accuracy: {accuracy:.2f}")

time.sleep(2)
print("Training completed successfully.")