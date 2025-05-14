.PHONY: release clean clean-venv venv install clean-venv infra serve

# by default, we settle down in this region
AWS_REGION ?= eu-west-3
AWS_PROFILE ?= "esgis_profile"

ifeq ($(CURRENT_BRANCH), main)
    environment = prod
else
    environment = $(CURRENT_BRANCH) # Rework hervlokossou_dev ==> hervlokossou
endif

clean:
    rm -rf build .coverage .python-version *egg-info .pytest_cache

clean-venv:
    rm -rf .venv

venv: clean-venv clean
    python3 -m venv .venv

install: 
    @echo "Installing dependencies for " ${environment}
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt

infra:
    aws cloudformation deploy \
        --template-file infrastructure/template.yaml \
        --region ${AWS_REGION} \
        --stack-name "pethaul-stack-${env}" \
        --parameter-overrides EnvironmentName=${env} \
        --capabilities CAPABILITY_NAMED_IAM \
        --tags "Application=Pethaul Companion" \
        --no-fail-on-empty-changeset
    aws cloudformation describe-stacks \
                --stack-name "pethaul-stack-${env}" \
                --region ${AWS_REGION} \
                --query 'Stacks[0].Outputs[?OutputKey==DynamoDBTableName].OutputValue' --output text  

build:
    sam build --use-container -t infrastructure/template.yaml

deploy-local:
    sam local start-api

deploy:
    @echo "Deploying to " ${env}
    # Extract env from the branch name

    sam deploy --resolve-s3 --template-file .aws-sam/build/template.yaml --stack-name multi-stack-${env} \
         --capabilities CAPABILITY_IAM --region ${AWS_REGION} --parameter-overrides EnvironmentName=${env} --no-fail-on-empty-changeset
    
test:
    @echo "Running tests..."
    .venv/bin/pytest
    
serve:
    .venv/bin/fastapi dev src/main.py