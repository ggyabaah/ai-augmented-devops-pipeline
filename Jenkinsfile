pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', credentialsId: 'github-dreds', url: 'https://github.com/ggyabaah/ai-augmented-devops-pipeline.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker image..."
                bat 'docker build -t ai-devops-pipeline .'
            }
        }

        stage('Train ML Model in Docker') {
            steps {
                echo "Training ML model inside Docker..."
                bat 'docker run --rm ai-devops-pipeline python scripts/train.py'
            }
        }

        stage('Test ML Model in Docker') {
            steps {
                echo "Testing ML model inside Docker..."
                bat 'docker run --rm ai-devops-pipeline python scripts/test.py'
            }
        }
    }

    post {
        always {
            echo 'Jenkins pipeline execution complete.'
        }
        failure {
            echo 'Pipeline failed. Please check logs.'
        }
    }
}