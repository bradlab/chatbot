pipeline {
    agent any

    options {
        ansiColor('xterm')
    }

    environment {
        // Define environment variables here
        BOT_NAME = 'awesome-bot'
        // BOT_TOKEN = credentials('telegram-bot-token')
    }

    stages {
        stage('Initialisation') {
            steps {
                sh "echo Branch name ${BRANCH_NAME}"
                sh "make venv && make install"
                sh "test dev"
            }
        }


        stage('Test Unitaire') {
            steps {
                script {
                    echo "Running tests..."
                    // Add your test commands here
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    echo "Building the project..."
                    // Add your build commands here
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo "Deploying the project..."
                    // Add your deployment commands here
                }
            }
        }
    }

}