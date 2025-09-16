pipeline {
    agent any

    environment {
        PYTHON_EXE = '"C:\\Program Files\\Python313\\python.exe"'
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', credentialsId: 'github-dreds', url: 'https://github.com/ggyabaah/ai-augmented-devops-pipeline.git'
            }
        }

        stage('Recreate Folders & Scripts') {
            steps {
                bat '''
                REM --- Ensure scripts folder exists ---
                if not exist scripts mkdir scripts

                REM --- Ensure model folder exists ---
                if not exist model mkdir model

                REM --- Create train.py ---
                echo import joblib > scripts\\train.py
                echo from sklearn.datasets import load_iris >> scripts\\train.py
                echo from sklearn.ensemble import RandomForestClassifier >> scripts\\train.py
                echo from sklearn.model_selection import train_test_split >> scripts\\train.py
                echo from sklearn.metrics import accuracy_score >> scripts\\train.py
                echo import os >> scripts\\train.py
                echo iris = load_iris() >> scripts\\train.py
                echo X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.2, random_state=42) >> scripts\\train.py
                echo model = RandomForestClassifier(n_estimators=100, random_state=42) >> scripts\\train.py
                echo model.fit(X_train, y_train) >> scripts\\train.py
                echo joblib.dump(model, "model/random_forest_model.pkl") >> scripts\\train.py
                echo print("[INFO] Model trained and saved.") >> scripts\\train.py

                REM --- Create test.py ---
                echo import joblib > scripts\\test.py
                echo from sklearn.datasets import load_iris >> scripts\\test.py
                echo from sklearn.metrics import accuracy_score >> scripts\\test.py
                echo iris = load_iris() >> scripts\\test.py
                echo X, y = iris.data, iris.target >> scripts\\test.py
                echo model = joblib.load("model/random_forest_model.pkl") >> scripts\\test.py
                echo predictions = model.predict(X) >> scripts\\test.py
                echo print("[INFO] Accuracy:", accuracy_score(y, predictions)) >> scripts\\test.py
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                bat "${PYTHON_EXE} -m pip install --upgrade pip"
                bat "${PYTHON_EXE} -m pip install -r requirements.txt"
            }
        }

        stage('Train ML Model') {
            steps {
                bat "${PYTHON_EXE} scripts\\train.py"
            }
        }

        stage('Test ML Model') {
            steps {
                bat "${PYTHON_EXE} scripts\\test.py"
            }
        }
    }

    post {
        always {
            echo 'Jenkins pipeline execution complete.'
        }
    }
}