pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    skipDefaultCheckout(true)
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }

  environment {
    // Git
    GIT_CREDENTIALS = 'github-dreds'
    GIT_URL         = 'https://github.com/ggyabaah/ai-augmented-devops-pipeline.git'
    GIT_BRANCH      = 'main'

    // App
    IMAGE_NAME      = 'ggyabaah/ai-augmented-devops'
    PYTHON_PATH     = 'C:\\Program Files\\Python313\\python.exe'

    // Compose
    COMPOSE_PROJECT_NAME = 'ai-devops-pipeline'
    ENV_FILE             = '.env'
    CURL_IMAGE           = 'curlimages/curl:8.10.1'
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
          if not exist "%ENV_FILE%" (echo ERROR: .env missing in workspace root & exit /b 1)
          if not exist "requirements.txt" (echo ERROR: requirements.txt missing & exit /b 1)

          echo === .env (ports only recommended) ===
          type "%ENV_FILE%"
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
              echo %DOCKER_HUB_PASS% | docker login -u %DOCKER_HUB_USER% --password-stdin

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
        bat '''
          cd /d "%WORKSPACE%"
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" down --remove-orphans || echo Nothing to remove.
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

    stage('Pre-pull Curl (fast)') {
      options { timeout(time: 3, unit: 'MINUTES') }
      steps {
        bat 'docker pull %CURL_IMAGE%'
      }
    }

    stage('Verify Containers Running (fast)') {
      options { timeout(time: 2, unit: 'MINUTES') }
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" ps

          REM Fail if any service is not running
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" ps --status running | findstr /I "trainer tester prometheus grafana pushgateway alertmanager" > NUL
          if errorlevel 1 (
            echo ERROR: One or more services are not running.
            docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" ps
            exit /b 1
          )
        '''
      }
    }

    stage('Verify Metrics Endpoints (no hang)') {
      options { timeout(time: 3, unit: 'MINUTES') }
      steps {
        // Use files + PowerShell to print first lines (no "more" pager).
        bat '''
          cd /d "%WORKSPACE%"
          set NET=%COMPOSE_PROJECT_NAME%_monitoring

          echo === Network: %NET% ===
          docker network ls | findstr /I "%NET%" || (echo ERROR: Compose network not found & exit /b 1)

          echo === Trainer metrics (first 25 lines) ===
          docker run --rm --network %NET% %CURL_IMAGE% -sS --fail --max-time 10 http://trainer:8000/metrics > trainer_metrics.txt
          powershell -NoProfile -Command "Get-Content trainer_metrics.txt | Select-Object -First 25"
          del trainer_metrics.txt

          echo === Tester metrics (first 25 lines) ===
          docker run --rm --network %NET% %CURL_IMAGE% -sS --fail --max-time 10 http://tester:8001/metrics > tester_metrics.txt
          powershell -NoProfile -Command "Get-Content tester_metrics.txt | Select-Object -First 25"
          del tester_metrics.txt

          echo === Pushgateway ready ===
          docker run --rm --network %NET% %CURL_IMAGE% -sS --fail --max-time 10 http://pushgateway:9091/-/ready > NUL
        '''
      }
    }

    stage('Verify Tester One-Shot (no hang)') {
      options { timeout(time: 5, unit: 'MINUTES') }
      steps {
        // Key changes:
        // -T disables pseudo-TTY (common Jenkins hang cause)
        // one-shot flags ensure script exits
        bat '''
          cd /d "%WORKSPACE%"
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" run --rm -T tester python -u scripts/test.py --once --no-server
        '''
      }
    }

    stage('Compose Logs (last 120 lines)') {
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" logs --tail=120
        '''
      }
    }
  }

  post {
    always {
      echo 'Pipeline complete. Cleaning up Compose stack...'
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
            docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" logs --tail=200
          '''
        } catch (err) {
          echo "Diagnostics failed safely: ${err}"
        }
      }
    }
  }
}