pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }

  environment {
    // Git
    GIT_CREDENTIALS      = 'github-dreds'
    GIT_URL              = 'https://github.com/ggyabaah/ai-augmented-devops-pipeline.git'
    GIT_BRANCH           = 'main'

    // App
    IMAGE_NAME           = 'ggyabaah/ai-augmented-devops'
    PYTHON_PATH          = 'C:\\Program Files\\Python313\\python.exe'

    // Compose
    COMPOSE_PROJECT_NAME = 'ai-devops-pipeline'
    ENV_FILE             = '%WORKSPACE%\\.env'

    // If you ever re-enable k8s from Jenkins, uncomment and set correctly
    // KUBECONFIG        = 'C:\\Users\\fritz\\.kube\\config'
  }

  stages {

    stage('Checkout') {
      steps {
        checkout([$class: 'GitSCM',
          branches: [[name: "*/${env.GIT_BRANCH}"]],
          userRemoteConfigs: [[url: env.GIT_URL, credentialsId: env.GIT_CREDENTIALS]]
        ])
      }
    }

    stage('Sanity Checks') {
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          echo === Workspace ===
          dir

          echo === Required files ===
          if not exist "docker-compose.yml" (echo ERROR: docker-compose.yml missing & exit /b 1)
          if not exist ".env" (echo ERROR: .env missing & exit /b 1)
          if not exist "requirements.txt" (echo ERROR: requirements.txt missing & exit /b 1)

          echo === .env (redact nothing sensitive!) ===
          type ".env"
        '''
      }
    }

    stage('Tooling Check') {
      steps {
        bat '''
          where docker
          docker version
          docker compose version
          docker info
        '''
      }
    }

    stage('Python Dependencies') {
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          "%PYTHON_PATH%" -m pip install --upgrade pip
          "%PYTHON_PATH%" -m pip install -r requirements.txt
          "%PYTHON_PATH%" -m pip install pytest
        '''
      }
    }

    stage('Unit Tests') {
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          if not exist test-results mkdir test-results
          "%PYTHON_PATH%" -m pytest -v --junitxml=test-results\\pytest-results.xml
        '''
      }
      post {
        always {
          junit 'test-results/*.xml'
        }
      }
    }

    stage('Train Model (CI One Run)') {
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          "%PYTHON_PATH%" scripts\\train.py --once --no-server
        '''
      }
    }

    stage('Test Model (CI One Run)') {
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          "%PYTHON_PATH%" scripts\\test.py --once --no-server
        '''
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

              docker build -t %IMAGE_NAME%:%BUILD_NUMBER% -t %IMAGE_NAME%:latest .
              docker push %IMAGE_NAME%:%BUILD_NUMBER%
              docker push %IMAGE_NAME%:latest
            '''
          }
        }
      }
    }

    stage('Compose Down (safe)') {
      steps {
        // Never fail build for a missing project
        bat '''
          cd /d "%WORKSPACE%"
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" down --remove-orphans
          exit /b 0
        '''
      }
    }

    stage('Compose Up') {
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" up -d --build
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" ps
        '''
      }
    }

    stage('Verify Metrics Endpoints (fast)') {
      options { timeout(time: 3, unit: 'MINUTES') }
      steps {
        // Verify inside the Compose network so we don't care about host port clashes
        bat '''
          cd /d "%WORKSPACE%"

          echo === Verify trainer metrics (inside network) ===
          docker run --rm --network %COMPOSE_PROJECT_NAME%_monitoring curlimages/curl:8.10.1 -s http://trainer:8000/metrics

          echo === Verify tester metrics (inside network) ===
          docker run --rm --network %COMPOSE_PROJECT_NAME%_monitoring curlimages/curl:8.10.1 -s http://tester:8001/metrics

          echo === Verify pushgateway ready (inside network) ===
          docker run --rm --network %COMPOSE_PROJECT_NAME%_monitoring curlimages/curl:8.10.1 -s http://pushgateway:9091/-/ready
        '''
      }
    }

    stage('Verify Tester One-Shot (no hang)') {
      options { timeout(time: 5, unit: 'MINUTES') }
      steps {
        // Do NOT run the long-lived service. Force a one-shot command so Jenkins doesn't hang.
        bat '''
          cd /d "%WORKSPACE%"
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" run --rm tester python -u scripts/test.py --once --no-server
        '''
      }
    }

    stage('Compose Logs (last 80 lines)') {
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" logs --tail=80
        '''
      }
    }

    // Optional: re-enable later once kubectl from Jenkins is stable
    // stage('Deploy to Kubernetes') {
    //   steps {
    //     bat '''
    //       cd /d "%WORKSPACE%"
    //       kubectl config current-context
    //       kubectl get nodes
    //       kubectl apply -f k8s\\deployment.yml
    //     '''
    //   }
    // }
  }

  post {
    always {
      echo 'Pipeline complete. Cleaning up Compose stack...'
      // Cleanup but don’t fail the job if cleanup has issues
      script {
        try {
          bat '''
            cd /d "%WORKSPACE%"
            docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" down --remove-orphans
          '''
        } catch (err) {
          echo "Cleanup failed safely: ${err}"
        }
      }
    }

    failure {
      echo 'Build failed. Showing Compose status + recent logs.'
      script {
        try {
          bat '''
            cd /d "%WORKSPACE%"
            docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" ps
            docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" logs --tail=120
          '''
        } catch (err) {
          echo "Diagnostics failed safely: ${err}"
        }
      }
    }
  }
}