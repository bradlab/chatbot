pipeline {
    agent any

    options {
        ansiColor('xterm')
    }

    environment {
        // Define environment variables here
        BOT_NAME = 'awesome-bot'
        TELEGRAM_BOT_TOKEN = credentials('telegram-bot-token')
        MISTRAL_API_KEY = credentials('mistral-api-key')
    }

    stages {
        stage('Initialisation') {
            steps {
                sh "echo Branch name ${BRANCH_NAME}"
                sh "make venv && make install"
            }
        }

        stage('Environment variable injection') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'bradlab-chatbot-env-file', variable: 'ENV_FILE')]) {
                        // Load the environment variables from the file
                        echo "Loading environment variables from ${ENV_FILE}"
                        sh "cat ${ENV_FILE} > .env"
                    }
                }
            }
        }


        stage('Tests Unitaires') {
            steps {
                script {
                    // Add your test commands here
                    echo "Running tests..."
                    sh "make test"
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    // Add your build commands here
                    echo "Building the project..."
                    sh "make build"
                }
            }
        }

        stage('Deploy') {
            when {
                anyOf {
                    branch 'bradlab'
                    branch 'dev'
                    branch 'preprod'
                    branch 'prod'
                }
            }
            steps {
                script {
                    // Add your deployment commands here
                    echo "Deploying the project..."
                    withCredentials([
                        string(credentialsId: 'telegram-bot-token', variable: 'TELEGRAM_BOT_TOKEN'),
                        string(credentialsId: 'mistral-api-key', variable: 'MISTRAL_API_KEY')
                    ]) {
                        sh """
                            make deploy env=${BRANCH_NAME} \
                            TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN} \
                            MISTRAL_API_KEY=${MISTRAL_API_KEY}
                        """
                    }
                }
            }
        }

        stage('Configure Webhook') {
            when {
                anyOf {
                    branch 'alwil17'
                    branch 'dev'
                    branch 'preprod'
                }
            }
            steps {
                script {
                    // Get the API URL from CloudFormation outputs
                    def apiUrl = sh(
                        script: """
                            aws cloudformation describe-stacks \
                            --stack-name multi-stack-${BRANCH_NAME} \
                            --region eu-west-3 \
                            --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
                            --output text
                        """,
                        returnStdout: true
                    ).trim()

                    // Configure the webhook
                    withCredentials([string(credentialsId: 'telegram-bot-token', variable: 'TELEGRAM_BOT_TOKEN')]) {
                        sh """
                            # Activer l'environnement virtuel et exécuter le script
                            . .venv/bin/activate
                            python seed/webhook.py --url "${apiUrl}/webhook"
                            deactivate
                        """
                    }
                }
            }
        }

        stage('Test endpoint'){
            when {
                anyOf {
                    branch 'bradlab'
                    branch 'dev'
                    branch 'preprod'
                    branch 'prod'
                }
            }
            steps {
                script {
                    // Add your endpoint testing commands here
                    echo "Testing the endpoint..."
                    sh "make test-endpoint env=${BRANCH_NAME}"
                }
            }
        }
    }

    post {
        always {
            script {
                // Add your post-build actions here
                echo "Post-build actions..."
            }
        }
        success {
            script {
                // Notify success
                echo "Build succeeded!"
                // Uncomment the line below to send a message to Telegram
                // sh "curl -X POST https://api.telegram.org/bot${BOT_TOKEN}/sendMessage -d chat_id=<CHAT_ID> -d text='Build succeeded!'"
            }
        }
        failure {
            script {
                // Notify failure
                echo "Build failed!"
                // Uncomment the line below to send a message to Telegram
                // sh "curl -X POST https://api.telegram.org/bot${BOT_TOKEN}/sendMessage -d chat_id=<CHAT_ID> -d text='Build failed!'"
            }
        }
    }

}
