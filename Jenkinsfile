pipeline {
    agent any

    environment {
        VENV = 'venv'
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', credentialsId: 'github-dreds', url: 'https://github.com/ggyabaah/ai-augmented-devops-pipeline.git'
            }
        }

        stage('Set Up Python Virtual Environment') {
            steps {
                bat 'python -m venv %VENV%'
                bat '%VENV%\\Scripts\\activate && python -m pip install --upgrade pip'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '%VENV%\\Scripts\\activate && pip install -r requirements.txt'
            }
        }

        stage('Train ML Model') {
            steps {
                bat '%VENV%\\Scripts\\activate && python model\\train.py'
            }
        }

        stage('Test ML Model') {
            steps {
                bat '%VENV%\\Scripts\\activate && python model\\test.py'
            }
        }
    }

    post {
        always {
            echo 'Jenkins pipeline execution complete.'
        }
    }
}