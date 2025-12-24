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
      description: 'Force a failure to simulate a faulty commit (used to test alerting).'
    )
    booleanParam(
      name: 'KEEP_STACK',
      defaultValue: true,
      description: 'Keep Prometheus/Grafana/Pushgateway running after the build for inspection.'
    )
    booleanParam(
      name: 'RESET_STACK_FIRST',
      defaultValue: false,
      description: 'If true, bring the Compose stack down at the start (clean slate).'
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

    // Pushgateway (host-mapped port in your compose)
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

    stage('Compose Down (optional clean slate)') {
      when {
        expression { return params.RESET_STACK_FIRST }
      }
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
        script {
          // Option 1: Jenkins parameter
          if (params.INJECT_FAULT) {
            error('Fault injection enabled (INJECT_FAULT=true). Forcing pipeline failure to simulate faulty commit.')
          }

          // Option 2: Repo flag file
          if (fileExists('fault.flag')) {
            def txt = readFile('fault.flag').trim().toLowerCase()
            if (txt.contains('fail_deploy=true')) {
              error('fault.flag contains FAIL_DEPLOY=true. Forcing pipeline failure to simulate faulty commit.')
            }
          }

          echo 'No fault injection requested. Continuing.'
        }
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
      echo 'Build SUCCESS: pushing success metrics to Pushgateway...'
      bat '''
        powershell -NoProfile -Command ^
          "$ts = [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); ^
           $v  = [int]$env:BUILD_NUMBER; ^
           $body  = 'deployments_total{pipeline=\"%PIPELINE_LABEL%\"} ' + $v + \"`n\"; ^
           $body += 'deployments_success_timestamp_seconds{pipeline=\"%PIPELINE_LABEL%\"} ' + $ts + \"`n\"; ^
           Invoke-WebRequest -Uri '%PUSHGATEWAY_BASE_URL%/metrics/job/deployments/instance/success' -Method POST -ContentType 'text/plain' -Body $body | Out-Null"
      '''
    }

    failure {
      echo 'Build FAILURE: pushing failure metrics to Pushgateway...'
      bat '''
        powershell -NoProfile -Command ^
          "$ts = [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); ^
           $v  = [int]$env:BUILD_NUMBER; ^
           $body  = 'deployments_failed_total{pipeline=\"%PIPELINE_LABEL%\"} ' + $v + \"`n\"; ^
           $body += 'deployments_failed_timestamp_seconds{pipeline=\"%PIPELINE_LABEL%\"} ' + $ts + \"`n\"; ^
           Invoke-WebRequest -Uri '%PUSHGATEWAY_BASE_URL%/metrics/job/deployments/instance/failure' -Method POST -ContentType 'text/plain' -Body $body | Out-Null"
      '''
    }

    always {
      script {
        if (params.KEEP_STACK) {
          echo 'KEEP_STACK=true, leaving stack running for Grafana/Prometheus inspection.'
          echo "Grafana:      http://127.0.0.1:13001"
          echo "Prometheus:   http://127.0.0.1:19090"
          echo "Pushgateway:  http://127.0.0.1:19091"
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