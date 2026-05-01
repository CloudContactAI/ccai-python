FROM python:3.11-slim

WORKDIR /sdk
COPY pyproject.toml setup.py ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

COPY integration/requirements.txt ./integration/
RUN pip install --no-cache-dir -r ./integration/requirements.txt

COPY integration/ ./integration/

WORKDIR /sdk/integration
CMD ["python", "test.py"]
