import json
import logging
from typing import List

import boto3

from src.config import env_vars
## Simple edit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("chatbot-bradlab-logs")

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
    def insert_data(item):
        dynamo_client = boto3.client("dynamodb", region_name=env_vars.AWS_REGION_NAME)
        dynamo_client.put_item(
            TableName=env_vars.DYNAMO_TABLE,
            Item=item,
        )
