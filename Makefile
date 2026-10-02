install:
	python -m pip install -r requirements.txt

prepare:
	PYTHONPATH=. python scripts/prepare_data.py

train:
	PYTHONPATH=. python scripts/train_model.py

test:
	PYTHONPATH=. pytest -q

run:
	PYTHONPATH=. uvicorn app.backend.main:app --host 0.0.0.0 --port 8000

demo:
	PYTHONPATH=. uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
