pipeline {
  agent any

  environment {
    // GitHub credentials stored in Jenkins
    GIT_CREDENTIALS = 'github-dreds'

    // Docker Hub image repo
    IMAGE_NAME = "ggyabaah/ai-augmented-devops"

    // Python interpreter path
    PYTHON_PATH = "C:\\Program Files\\Python313\\python.exe"

    // Compose project name (Compose uses this for naming containers/networks)
    COMPOSE_PROJECT_NAME = "ai-devops-pipeline"

    // .env file location (must exist in repo root after checkout)
    ENV_FILE = "%WORKSPACE%\\.env"

    // Optional (only if you still deploy to Minikube from Jenkins)
    // KUBECONFIG = "C:\\Users\\fritz\\.kube\\config"
  }

  stages {

    stage('Checkout Code') {
      steps {
        git branch: 'main',
          credentialsId: "${GIT_CREDENTIALS}",
          url: 'https://github.com/ggyabaah/ai-augmented-devops-pipeline.git'
      }
    }

    stage('Sanity Check (Workspace + .env)') {
      steps {
        bat 'cd /d "%WORKSPACE%" && dir'
        bat 'cd /d "%WORKSPACE%" && if not exist ".env" (echo ERROR: .env missing in workspace & exit /b 1)'
        bat 'cd /d "%WORKSPACE%" && type .env'
        bat 'cd /d "%WORKSPACE%" && if not exist "docker-compose.yml" (echo ERROR: docker-compose.yml missing & exit /b 1)'
      }
    }

    stage('Check Tooling (Docker + Compose)') {
      steps {
        bat 'where docker'
        bat 'docker version'
        bat 'docker info'
        bat 'docker compose version'
      }
    }

    stage('Install Dependencies') {
      steps {
        bat 'cd /d "%WORKSPACE%" && "%PYTHON_PATH%" -m pip install --upgrade pip'
        bat 'cd /d "%WORKSPACE%" && "%PYTHON_PATH%" -m pip install -r requirements.txt'
      }
    }

    stage('Unit Tests') {
      steps {
        bat 'cd /d "%WORKSPACE%" && if not exist test-results mkdir test-results'
        bat 'cd /d "%WORKSPACE%" && "%PYTHON_PATH%" -m pip install pytest'
        bat 'cd /d "%WORKSPACE%" && "%PYTHON_PATH%" -m pytest -v --junitxml=test-results\\pytest-results.xml'
      }
      post {
        always {
          junit 'test-results/*.xml'
        }
      }
    }

    stage('Train Model (CI One Run)') {
      steps {
        // If your train.py runs a server/loop, add flags like you did for test.py
        // Adjust flags to match your script
        bat 'cd /d "%WORKSPACE%" && "%PYTHON_PATH%" scripts\\train.py --once --no-server'
      }
    }

    stage('Test Model (CI One Run)') {
      steps {
        bat 'cd /d "%WORKSPACE%" && "%PYTHON_PATH%" scripts\\test.py --once --no-server'
      }
    }

    stage('Docker Build & Push') {
      steps {
        script {
          withCredentials([usernamePassword(
            credentialsId: 'docker-hub-creds',
            usernameVariable: 'DOCKER_HUB_USER',
            passwordVariable: 'DOCKER_HUB_PASS'
          )]) {
            bat '''
              cd /d "%WORKSPACE%"
              echo %DOCKER_HUB_PASS%> docker_pass.txt
              docker login -u %DOCKER_HUB_USER% --password-stdin < docker_pass.txt
              del docker_pass.txt
            '''
            bat 'cd /d "%WORKSPACE%" && docker build -t %IMAGE_NAME%:%BUILD_NUMBER% -t %IMAGE_NAME%:latest .'
            bat 'cd /d "%WORKSPACE%" && docker push %IMAGE_NAME%:%BUILD_NUMBER%'
            bat 'cd /d "%WORKSPACE%" && docker push %IMAGE_NAME%:latest'
          }
        }
      }
    }

    // If Kubernetes from Jenkins is still flaky, leave this stage disabled for now
    // stage('Deploy to Kubernetes') {
    //   steps {
    //     bat 'cd /d "%WORKSPACE%" && kubectl config current-context'
    //     bat 'cd /d "%WORKSPACE%" && kubectl get nodes'
    //     bat 'cd /d "%WORKSPACE%" && kubectl apply -f k8s\\deployment.yml'
    //   }
    // }

    stage('Docker Compose Orchestration (with .env)') {
      steps {
        // CLEAN DOWN FIRST (do not fail build if nothing exists)
        bat 'cd /d "%WORKSPACE%" && docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" down --remove-orphans'
        // UP
        bat 'cd /d "%WORKSPACE%" && docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" up -d --build'
        // SHOW
        bat 'cd /d "%WORKSPACE%" && docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" ps'
      }
    }

    stage('Verify Service Health') {
      steps {
        // Optional: quick visibility into container logs if something fails
        bat 'cd /d "%WORKSPACE%" && docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" logs --tail=50'
      }
    }

  }

  post {
    always {
      echo 'Jenkins pipeline execution complete.'
      // Cleanup but don’t fail the job if cleanup has issues
      script {
        try {
          bat 'cd /d "%WORKSPACE%" && docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" down --remove-orphans'
        } catch (err) {
          echo "Cleanup failed safely: ${err}"
        }
      }
    }
  }
}