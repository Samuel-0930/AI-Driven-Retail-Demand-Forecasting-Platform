# Demand Signal: AI 기반 수요 예측 포트폴리오

Demand Signal은 **실데이터 EDA 사례**와 **재현 가능한 합성 데이터 예측 앱**을 분리해 보여 주는 데이터 분석 중심 포트폴리오입니다. 한쪽은 수요 구조를 비판적으로 해석하고, 다른 한쪽은 모델 학습부터 API·대시보드까지의 흐름을 직접 실행할 수 있게 합니다.

## 포트폴리오 구성

| 트랙 | 보여 주는 역량 | 데이터 | 시작점 |
| --- | --- | --- | --- |
| 실데이터 EDA 사례 | 데이터 품질, 희소 수요, 집중도, 계절성, 외생 변수 검증 | Commax 출하 데이터 | [EDA 사례 요약](COMMAX_EDA_CASE_STUDY.md), [노트북](notebooks/EDA/final_eda.ipynb) |
| 실행 가능한 앱 데모 | 합성 데이터 생성, Prophet 학습, MLflow 실험 추적, FastAPI 서빙, Next.js 시각화 | 결정론적 합성 리테일 수요 데이터 | [Data Card](DATA_CARD.md), [Model Card](MODEL_CARD.md) |

두 트랙은 의도적으로 연결하지 않았습니다. Commax EDA 원본은 저장소에 재배포하지 않으며, 현재 앱의 모델은 합성 데이터로만 학습됩니다. 따라서 데모의 모델 성능을 실제 출하 데이터 성능처럼 주장하지 않습니다.

## 주요 기능

- 매장·상품·기간(최대 90일)·프로모션 조건 기반의 일별 수요 예측
- Prophet 점 예측과 예측 구간 시각화
- MLflow 실험 기록과 모델 artifact 저장
- FastAPI 입력 검증·오류 처리, rolling backtest·seasonal-naive 비교, Prometheus API 메트릭
- Docker Compose 기반의 로컬 실행과 GitHub Actions 검증

## 아키텍처

```text
Next.js dashboard → FastAPI → MLflow run artifacts → Prophet forecast
                         └→ Prometheus → Grafana
```

## 빠른 실행

사전 요구사항: Docker Desktop, Docker Compose, Git

```bash
git clone https://github.com/Samuel-0930/AI-Driven-Retail-Demand-Forecasting-Platform.git
cd AI-Driven-Retail-Demand-Forecasting-Platform
cp .env.example .env
docker compose up --build
```

새 터미널에서 기본 데모 모델을 학습합니다.

```bash
docker compose exec backend python backend/bootstrap_demo.py
```

이 명령은 합성 데이터가 없으면 시드 42로 생성하고, 기본 조합(매장 1·상품 1)의 모델을 학습합니다. 또한 30일 horizon의 rolling backtest 3회와 주간 seasonal-naive 기준선 비교 결과를 생성합니다. 이후 [http://localhost:3000](http://localhost:3000)에서 동일 조합을 선택해 예측과 모델 검증 결과를 확인할 수 있습니다.

| 서비스 | 주소 |
| --- | --- |
| 대시보드 | http://localhost:3000 |
| API 문서 | http://localhost:8000/docs |
| MLflow | http://localhost:5001 |
| Prometheus | http://localhost:9091 |
| Grafana | http://localhost:3001 (`admin` / `GRAFANA_ADMIN_PASSWORD`) |

## 데이터와 모델의 한계

- 앱 모델은 합성 데이터 기반이며 실제 재고·발주 의사결정용이 아닙니다.
- rolling backtest는 30일 horizon 3회이고, 평가 시 실제 holdout 프로모션 값을 사용해 미래 성능보다 낙관적일 수 있습니다.
- 실데이터 EDA의 외부 경제지표는 결측·발표 지연·누수 여부를 검증하기 전에는 예측 변수로 사용하면 안 됩니다.

상세한 계보와 사용 제한은 [DATA_CARD.md](DATA_CARD.md), 모델 한계와 선택 규칙은 [MODEL_CARD.md](MODEL_CARD.md)를 참고하세요.

## 개발과 검증

- 로컬 개발 명령: [DEVELOPMENT.md](DEVELOPMENT.md)
- 배포 가이드: [DEPLOYMENT.md](DEPLOYMENT.md)
- 개선 로드맵: [PORTFOLIO_ROADMAP.md](PORTFOLIO_ROADMAP.md)

GitHub Actions는 backend test, frontend lint/build, Compose 설정 검증을 실행합니다. `main` 브랜치에서는 검증을 통과한 Docker 이미지를 발행합니다. Prometheus/Grafana는 API 상태와 성능을 관찰하며, 수요 정확도·drift 모니터링은 아직 구현 대상입니다.

## 기술 스택

React, Next.js, TypeScript, Recharts, Python, FastAPI, Prophet, Pandas, MLflow, Docker Compose, Prometheus, Grafana, GitHub Actions

## 라이선스

[MIT License](LICENSE)
