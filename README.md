# DemandSense: AI 기반 수요 예측 대시보드

**DemandSense**는 시계열 데이터를 분석하여 미래 수요를 예측하고, 그 결과를 시각적으로 탐색할 수 있는 풀스택 웹 애플리케이션입니다. 머신러닝 모델의 학습부터 서빙, 시각화, 그리고 CI/CD 및 모니터링까지 MLOps의 전 과정을 경험할 수 있도록 설계되었습니다.

---

## ✨ 주요 기능 (Key Features)

- **AI 기반 수요 예측**: `scikit-learn`과 `Prophet`을 활용한 정교한 시계열 예측 모델
- **인터랙티브 대시보드**: `Next.js`와 `Recharts`로 구현된 사용자 친화적 데이터 시각화
- **실험 관리 및 모델 서빙**: `MLflow`를 이용한 모델 실험 추적과 API 서빙
- **RESTful API**: `FastAPI`로 구축된 고성능 백엔드 API
- **컨테이너 기반 환경**: `Docker`와 `Docker Compose`를 통한 간편한 설치 및 실행
- **자동화된 이미지 빌드 파이프라인**: GitHub Actions를 통한 테스트와 Docker 이미지 발행
- **API 모니터링**: Prometheus와 Grafana를 이용한 HTTP 상태 및 성능 모니터링

---

## 🏗️ 시스템 아키텍처 (Architecture)

이 프로젝트는 마이크로서비스 아키텍처를 기반으로 하며, 각 컴포넌트는 독립적으로 실행되고 Docker를 통해 관리됩니다.

```
+-----------------+      +---------------------+      +------------------+
|                 |      |                     |      |                  |
|   Frontend      |      |     Backend API     |      |      MLflow      |
|   (Next.js)     |----->|     (FastAPI)       |----->|   Tracking Server|
|   Port: 3000    |      |     Port: 8000      |      |     Port: 5001   |
|                 |      |                     |      |                  |
+-----------------+      +----------+----------+      +------------------+
                                    |
                                    |
                         +----------v----------+
                         |                     |
                         |    ML Models        |
                         | (Prophet, etc.)     |
                         |                     |
                         +---------------------+
```

1.  **Frontend (Next.js)**: 사용자가 매장·상품·기간·프로모션 조건을 선택하고 예측 결과를 확인하는 웹 인터페이스입니다.
2.  **Backend (FastAPI)**: 예측 요청을 처리하고 ML 모델을 호출하여 결과를 반환하는 API 서버입니다.
3.  **MLflow**: 모델 학습 실험을 기록하고, 최적의 모델을 저장 및 관리하는 레지스트리입니다.

---

## 🛠️ 기술 스택 (Tech Stack)

| 분야            | 기술                                                              |
| :-------------- | :---------------------------------------------------------------- |
| **Frontend**    | `React`, `Next.js`, `TypeScript`, `Tailwind CSS`, `Recharts`      |
| **Backend**     | `Python`, `FastAPI`, `Uvicorn`                                    |
| **ML/Data**     | `scikit-learn`, `Prophet`, `Pandas`, `NumPy`                      |
| **MLOps**       | `MLflow`, `Docker`, `Docker Compose`, `GitHub Actions`            |
| **Monitoring**  | `Prometheus`, `Grafana`                                           |
| **Notebook**    | `Jupyter Notebook`                                                |

---

## 🚀 시작하기 (Getting Started)

로컬 개발용 명령과 환경 변수는 [DEVELOPMENT.md](DEVELOPMENT.md)를 참고하세요. 포트폴리오 보완 계획은 [PORTFOLIO_ROADMAP.md](PORTFOLIO_ROADMAP.md)에 정리되어 있습니다.

이 프로젝트를 로컬 환경에서 실행하려면 아래 단계를 따르세요.

### 사전 요구사항

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)

### 설치 및 실행

1.  **프로젝트 클론**
    ```bash
    git clone https://github.com/Samuel-0930/AI-Driven-Retail-Demand-Forecasting-Platform.git
    cd AI-Driven-Retail-Demand-Forecasting-Platform
    ```

2.  **전체 서비스 실행**
    Docker Compose를 사용하여 Frontend, Backend, MLflow, Monitoring 도구들을 한 번에 실행합니다.
    ```bash
    docker compose up --build
    ```

