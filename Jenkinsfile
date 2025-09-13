pipeline {
    agent any

    environment {
        IMAGE_NAME = 'ai-devops-pipeline'
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', credentialsId: 'github-dreds', url: 'https://github.com/ggyabaah/ai-augmented-devops-pipeline.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat "docker build -t %IMAGE_NAME% ."
            }
        }

        stage('Train ML Model in Docker') {
            steps {
                bat "docker run --rm %IMAGE_NAME% python model/train.py"
            }
        }

        stage('Test ML Model in Docker') {
            steps {
                bat "docker run --rm %IMAGE_NAME% python model/test.py"
            }
        }
    }

    post {
        always {
            echo 'Jenkins pipeline execution complete.'
        }
    }
}