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

deploy: clean-zip out/tina.zip
	aws lambda update-function-code --function-name tina-checkin --zip-file fileb://out/tina.zip --profile stefankopieczek-iamadmin

.PHONY: invoke
invoke:
	aws lambda invoke --function-name tina-checkin out/result --profile stefankopieczek-iamadmin
	cat out/result | jq
