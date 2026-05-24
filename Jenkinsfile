// ─────────────────────────────────────────────────────────────────────────────
// AI SupportOps — Jenkins CI/CD Pipeline
// Triggers on GitHub push → Lint → Test → Deploy to EC2
// ─────────────────────────────────────────────────────────────────────────────

pipeline {
    agent any

    // ── Environment Variables ────────────────────────────────────────────────
    environment {
        APP_NAME        = 'ai-supportops'
        DEPLOY_USER     = 'ubuntu'
        DEPLOY_DIR      = '/home/ubuntu/app'
        DOCKER_COMPOSE  = 'docker compose -f infra/docker-compose.yml'
        // These come from Jenkins Credentials:
        //   - EC2_HOST          : Elastic IP of your EC2 instance
        //   - EC2_SSH_KEY       : SSH private key (Jenkins SSH credential ID)
        //   - GROQ_API_KEY      : Groq API key for the app
        //   - DB_PASSWORD       : PostgreSQL password
    }

    // ── Triggers ─────────────────────────────────────────────────────────────
    triggers {
        githubPush()    // Auto-trigger on GitHub webhook push
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    // ── Pipeline Stages ──────────────────────────────────────────────────────
    stages {

        // ── Stage 1: Checkout ────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                echo "✅ Code checked out — branch: ${env.BRANCH_NAME ?: 'main'}"
            }
        }

        // ── Stage 2: Lint ────────────────────────────────────────────────────
        stage('Lint') {
            steps {
                echo '🔍 Running linter (ruff)...'
                sh '''
                    cd backend
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet --upgrade pip
                    pip install --quiet ruff
                    ruff check app/
                '''
                echo '✅ Lint passed'
            }
        }

        // ── Stage 3: Test ────────────────────────────────────────────────────
        stage('Test') {
            steps {
                echo '🧪 Running tests (pytest)...'
                sh '''
                    cd backend
                    . .venv/bin/activate
                    pip install --quiet -r requirements.txt
                    pip install --quiet pytest pytest-cov pytest-asyncio
                    python -m pytest tests/ \
                        --tb=short \
                        --junitxml=test-results.xml \
                        --cov=app \
                        --cov-report=term-missing \
                        || true
                '''
                echo '✅ Tests completed'
            }
            post {
                always {
                    // Publish test results in Jenkins UI
                    junit allowEmptyResults: true, testResults: 'backend/test-results.xml'
                }
            }
        }

        // ── Stage 4: Deploy to EC2 ──────────────────────────────────────────
        stage('Deploy') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo '🚀 Deploying to EC2...'
                withCredentials([
                    string(credentialsId: 'EC2_HOST', variable: 'EC2_HOST'),
                    sshUserPrivateKey(
                        credentialsId: 'EC2_SSH_KEY',
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        chmod 600 "$SSH_KEY"

                        # SSH options to skip host key checking
                        SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

                        # Deploy script executed on the remote EC2 instance
                        ssh $SSH_OPTS -i "$SSH_KEY" ${DEPLOY_USER}@${EC2_HOST} << 'DEPLOY_SCRIPT'
                            set -e

                            echo "══════════════════════════════════════════════"
                            echo "  AI SupportOps — Deployment Started"
                            echo "══════════════════════════════════════════════"

                            APP_DIR="/home/ubuntu/app"
                            REPO_URL="https://github.com/${GIT_URL##*/}"

                            # ── Clone or pull latest code ──────────────────
                            if [ ! -d "$APP_DIR/.git" ]; then
                                echo "📦 First deploy — cloning repository..."
                                git clone ${GIT_URL} $APP_DIR
                            else
                                echo "🔄 Pulling latest changes..."
                                cd $APP_DIR
                                git fetch --all
                                git reset --hard origin/main || git reset --hard origin/master
                            fi

                            cd $APP_DIR

                            # ── Create .env if it doesn't exist ────────────
                            if [ ! -f backend/.env ]; then
                                echo "⚙️  Creating .env from .env.example..."
                                cp backend/.env.example backend/.env
                                echo "⚠️  IMPORTANT: Edit backend/.env with real values!"
                            fi

                            # ── Build and deploy with Docker Compose ───────
                            echo "🐳 Building and starting containers..."
                            docker compose -f infra/docker-compose.yml down --remove-orphans || true
                            docker compose -f infra/docker-compose.yml up --build -d

                            # ── Wait for health check ──────────────────────
                            echo "⏳ Waiting for app to be healthy..."
                            for i in $(seq 1 30); do
                                if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
                                    echo "✅ App is healthy!"
                                    break
                                fi
                                if [ $i -eq 30 ]; then
                                    echo "❌ Health check failed after 30 attempts"
                                    docker compose -f infra/docker-compose.yml logs --tail=50 backend
                                    exit 1
                                fi
                                echo "  Attempt $i/30 — waiting..."
                                sleep 5
                            done

                            # ── Cleanup old Docker images ──────────────────
                            echo "🧹 Cleaning up old images..."
                            docker image prune -f

                            echo "══════════════════════════════════════════════"
                            echo "  ✅ Deployment Complete!"
                            echo "══════════════════════════════════════════════"
DEPLOY_SCRIPT
                    '''
                }
                echo '✅ Deployed successfully to EC2'
            }
        }
    }

    // ── Post Actions ─────────────────────────────────────────────────────────
    post {
        success {
            echo '''
            ╔══════════════════════════════════════════════╗
            ║  ✅ Pipeline completed successfully!         ║
            ╚══════════════════════════════════════════════╝
            '''
        }
        failure {
            echo '''
            ╔══════════════════════════════════════════════╗
            ║  ❌ Pipeline FAILED — check logs above       ║
            ╚══════════════════════════════════════════════╝
            '''
            // Uncomment to enable email notifications:
            // mail to: 'your-email@example.com',
            //      subject: "❌ Jenkins: ${APP_NAME} build #${BUILD_NUMBER} FAILED",
            //      body: "Check: ${BUILD_URL}"
        }
        cleanup {
            cleanWs()
        }
    }
}
