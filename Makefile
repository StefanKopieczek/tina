venv:
	python -m venv venv
	. ./venv/bin/activate && pip install -r requirements.txt

out/tina.zip: venv
	cd venv/lib/python*/site-packages && zip -r ../../../../out/tina.zip .
	zip -gr out/tina.zip tina

.PHONY: clean-zip
clean-zip:
	-rm out/tina.zip

.PHONY: zip
zip: clean-zip out/tina.zip

test: venv
	python -m unittest

deploy: test clean-zip out/tina.zip
	aws lambda update-function-code --function-name tina-checkin --zip-file fileb://out/tina.zip --profile stefankopieczek-iamadmin
	aws lambda update-function-code --function-name tina-respond --zip-file fileb://out/tina.zip --profile stefankopieczek-iamadmin

.PHONY: invoke-checkin
invoke-checkin:
	aws lambda invoke --function-name tina-checkin out/result --profile stefankopieczek-iamadmin --log-type Tail
	cat out/result | jq

.PHONY: invoke-respond
invoke-respond:
	aws lambda invoke --function-name tina-respond out/result --profile stefankopieczek-iamadmin --log-type Tail
	cat out/result | jq
