pipeline {

    agent any

    stages {

        stage('Python CI (Install, Lint, Tests)') {
            agent {
                docker {
                    image 'python:3.13'
                    args '-u root'
                }
            }
            steps {
                 sh 'pip install uv'
                 sh 'uv sync'

                sh 'uv run ruff format .'
                sh 'uv run ruff check .'

                withEnv([
                    'MONGO_URL=mongodb://localhost:27017/test',
                    'AWS_ACCESS_KEY_ID=test',
                    'AWS_SECRET_ACCESS_KEY=test',
                    'AWS_REGION=us-east-1',
                    'SES_EMAIL_FROM=user@example.com',
                    'BUCKET_NAME=test',
                    'RABBITMQ_URL=amqp://guest:guest@localhost/'
                ]) {
                    sh 'uv run coverage run -m pytest'
                    sh 'uv run coverage report'
                }
            }
        }

        stage('Build Docker') {
            steps {
                sh 'docker build -t yuliyaswork/notification:latest .'
            }
        }

        stage('Push Docker') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                    sh 'docker login -u $DOCKER_USER -p $DOCKER_PASS'
                    sh 'docker push yuliyaswork/notification:latest'
                }
            }
        }

//         stage('Deploy to minikube') {
//             steps {
//                 sh 'kubectl apply -f ../infrastructure/k8s/notification-deployment.yaml'
//                 sh 'kubectl rollout restart deployment notification -n app'
//             }
//         }
    }
}