3.  **애플리케이션 접속**
    - **Frontend (대시보드)**: [http://localhost:3000](http://localhost:3000)
    - **Backend (API Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)
    - **MLflow (실험 관리)**: [http://localhost:5001](http://localhost:5001)
    - **Prometheus (메트릭)**: [http://localhost:9091](http://localhost:9091)
    - **Grafana (시각화)**: [http://localhost:3001](http://localhost:3001) (기본 ID: `admin`, 비밀번호는 `GRAFANA_ADMIN_PASSWORD`)

---

## 📂 프로젝트 구조 (Project Structure)

```
.
├── backend/         # FastAPI 백엔드 서버
│   ├── app/         # API 라우트, 서비스 로직
│   ├── tests/       # API 유닛 테스트
│   └── train_*.py   # 모델 학습 스크립트
├── frontend/        # Next.js 프론트엔드
├── mlflow/          # MLflow 서버 설정
├── monitoring/      # 모니터링 설정 (Prometheus, Grafana)
├── notebooks/       # 데이터 분석 및 모델링 (EDA)
├── data/            # 원본 및 가공 데이터
└── docker-compose.yml # 서비스 오케스트레이션 설정
```

---

## 📈 ML 파이프라인 (ML Pipeline)

1.  **데이터 준비**: `notebooks/EDA/final_eda.ipynb`에서 데이터를 탐색하고 전처리를 수행합니다.
2.  **모델 학습**: `backend/train_baseline.py` 스크립트를 실행하여 모델을 학습합니다.
    ```bash
    docker compose exec backend python backend/train_baseline.py
    ```
3.  **실험 확인**: [MLflow UI](http://localhost:5001)에서 학습 결과와 메트릭을 확인합니다.
4.  **서빙**: 학습된 모델은 FastAPI를 통해 즉시 API로 제공됩니다.

---

## � CI/CD 및 모니터링 (CI/CD & Monitoring)

이 프로젝트는 안정적인 운영을 위해 CI/CD 파이프라인과 모니터링 시스템을 갖추고 있습니다.

### CI/CD 파이프라인 (GitHub Actions)
- **자동화된 검증**: `main` 또는 `develop` 브랜치에 푸시될 때마다 backend test, frontend lint/build, Compose 구성을 검증합니다.
- **Docker 이미지 발행**: `main` 브랜치에 푸시되면 검증을 통과한 Docker 이미지를 Docker Hub에 발행합니다.

### 모니터링 스택
- **Prometheus**: 백엔드 API의 성능 지표(요청 수, 응답 시간 등)를 수집합니다. 예측 정확도·drift 모니터링은 아직 구현 대상입니다.
- **Grafana**: 수집된 데이터를 시각화합니다. `monitoring/grafana/fastapi_dashboard.json`이 자동으로 로드되어 즉시 대시보드를 확인할 수 있습니다.

### 테스트 실행
로컬에서 테스트를 실행하려면 다음 명령어를 사용하세요:
```bash
docker compose exec backend pytest backend/tests/
```

---

## 🚀 배포 (Deployment)

Docker Hub에 배포된 이미지를 사용하여 소스 코드 없이도 어디서든 서비스를 실행할 수 있습니다. 자세한 내용은 [DEPLOYMENT.md](DEPLOYMENT.md)를 참고하세요.

---

## 🔮 향후 개선 사항 (Future Improvements)

- [x]  **CI/CD 파이프라인 구축**: GitHub Actions를 이용한 테스트 및 배포 자동화
- [x]  **모델 모니터링**: Prometheus & Grafana를 이용한 시스템 모니터링
- [ ]  **클라우드 배포**: AWS, GCP 등 클라우드 환경에 서비스 배포
- [ ]  **고급 모델 추가**: LSTM, GRU 등 딥러닝 기반 시계열 모델 적용

---

## 📄 라이선스 (License)

이 프로젝트는 [MIT License](LICENSE)를 따릅니다.

---

## 👤 만든이 (Author)

- **[Samyeol Son]**
- **Email**: samyeol0930@gmail.com
- **GitHub**: [Samuel-0930](https://github.com/Samuel-0930)
