# Chatbot API FastAPI

[![GitHub](https://img.shields.io/badge/GitHub-kybaloo%2Fchatbot-blue?logo=github)](https://github.com/kybaloo/chatbot)

Une API de chatbot développée avec FastAPI, conçue pour être déployée sur AWS Lambda via Mangum. Ce projet est disponible sur [GitHub](https://github.com/kybaloo/chatbot).

## 🌟 Fonctionnalités

- API REST avec FastAPI
- Configuration via variables d'environnement
- Compatibilité AWS Lambda avec Mangum
- Logging configurable
- Conteneurisation avec Docker
- Intégration CI/CD avec Jenkins
- Gestion d'infrastructure via AWS CloudFormation

## 🛠️ Technologies utilisées

- [Python 3.12](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/usage/pydantic_settings/)
- [AWS SDK (boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Mangum](https://github.com/jordaneremieff/mangum) - Adaptateur AWS Lambda pour les applications ASGI
- [Docker](https://www.docker.com/)
- [Jenkins](https://www.jenkins.io/)

## 🚀 Installation

### Prérequis

- Python 3.12+
- Docker (optionnel)
- AWS CLI (optionnel)

### Installation locale

1. Cloner le dépôt
   ```bash
   git clone https://github.com/kybaloo/chatbot.git
   cd chatbot
   ```

2. Créer et activer un environnement virtuel

   **Option 1 : Utiliser Make**
   ```bash
   make venv
   # Sur Windows
   .venv\Scripts\activate
   # Sur Unix
   source .venv/bin/activate
   ```

   **Option 2 : Utiliser Python directement**
   ```bash
   # Sur Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # Sur Unix
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Installer les dépendances
   ```bash
   make install
   ```

4. Créer un fichier `.env` à la racine du projet avec les variables suivantes :
   ```
   ENV_NAME=local
   AWS_REGION_NAME=eu-west-3
   DYNAMO_TABLE=votre-table-dynamo
   AWS_PROFILE=votre-profil-aws
   MISTRAL_API_KEY=votre-clé-mistral
   ```

## ▶️ Exécution

### Localement

```bash
uvicorn src.main:app --reload
```

### Avec Docker

1. Construire l'image
   ```bash
   docker build -t chatbot-api .
   ```

2. Exécuter le conteneur
   ```bash
   docker run -p 8000:80 chatbot-api
   ```

## 📚 Documentation API

Une fois l'API lancée, la documentation interactive est disponible aux URLs suivantes :

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## ⚙️ Déploiement

### Sur AWS Lambda

Le projet est configuré pour être déployé sur AWS Lambda grâce à Mangum :

```bash
make infra  # Déploie l'infrastructure CloudFormation
```

### Via CI/CD

Le projet intègre un pipeline Jenkins pour l'intégration et le déploiement continus :

1. Installation et tests
2. Tests unitaires
3. (Autres étapes définies dans le Jenkinsfile)

## 🧪 Tests

```bash
pytest
```

## 📂 Structure du projet

```
├── Dockerfile            # Configuration Docker
├── Jenkinsfile           # Pipeline CI/CD Jenkins
├── LICENSE               # Fichier de licence MIT
├── Makefile              # Commandes Make
├── README.md             # Ce fichier
├── requirements.txt      # Dépendances Python
├── version               # Version du projet
└── src/                  # Code source
    ├── __init__.py
    ├── config.py         # Configuration et variables d'environnement
    ├── main.py           # Point d'entrée de l'application FastAPI
    └── utils.py          # Utilitaires (logging, etc.)
```

## 🤝 Contribution

1. Forker le projet
2. Créer une branche de fonctionnalité (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit des changements (`git commit -am 'Ajouter une nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📝 Licence

Ce projet est sous licence [MIT](https://opensource.org/licenses/MIT) - voir le fichier [LICENSE](LICENSE) pour plus de détails.
