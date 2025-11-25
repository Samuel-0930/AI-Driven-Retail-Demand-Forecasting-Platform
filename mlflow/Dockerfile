FROM python:3.11-slim

RUN pip install mlflow==2.14.1

EXPOSE 5000

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", "--backend-store-uri", "sqlite:///mlruns/mlflow.db", "--default-artifact-root", "/mlruns"]
