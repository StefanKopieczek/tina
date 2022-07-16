AWS_ACCOUNT_ID = 833033589552
AWS_REGION = eu-west-1
ECR_REPO = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/tina
LATEST_ECR_IMAGE = $(ECR_REPO):latest

BASE_IMAGE_NAME = base
TINA_IMAGE_NAME = tina
SHARED_NAME = shared
CHECKIN_NAME = tina-checkin
MESSAGE_HANDLER_NAME = tina-handle-message
MANUAL_TEST_NAME = tina-manual-test
PING_NAME = tina-ping
TEST_RUNNER_NAME = test-runner

.PHONY: all
all: test upload

.PHONY: test
test: docker-build-test-runner
	docker run -t tina/$(TEST_RUNNER_NAME)

#
# Docker recipes
#

DOCKER_BUILD = docker build $(2) -f docker/$(1).Dockerfile -t tina/$(1)

.PHONY: docker-build-base
docker-build-base:
	$(call DOCKER_BUILD,$(BASE_IMAGE_NAME),./docker)

.PHONY: docker-build-tina
docker-build-tina: docker-build-base
	$(call DOCKER_BUILD,$(TINA_IMAGE_NAME),.)

.PHONY: docker-build-test-runner
docker-build-test-runner: docker-build-tina
	$(call DOCKER_BUILD,$(TEST_RUNNER_NAME),.)

.PHONY: docker
docker: docker-build-tina

.PHONY: upload
upload: docker-build-tina test
	docker tag tina/$(TINA_IMAGE_NAME) $(LATEST_ECR_IMAGE)
	docker push $(LATEST_ECR_IMAGE)
	make clean-up-old-images

.PHONY clean-up-old-images:
clean-up-old-images:
	aws ecr list-images --repository-name tina --profile stefankopieczek-iamadmin | jq -e '[.imageIds[] | select(has("imageTag") | not)] | length == 0' || aws ecr batch-delete-image --repository-name tina --profile stefankopieczek-iamadmin --image-ids $$(aws ecr list-images --repository-name tina --profile stefankopieczek-iamadmin | jq -c '[.imageIds[] | select(has("imageTag") | not)]')

#
# Lambda recipes
#

DEPLOY_LAMBDA = aws lambda update-function-code --profile stefankopieczek-iamadmin --function-name $(1) --image-uri $(LATEST_ECR_IMAGE)
WAIT_FOR_LAMBDA = aws lambda wait function-updated --function-name $(1) --profile stefankopieczek-iamadmin
INVOKE_LAMBDA = aws lambda invoke --function-name $(1) out/result --profile stefankopieczek-iamadmin --log-type Tail | jq -r '.LogResult | @base64d'

.PHONY: deploy-checkin
deploy-checkin: test upload
	$(call WAIT_FOR_LAMBDA,$(CHECKIN_NAME))
	$(call DEPLOY_LAMBDA,$(CHECKIN_NAME))

.PHONY: deploy-message-handler
deploy-message-handler: test upload
	$(call WAIT_FOR_LAMBDA,$(MESSAGE_HANDLER_NAME))
	$(call DEPLOY_LAMBDA,$(MESSAGE_HANDLER_NAME))

.PHONY: deploy-manual-test
deploy-manual-test: test upload
	$(call WAIT_FOR_LAMBDA,$(MANUAL_TEST_NAME))
	$(call DEPLOY_LAMBDA,$(MANUAL_TEST_NAME))

.PHONY: deploy
deploy: deploy-checkin deploy-message-handler deploy-manual-test

.PHONY: invoke-checkin
invoke-checkin:
	$(call WAIT_FOR_LAMBDA,$(CHECKIN_NAME))
	$(call INVOKE_LAMBDA,$(CHECKIN_NAME))

.PHONY: invoke-handle-message
invoke-handle-message:
	$(call WAIT_FOR_LAMBDA,$(MESSAGE_HANDLER_NAME))
	$(call INVOKE_LAMBDA,$(MESSAGE_HANDLER_NAME))

.PHONY: invoke-manual-test
invoke-manual-test:
	$(call WAIT_FOR_LAMBDA,$(MANUAL_TEST_NAME))
	$(call INVOKE_LAMBDA,$(MANUAL_TEST_NAME))

.PHONY: invoke-local
invoke-local:
	curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
