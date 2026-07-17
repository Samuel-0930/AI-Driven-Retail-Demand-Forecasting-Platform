# Model Card — Synthetic Demand Forecast Demo

## Intended use

매장·상품·기간·프로모션 여부를 입력받아 Prophet 기반 예측 결과와 예측 구간을 보여 주는 취업 포트폴리오용 데모입니다. 모델 학습, 실험 추적, API 서빙, 시각화의 연결을 설명하기 위한 용도입니다.

## Model and training

- 모델: `Prophet` + `is_promo` 외생 변수
- 학습 데이터: `data/raw/retail_sales.csv`의 결정론적 합성 데이터
- 검증 방식: 시계열 마지막 30일 holdout
- 기록: MLflow에 매장/상품, 데이터 유형, 학습·검증 행 수, MAE, RMSE, 모델 artifact를 기록
- 기본 실행: `python backend/bootstrap_demo.py`가 기본 조합(매장 1, 상품 1)을 학습

API는 요청 조합의 완료된 MLflow run 중 **MAE가 가장 낮은 모델**을 읽습니다. 이는 데모의 단순 선택 규칙이며, 운영 환경의 승인 절차나 모델 레지스트리 별칭을 대체하지 않습니다.

## Inputs and outputs

| 구분 | 내용 |
| --- | --- |
| 입력 | 양의 정수 매장/상품 ID, 최대 90일의 예측 기간, 프로모션 여부 |
| 출력 | 일별 점 예측(`predicted_sales`)과 Prophet 예측 구간(`lower_bound`, `upper_bound`) |
| 요청 제약 | 시작일 ≤ 종료일, 최대 90일, 사전에 학습된 매장·상품 조합만 가능 |

## Evaluation caveats

- holdout 평가에서 실제 관측된 프로모션 값을 사용합니다. 미래 프로모션 계획이 완벽히 알려진 상황을 가정하므로, 실제 운영 성능보다 낙관적일 수 있습니다.
- 단일 30일 holdout만 사용합니다. 계절·기간 변화에 대한 안정성을 검증하려면 rolling-origin backtest와 naive seasonal baseline 비교가 필요합니다.
- MAE와 RMSE만 기록합니다. 실무 도입 전에는 WAPE/MASE, 품절·과예측 비용, 구간 예측의 coverage를 추가해야 합니다.
- 합성 데이터이므로 실수요 일반화 성능을 주장하지 않습니다.

## Responsible use

이 모델은 재고 배분, 구매 발주, 가격 변경, 고객별 의사결정에 사용하면 안 됩니다. 실제 배포 전에는 데이터 계보, 누수 점검, 편향·드리프트 모니터링, 승인된 모델 레지스트리, 접근 제어를 갖춰야 합니다.
