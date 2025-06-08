import json
import logging
from typing import List
from boto3.dynamodb.conditions import Key, Attr

import boto3

from src.config import env_vars
## Simple edit

logging.basicConfig()
logger = logging.getLogger("chatbot")

class Utils:

    ALLOWED_EXTENSIONS = ["pdf", "docx", "doc", "png", "jpg", "jpeg"]

    @staticmethod
    def log_info(message):
        """_summary_
        Log a simple info message
        """
        logger.info(msg=f"==> {message}")
        
    @staticmethod
    def log_warning(message):
        """_summary_
        Log a simple warning message
        """
        logger.warning(msg=f"==> {message}")

    @staticmethod
    def log_debug(message):
        """_summary_
        Log a debug message
        """
        logger.debug(msg=f"==> {message}")

    @staticmethod
    def log_error(message):
        """_summary_
        Log an error message
        """
        logger.error(msg=f"==> {message}")

    @staticmethod
    def log_list(elements: List[any]):
        if elements:
            logger.info(
                msg=f"Displaying all the {len(elements)} elements of the list"
            )
            for i in range(len(elements)):
                logger.info(
                    msg=f"##### {i} ==> {json.dumps(elements[i], indent=4)}"
                )

    @staticmethod
    def get_logger():
        return logger

    @staticmethod
    def get_session():
        return boto3.Session(
            region_name=env_vars.AWS_REGION_NAME, env_name=env_vars.ENV_NAME
        )
    
    @staticmethod
    def get_dynamo_resource() -> boto3.resource:
        # In Lambda, use the role credentials
        Utils.log_info(f"Initialisation de la connexion DynamoDB à la table: {env_vars.DYNAMO_TABLE} en région: {env_vars.AWS_REGION_NAME}")
        return boto3.resource("dynamodb", region_name=env_vars.AWS_REGION_NAME)
        


    @staticmethod
    def insert_data(item):
        try:
            dynamo_client = boto3.client("dynamodb", region_name=env_vars.AWS_REGION_NAME)
            dynamo_client.put_item(
                TableName=env_vars.DYNAMO_TABLE,
                Item=item,
            )
            return True
        except Exception as e:
            logger.error(msg=f"Erreur lors de l'insertion dans DynamoDB: {str(e)}")
            raise e
        
    @staticmethod
    def get_chat_history(chat_id: str, limit: int = 100) -> list[dict]:
        try:
            dynamo_resource = Utils.get_dynamo_resource()
            table = dynamo_resource.Table(env_vars.DYNAMO_TABLE)

            response = table.query(
                KeyConditionExpression=Key('chat_id').eq(str(chat_id)),
                Limit=limit,
                ScanIndexForward=True,  # Trier par timestamp croissant
            )
            
            items: list[dict] = response.get("Items", [])
            logger.info(msg=f"Historique du chat {chat_id} récupéré. Messages trouvés: {len(items)}")
            return items
        except Exception as e:
            logger.error(msg=f"Erreur : chat history in DynamoDB: {str(e)}")
            raise e
    
    @staticmethod
    def get_user_chats(user_id: str, start_timestamp: str, end_timestamp: str, limit: int = 100) -> list[dict]:
        try:
            dynamo_resource = Utils.get_dynamo_resource()
            table = dynamo_resource.Table(env_vars.DYNAMO_TABLE)
            
            # Utilise une requête sur l'index avec le user_id
            query_params = {
                'IndexName': "UserIndex",
                'KeyConditionExpression': Key('user_id').eq(str(user_id)) & Key('timestamp').between(start_timestamp, end_timestamp),
                'Limit': limit,
                'ScanIndexForward': False # Du plus récents au plus anciens
            }

            items = []
            response = table.query(**query_params)
            items.extend(response.get('Items', []))
            
            while 'LastEvaluatedKey' in response:
                query_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = table.query(**query_params)
                items.extend(response.get('Items', []))

            return items
        except Exception as e:
            logger.error(msg=f"Erreur : chat history in DynamoDB: {str(e)}")
            raise e
