VENV?=.venv
PY?=$(VENV)/bin/python

.PHONY: install fanduel normalize merge signals run

install:
	python -m venv $(VENV)
	$(PY) -m pip install -r requirements.txt

fanduel:
	$(PY) scripts/run_fanduel_all.py

normalize:
	$(PY) scripts/normalize_all.py

merge:
	$(PY) scripts/merge_all_books.py

signals:
	$(PY) scripts/generate_signals.py

run: fanduel normalize merge signals
