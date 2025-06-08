import boto3
import datetime, asyncio, uuid

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

# Importez vos settings
from .config import env_vars
from .utils import Utils

class DynamoDBRepository:
    """
    Classe de dépôt pour interagir avec DynamoDB afin de stocker les logs de chat.
    """
    def __init__(self):
        self.table_name = env_vars.DYNAMO_TABLE
        self.region_name = env_vars.AWS_REGION_NAME
        self._table = None # Sera initialisé lors du premier accès

    @property
    def table(self):
        """
        Initialise la table DynamoDB si elle n'est pas déjà initialisée.
        Utilise un singleton-like pour la table.
        """
        if self._table is None:
            Utils.log_info(f"Initialisation de la connexion DynamoDB à la table: {self.table_name} en région: {self.region_name}")
            dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
            self._table = dynamodb.Table(self.table_name)
        return self._table

    async def save_message(
        self, 
        chat_id: int, 
        message_id: int, 
        user_id: int, 
        user_name: str, 
        text: str, 
        role: str, 
        ai_model: str = None
    ):
        """
        Sauvegarde un message (utilisateur ou bot) dans la table DynamoDB.
        """
        try:
            id = str(uuid.uuid4())  # Génère un UUID
            # item = {
            #     "id": {"S": str(id)},
            #     "chat_id": {"S": str(chat_id)},
            #     "timestamp": {"S": datetime.datetime.now(datetime.timezone.utc).isoformat()},
            #     "message_id": {"S": str(message_id)},
            #     "user_id": {"S": str(user_id)},
            #     "user_name": {"S": user_name},
            #     "text": {"S": text},
            #     "role": {"S": role},
            # }
            item = {
                'id': id,
                'chat_id': str(chat_id),
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'message_id': str(message_id),
                'user_id': str(user_id),
                'user_name': user_name,
                'text': text,
                'role': role,
            }
            if ai_model:
                item["ai_model"] = str(ai_model)
                # item["ai_model"] = {"S": ai_model}
            
            # Utils.insert_data(item)

            # Exécute l'opération put_item (synchrone) dans un thread séparé
            # await asyncio.to_thread(self.table.put_item, Item=item)
            return True
        except Exception as e:
            Utils.log_error(f"Erreur lors de l'enregistrement dans DynamoDB: {e}")
            # L'erreur n'est pas levée pour ne pas interrompre le flux du bot
            raise e
            
    async def get_chat_history(self, chat_id: int, limit: int = 100) -> list[dict]:
        """
        Récupère l'historique d'une discussion donnée par chat_id, trié par timestamp.
        Retourne une liste de dictionnaires représentant les messages.
        """
        try:
            # return Utils.get_chat_history(chat_id=chat_id, limit=limit)
            response = await asyncio.to_thread(
                self.table.query,
                KeyConditionExpression=Key('chat_id').eq(str(chat_id)),
                Limit=limit,
                ScanIndexForward=True # True pour tri ascendant (du plus ancien au plus récent)
            )
            Utils.log_info(f"Historique du chat {chat_id} récupéré. Messages trouvés: {len(response.get('Items', []))}")
            # return response.get('Items', [])
        except ClientError as e:
            error_code = e.response['Error']['Code']
            Utils.log_error(f"Erreur DynamoDB lors de la récupération de l'historique: {error_code} - {e}")
            return []
        except Exception as e:
            Utils.log_error(f"Erreur inattendue lors de la récupération de l'historique: {e}")
            return []

    async def get_user_messages_by_date_range(self, user_id: int, start_timestamp: str, end_timestamp: str, limit: int = 100) -> list[dict]:
        """
        Récupère tous les messages (user et bot) d'un utilisateur spécifique
        dans une plage de dates donnée, en utilisant le GSI 'UserIndex' (cf fichier dynamo.bash). 
        Les timestamps doivent être au format ISO 8601 (ex: "2025-01-01T00:00:00Z").
        """
        gsi_name = "UserIndex"
        try:
            # return Utils.get_user_chats(user_id, start_timestamp, end_timestamp, limit)
            query_params = {
                'IndexName': gsi_name,
                'KeyConditionExpression': Key('user_id').eq(str(user_id)) & Key('timestamp').between(start_timestamp, end_timestamp),
                'Limit': limit,
                'ScanIndexForward': True # Du plus ancien au plus récent
            }
            
            items = []
            response = await asyncio.to_thread(self.table.query, **query_params)
            items.extend(response.get('Items', []))

            while 'LastEvaluatedKey' in response:
                query_params['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = await asyncio.to_thread(self.table.query, **query_params)
                items.extend(response.get('Items', []))

            Utils.log_info(f"Messages pour l'utilisateur {user_id} dans la plage {start_timestamp} à {end_timestamp} récupérés. Messages trouvés: {len(items)}")
            return items

        except ClientError as e:
            error_code = e.response['Error']['Code']
            Utils.log_error(f"Erreur DynamoDB lors de la récupération des messages de l'utilisateur par plage de date: {error_code} - {e}")
            return []
        except Exception as e:
            Utils.log_error(f"Erreur inattendue lors de la récupération des messages de l'utilisateur par plage de date: {e}")
            return []
    
# Instanciation globale du dépôt
# C'est important si vous voulez qu'il soit un singleton à travers votre application
dynamodb_repo = DynamoDBRepository()
