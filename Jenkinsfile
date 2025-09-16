pipeline {
    agent any

    environment {
        MODEL_DIR = "C:/ProgramData/Jenkins/.jenkins/workspace/AI-Augmented-DevOps/model"
    }

    stages {
        stage('Clean Workspace & Docker') {
            steps {
                echo "Cleaning workspace and Docker environment..."
                deleteDir()
                bat '''
                echo Cleaning Docker...
                docker ps -aq | findstr . >nul && docker stop $(docker ps -aq) || echo No running containers
                docker ps -aq | findstr . >nul && docker rm $(docker ps -aq) || echo No containers to remove
                docker images -q ai-devops-pipeline | findstr . >nul && docker rmi -f ai-devops-pipeline || echo No old ai-devops-pipeline image
                '''
            }
        }

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
                bat "docker run --rm -v %MODEL_DIR%:/app/model ai-devops-pipeline python scripts/train.py"
            }
        }

        stage('Test ML Model in Docker') {
            steps {
                echo "Testing ML model inside Docker..."
                bat "docker run --rm -v %MODEL_DIR%:/app/model ai-devops-pipeline python scripts/test.py"
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