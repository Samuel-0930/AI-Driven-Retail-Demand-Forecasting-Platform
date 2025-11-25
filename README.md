# DemandSense: AI 기반 수요 예측 대시보드

**DemandSense**는 시계열 데이터를 분석하여 미래 수요를 예측하고, 그 결과를 시각적으로 탐색할 수 있는 풀스택 웹 애플리케이션입니다. 머신러닝 모델의 학습부터 서빙, 시각화까지 전 과정을 포함하여 MLOps의 기본 파이프라인을 경험할 수 있도록 설계되었습니다.

---

## ✨ 주요 기능 (Key Features)

- **AI 기반 수요 예측**: `scikit-learn`과 `Prophet`을 활용한 시계열 예측 모델
- **인터랙티브 대시보드**: `Next.js`와 `Recharts`로 구현된 사용자 친화적 UI
- **실험 관리 및 모델 서빙**: `MLflow`를 이용한 모델 실험 추적 및 버전 관리
- **RESTful API**: `FastAPI`로 구축된 빠르고 효율적인 백엔드 API
- **컨테이너 기반 환경**: `Docker`와 `Docker Compose`를 통한 간편한 설치 및 실행

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

1.  **Frontend (Next.js)**: 사용자가 데이터를 업로드하고 예측 결과를 확인할 수 있는 UI를 제공합니다.
2.  **Backend (FastAPI)**: 예측 요청을 받아 ML 모델을 호출하고 결과를 프론트엔드에 반환하는 API 서버입니다.
3.  **MLflow**: 모델 학습 과정(실험)을 기록하고, 최적의 모델을 저장 및 관리하는 서버입니다.

---

## 🛠️ 기술 스택 (Tech Stack)

| 분야            | 기술                                                              |
| :-------------- | :---------------------------------------------------------------- |
| **Frontend**    | `React`, `Next.js`, `TypeScript`, `Tailwind CSS`, `Recharts`      |
| **Backend**     | `Python`, `FastAPI`, `Uvicorn`                                    |
| **ML/Data**     | `scikit-learn`, `Prophet`, `Pandas`, `NumPy`                      |
| **MLOps**       | `MLflow`, `Docker`, `Docker Compose`                              |
| **Notebook**    | `Jupyter Notebook`                                                |

---

## 🚀 시작하기 (Getting Started)

이 프로젝트를 로컬 환경에서 실행하려면 아래 단계를 따르세요.

### 사전 요구사항

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)

### 설치 및 실행

1.  **프로젝트 클론**
    ```bash
    git clone https://github.com/your-username/demand-sense.git
    cd demand-sense
    ```

2.  **Docker Compose를 이용한 전체 서비스 실행**
    모든 서비스(Frontend, Backend, MLflow)를 한 번에 실행합니다.
    ```bash
    docker-compose up --build
    ```

3.  **애플리케이션 접속**
    - **Frontend (대시보드)**: [http://localhost:3000](http://localhost:3000)
    - **Backend (API Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)
    - **MLflow (실험 관리)**: [http://localhost:5001](http://localhost:5001)

---

## 📂 프로젝트 구조 (Project Structure)

```
.
├── backend/         # FastAPI 백엔드 서버
│   ├── app/         # API 라우트, 서비스 로직
│   ├── data_generator.py # 샘플 데이터 생성
│   └── train_*.py   # 모델 학습 스크립트
├── frontend/        # Next.js 프론트엔드
│   ├── app/         # 페이지 라우팅
│   └── components/  # 리액트 컴포넌트 (대시보드 등)
├── mlflow/          # MLflow 서버 설정
├── notebooks/       # 데이터 분석 및 모델링 (EDA)
├── data/            # 원본 및 가공 데이터
└── docker-compose.yml # 서비스 오케스트레이션
```

---

## 📈 ML 파이프라인 (ML Pipeline)

1.  **데이터 준비**: `notebooks/comprehensive_eda.ipynb`에서 데이터를 탐색하고 전처리를 수행합니다.
2.  **모델 학습 및 실험**: `backend/train_baseline.py` 또는 `train_all.py` 스크립트를 실행하여 모델을 학습합니다.
    ```bash
    # 백엔드 컨테이너 접속
    docker-compose exec backend bash

    # 모델 학습 스크립트 실행
    python train_baseline.py
    ```
3.  **실험 결과 확인**: [MLflow UI](http://localhost:5001)에 접속하여 파라미터, 메트릭 등 학습 결과를 확인하고 최적의 모델을 선정합니다.
4.  **모델 서빙**: FastAPI 백엔드는 MLflow에 저장된 모델을 로드하여 예측 API를 제공합니다.

---

## 🛠️ CI/CD & Monitoring

This project includes a robust CI/CD pipeline and monitoring stack.

### CI/CD Pipeline (GitHub Actions)
- **Automated Testing**: Runs `pytest` on every push to `main` and `develop`.
- **Docker Deployment**: Automatically builds and pushes images to Docker Hub on pushes to `main`.

### Monitoring Stack
Real-time observability is provided by:
- **Prometheus** (`http://localhost:9091`): Collects metrics from the backend API.
- **Grafana** (`http://localhost:3001`): Visualizes metrics with a custom dashboard.
    - **Default Login**: `admin` / `admin`
    - **Dashboard**: Import `monitoring/grafana/fastapi_dashboard.json` for API insights.

### Testing
Run backend tests locally using Docker:
```bash
docker-compose exec backend pytest backend/tests/
```

---

## 🚀 Deployment

For easy deployment using pre-built images, see [DEPLOYMENT.md](DEPLOYMENT.md).

---

## 🔮 향후 개선 사항 (Future Improvements)

- [x]  **CI/CD 파이프라인 구축**: GitHub Actions를 이용해 테스트 및 배포 자동화
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
