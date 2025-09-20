pipeline {
    agent any

    environment {
        // GitHub and Docker credentials stored in Jenkins
        GIT_CREDENTIALS = 'github-dreds'
        DOCKER_HUB_USER = credentials('docker-hub-username')
        DOCKER_HUB_PASS = credentials('docker-hub-password')

        // Docker Hub image repo
        IMAGE_NAME = "ggyabaah/ai-augmented-devops"

        // Python interpreter path
        PYTHON_PATH = "C:\\Program Files\\Python313\\python.exe"

        // Compose project name for orchestration clarity
        COMPOSE_PROJECT_NAME = "ai-devops-pipeline"
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', credentialsId: "${GIT_CREDENTIALS}", url: 'https://github.com/ggyabaah/ai-augmented-devops-pipeline.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '"${PYTHON_PATH}" -m pip install -r requirements.txt'
            }
        }

        stage('Train Model') {
            steps {
                sh '"${PYTHON_PATH}" scripts/train.py'
            }
        }

        stage('Test Model') {
            steps {
                sh '"${PYTHON_PATH}" scripts/test.py'
            }
        }

        stage('Docker Build & Push') {
            steps {
                script {
                    sh 'echo $DOCKER_HUB_PASS | docker login -u $DOCKER_HUB_USER --password-stdin'
                    sh 'docker build -t $IMAGE_NAME:$BUILD_NUMBER .'
                    sh 'docker push $IMAGE_NAME:$BUILD_NUMBER'
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh 'kubectl apply -f k8s/deployment.yml'
            }
        }

        stage('Docker Compose Orchestration') {
            steps {
                // Stop and clean up old containers
                bat 'docker-compose down || exit 0'

                // Start fresh with new containers
                bat 'docker-compose up --build -d'
            }
        }

        stage('Verify Trainer Service') {
            steps {
                // Run test container against trainer
                bat 'docker-compose run --rm tester'
            }
        }
    }

    post {
        always {
            echo 'Jenkins pipeline execution complete.'
            bat 'docker-compose down || exit 0'
        }
    }
}