.PHONY: build, build-test, run, test

build:
	docker build -t qairamap-api -f .docker/dev/Dockerfile .

build-test:
	docker build -t qairamap-api-test -f .docker/test/Dockerfile .

run:
	docker run -it \
		--name=qairamap-api \
		--rm \
		--net=host \
		--volume="$(PWD):/src" \
		qairamap-api bash -c "python run.py"

test:
	docker run -it \
		--name=qairamap-api-test \
		--rm \
		--net=host \
		--volume="$(PWD):/src" \
		qairamap-api-test bash -c "pytest -v"
