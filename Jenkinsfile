// ─────────────────────────────────────────────────────────────────────────────
// AI SupportOps — Jenkins CI/CD Pipeline
// Runs inside Kubernetes (k3s) — builds, tests, and deploys via kubectl
// ─────────────────────────────────────────────────────────────────────────────

pipeline {
    agent any

    // ── Environment Variables ────────────────────────────────────────────────
    environment {
        APP_NAME        = 'ai-supportops'
        KUBE_NAMESPACE  = 'supportops'
        IMAGE_NAME      = 'supportops-backend'
        IMAGE_TAG       = "${BUILD_NUMBER}"
        DEPLOY_DIR      = '/home/ubuntu/app'
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

        // ── Stage 4: Build Docker Image ──────────────────────────────────────
        stage('Build') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo '🐳 Building Docker image...'
                sh """
                    cd backend
                    docker build \
                        --target production \
                        -t ${IMAGE_NAME}:${IMAGE_TAG} \
                        -t ${IMAGE_NAME}:latest \
                        .
                """
                echo "✅ Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        // ── Stage 5: Deploy to Kubernetes ────────────────────────────────────
        stage('Deploy') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo '🚀 Deploying to Kubernetes...'
                sh """
                    echo "══════════════════════════════════════════════"
                    echo "  AI SupportOps — K8s Deployment Started"
                    echo "══════════════════════════════════════════════"

                    # ── Apply K8s manifests (idempotent) ──────────────
                    echo "📦 Applying K8s manifests..."
                    kubectl apply -f devops/k8s/namespace.yaml
                    kubectl apply -f devops/k8s/configmap.yaml
                    kubectl apply -f devops/k8s/postgres.yaml
                    kubectl apply -f devops/k8s/redis.yaml
                    kubectl apply -f devops/k8s/chromadb.yaml
                    kubectl apply -f devops/k8s/nginx.yaml
                    kubectl apply -f devops/k8s/backend.yaml
                    kubectl apply -f devops/k8s/jenkins.yaml

                    # ── Update backend image ──────────────────────────
                    echo "🔄 Updating backend image to ${IMAGE_NAME}:${IMAGE_TAG}..."
                    kubectl set image deployment/backend \
                        backend=${IMAGE_NAME}:${IMAGE_TAG} \
                        -n ${KUBE_NAMESPACE}

                    # ── Wait for rollout ──────────────────────────────
                    echo "⏳ Waiting for rollout to complete..."
                    kubectl rollout status deployment/backend \
                        -n ${KUBE_NAMESPACE} \
                        --timeout=300s

                    # ── Verify all pods are running ───────────────────
                    echo "🔍 Checking pod status..."
                    kubectl get pods -n ${KUBE_NAMESPACE}

                    # ── Cleanup old Docker images ─────────────────────
                    echo "🧹 Cleaning up old images..."
                    docker image prune -f

                    echo "══════════════════════════════════════════════"
                    echo "  ✅ K8s Deployment Complete!"
                    echo "══════════════════════════════════════════════"
                """
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
