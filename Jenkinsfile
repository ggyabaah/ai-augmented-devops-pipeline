pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    skipDefaultCheckout(true)
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }

  parameters {
    booleanParam(
      name: 'INJECT_FAULT',
      defaultValue: false,
      description: 'Simulate a faulty commit by forcing the pipeline to fail after the stack is up.'
    )
    booleanParam(
      name: 'KEEP_STACK',
      defaultValue: true,
      description: 'Leave Prometheus/Grafana/Pushgateway running after the build for inspection.'
    )
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

    // Pushgateway (host-mapped port from your docker ps output)
    PUSHGATEWAY_BASE_URL = 'http://127.0.0.1:19091'
    PIPELINE_LABEL       = 'ai-augmented-devops'
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
          echo === Required files ===
          if not exist "docker-compose.yml" (echo ERROR: docker-compose.yml missing & exit /b 1)
          if not exist "%ENV_FILE%" (echo ERROR: .env missing in workspace root & exit /b 1)
          if not exist "requirements.txt" (echo ERROR: requirements.txt missing & exit /b 1)
        '''
      }
    }

    stage('Tooling Check') {
      steps {
        bat '''
          where docker
          docker version
          docker compose version
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

    stage('Pre-pull Curl (avoid first-run delays)') {
      options { timeout(time: 3, unit: 'MINUTES') }
      steps {
        bat 'docker pull %CURL_IMAGE%'
      }
    }

    stage('Compose Up (NO tester service)') {
      options { timeout(time: 8, unit: 'MINUTES') }
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" up -d --build trainer pushgateway prometheus alertmanager grafana
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" ps
        '''
      }
    }

    stage('Verify Trainer Metrics (fast)') {
      options { timeout(time: 3, unit: 'MINUTES') }
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          set NET=%COMPOSE_PROJECT_NAME%_monitoring

          docker run --rm --network %NET% %CURL_IMAGE% -sS --fail --max-time 10 http://trainer:8000/metrics > trainer_metrics.txt

          echo === Key metric lines (if present) ===
          findstr /I "python_ process_ deployments_total" trainer_metrics.txt || echo (No matching lines found)

          del trainer_metrics.txt
        '''
      }
    }

    stage('Fault Injection Check (simulate faulty commit)') {
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          echo === Fault Injection Check ===
          echo INJECT_FAULT param: %INJECT_FAULT%

          rem Option 1: Jenkins parameter
          if /I "%INJECT_FAULT%"=="true" (
            echo Fault injection enabled via parameter. Forcing failure now.
            exit /b 1
          )

          rem Option 2: Repo file flag (fault.flag containing FAIL_DEPLOY=true)
          if exist "fault.flag" (
            findstr /I "FAIL_DEPLOY=true" fault.flag >nul 2>&1
            if %errorlevel%==0 (
              echo fault.flag detected with FAIL_DEPLOY=true. Forcing failure now.
              exit /b 1
            )
          )

          echo No fault injection requested. Continuing.
        '''
      }
    }

    stage('Verify Tester One-Shot (NO HANG)') {
      options { timeout(time: 5, unit: 'MINUTES') }
      steps {
        bat '''
          cd /d "%WORKSPACE%"
          docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" run --rm tester python -u scripts/test.py --once --no-server
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

    success {
      echo 'Build SUCCESS: pushing deployments_total to Pushgateway...'
      bat '''
        powershell -NoProfile -Command ^
          "$body = 'deployments_total{pipeline=\"%PIPELINE_LABEL%\"} 1`n'; ^
           Invoke-WebRequest -Uri '%PUSHGATEWAY_BASE_URL%/metrics/job/deployments/instance/success' -Method POST -ContentType 'text/plain' -Body $body | Out-Null"
      '''
    }

    failure {
      echo 'Build FAILURE: pushing deployments_failed_total to Pushgateway...'
      bat '''
        powershell -NoProfile -Command ^
          "$body = 'deployments_failed_total{pipeline=\"%PIPELINE_LABEL%\"} 1`n'; ^
           Invoke-WebRequest -Uri '%PUSHGATEWAY_BASE_URL%/metrics/job/deployments/instance/failure' -Method POST -ContentType 'text/plain' -Body $body | Out-Null"
      '''
    }

    always {
      script {
        if (params.KEEP_STACK) {
          echo 'KEEP_STACK=true, leaving Compose stack running for Grafana/Prometheus inspection.'
        } else {
          echo 'KEEP_STACK=false, cleaning up Compose stack...'
          bat '''
            cd /d "%WORKSPACE%"
            docker compose --env-file "%ENV_FILE%" -p "%COMPOSE_PROJECT_NAME%" down --remove-orphans || exit /b 0
          '''
        }
      }
    }
  }
}