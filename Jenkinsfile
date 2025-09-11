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
                script {
                    docker.build("${IMAGE_NAME}")
                }
            }
        }

        stage('Run ML Model in Docker') {
            steps {
                script {
                    docker.image("${IMAGE_NAME}").inside {
                        sh 'python model/train.py'
                        sh 'python model/test.py'
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Jenkins pipeline execution complete.'
        }
    }
}