pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'ai-devops-pipeline'
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
                    dockerImage = docker.build("${DOCKER_IMAGE}")
                }
            }
        }

        stage('Train ML Model in Docker') {
            steps {
                script {
                    dockerImage.inside {
                        sh 'python scripts/train.py'
                    }
                }
            }
        }

        stage('Test ML Model in Docker') {
            steps {
                script {
                    dockerImage.inside {
                        sh 'python scripts/test.py'
                    }
                }
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