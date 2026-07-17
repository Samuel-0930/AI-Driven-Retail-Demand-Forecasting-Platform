# 🚀 Demand Signal 배포 가이드

이 문서는 Docker Hub에 배포된 이미지를 사용하여 **Demand Signal** 애플리케이션을 어디서든 쉽게 실행하는 방법을 안내합니다.

## 📋 사전 요구사항

*   [Docker](https://www.docker.com/get-started)가 설치되어 있어야 합니다.
*   [Docker Compose](https://docs.docker.com/compose/install/)가 설치되어 있어야 합니다.

## 🏃‍♂️ 실행 방법

소스 코드는 필요 없지만 저장소의 최신 `docker-compose.deploy.yml` 파일은 필요합니다.

1.  **Compose 파일 다운로드**:

    ```bash
    curl -O https://raw.githubusercontent.com/Samuel-0930/AI-Driven-Retail-Demand-Forecasting-Platform/develop/docker-compose.deploy.yml
    ```

2.  **Grafana 관리자 비밀번호 설정**: 기본 비밀번호를 사용하지 않도록 환경변수를 먼저 설정합니다.

    ```bash
    export GRAFANA_ADMIN_PASSWORD='충분히-긴-비밀번호'
    ```

3.  **실행**: 터미널에서 해당 파일이 있는 경로로 이동하여 아래 명령어를 실행합니다.

    ```bash
    docker compose -f docker-compose.deploy.yml up -d
    ```

4.  **접속**:
    *   **Frontend (대시보드)**: [http://localhost:3000](http://localhost:3000)
    *   **Backend (API)**: [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **MLflow**: [http://localhost:5001](http://localhost:5001)

## 🛑 종료 방법

```bash
docker compose -f docker-compose.deploy.yml down
```
