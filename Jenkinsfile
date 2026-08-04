pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/YuliyaS-work/Notification_Service.git'
            }
        }

             stage('Install uv') {
            steps {
                sh 'pip install uv'
                sh 'uv sync'
            }
        }

        stage('Lint/Format') {
            steps {
                sh 'uv run black .'
                sh 'uv run flake8 .'
            }
        }

        stage('Tests') {
            steps {
                sh 'uv run pytest --cov=.'
            }
        }

        stage('Build Docker') {
            steps {
                sh 'docker build -t notification-2/notification:latest .'
            }
        }

        stage('Push Docker') {
            steps {
                sh 'docker login -u $DOCKER_USER -p $DOCKER_PASS'
                sh 'docker push notification-2/notification:latest'
            }
        }

        stage('Deploy to minikube') {
            steps {
                sh 'kubectl apply -f ../infrastructure/k8s/notification-deployment.yaml'
                sh 'kubectl rollout restart deployment notification -n app'
            }
        }
    }
}