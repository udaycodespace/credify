.PHONY: test lint docker clean deploy

test:
	./run_tests.sh

lint:
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127

docker:
	docker build -t blockchain-credentials .

deploy:
	docker build -t blockchain-credentials .
	docker tag blockchain-credentials your-registry/blockchain-credentials:latest
	docker push your-registry/blockchain-credentials:latest

clean:
	docker rm -f $$(docker ps -aq --filter ancestor=blockchain-credentials)
	rm -rf data/ htmlcov/ .pytest_cache/
