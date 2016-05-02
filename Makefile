-include ./mymakefile

test: clean
	- rm -f unittest.xml
	py.test -s -vvvv --junit-xml=unittest.xml tests

test-cov: clean
	- rm -f .coverage
	- rm -rf htmlcov
	py.test -vvvv --cov-report html --cov-report=term --cov=lain_sdk tests

clean:
	- find . -iname "*__pycache__" | xargs rm -rf
	- find . -iname "*.pyc" | xargs rm -rf
	- rm -rf dist build lain_sdk.egg-info
