.PHONY: clean lint build deploy virtual-env

virtual-env:
	virtualenv -p python3 venv

clean:
	rm -rf build dist *.egg-info

lint:
	flake8 src --exclude 'src/xtce.py' --count --show-source --statistics --format pylint

#TODO: Add lint as a dependency to build recipe
build:
	python setup.py sdist bdist_wheel

deploy: clean build
	twine upload -r pypi dist/*
