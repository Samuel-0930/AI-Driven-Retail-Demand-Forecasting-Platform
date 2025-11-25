# 🚀 DemandSense 배포 가이드

이 문서는 Docker Hub에 배포된 이미지를 사용하여 **DemandSense** 애플리케이션을 어디서든 쉽게 실행하는 방법을 안내합니다.

## 📋 사전 요구사항

*   [Docker](https://www.docker.com/get-started)가 설치되어 있어야 합니다.
*   [Docker Compose](https://docs.docker.com/compose/install/)가 설치되어 있어야 합니다.

## 🏃‍♂️ 실행 방법

소스 코드를 다운로드할 필요 없이, 아래 `docker-compose.deploy.yml` 파일만 있으면 됩니다.

1.  **파일 생성**: `docker-compose.yml`이라는 이름으로 파일을 만들고 아래 내용을 붙여넣으세요. (또는 저장소의 `docker-compose.deploy.yml`을 사용하세요)

    ```yaml
    services:
      backend:
        image: samuelsuperson/demand-sense-backend:latest
        ports:
          - "8000:8000"
        environment:
          - MLFLOW_TRACKING_URI=http://mlflow:5000
        volumes:
          - mlruns_data:/mlruns
        depends_on:
          - mlflow

      frontend:
        image: samuelsuperson/demand-sense-frontend:latest
        ports:
          - "3000:3000"
        environment:
          - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
        depends_on:
          - backend

      mlflow:
        image: samuelsuperson/demand-sense-mlflow:latest
        ports:
          - "5001:5000"
        volumes:
          - mlruns_data:/mlruns

    volumes:
      mlruns_data:
    ```

2.  **실행**: 터미널에서 해당 파일이 있는 경로로 이동하여 아래 명령어를 실행합니다.

    ```bash
    docker-compose up -d
    ```

3.  **접속**:
    *   **Frontend (대시보드)**: [http://localhost:3000](http://localhost:3000)
    *   **Backend (API)**: [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **MLflow**: [http://localhost:5001](http://localhost:5001)

## 🛑 종료 방법

```bash
docker-compose down
```
