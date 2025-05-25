aws dynamodb create-table \
    --table-name chatbot-dbtable-hervlockossou \
    --attribute-definitions \
        AttributeName=chat_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
        AttributeName=ai_model,AttributeType=S \
    --key-schema \
        AttributeName=chat_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --global-secondary-indexes \
        '[
            {
                "IndexName": "UserIndex",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"}
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": ["chat_id", "message_id", "role", "text", "ai_model"]
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                }
            }
        ]' \
    --region eu-west-3