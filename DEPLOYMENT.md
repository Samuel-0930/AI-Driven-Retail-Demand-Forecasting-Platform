# Demand Signal 공개 데모 배포 가이드

## 배포 구성

```text
Vercel (Next.js dashboard) → Render (FastAPI analysis API) → versioned public demo data
```

공개 환경에는 `data/public/`만 포함합니다. 이 디렉터리는 상위 20개 품목의 품목 코드·품목명·수요 패턴·월·출하량과 사전 계산된 benchmark만 담습니다. 원본 COMMAX CSV와 전체 파생 결과는 배포하지 않습니다.

## 1. Render: 분석 API

1. GitHub 저장소를 Render에 연결합니다.
2. 저장소 루트의 `render.yaml`을 Blueprint로 선택합니다.
3. 서비스가 생성되면 `/health`가 `200`을 반환하는지 확인합니다.

`render.yaml`은 Dockerfile 기반 FastAPI 서비스를 Singapore 리전에 생성하고, 배포 환경에서는 API 문서를 비활성화합니다. Docker는 Render가 제공하는 `PORT` 환경 변수를 사용합니다.

선택 환경 변수:

| 변수 | 용도 | 기본값 |
| --- | --- | --- |
| `ENABLE_API_DOCS` | `/docs` 공개 여부 | `false` (Render) |
| `COMMAX_DATA_PATH` | 공개 대시보드 CSV 위치 | `data/public/commax_dashboard_top20.csv` |
| `COMMAX_EVALUATION_PATH` | benchmark JSON 위치 | `data/public/commax_evaluation.json` |
| `ALLOWED_ORIGINS` | 직접 API 호출을 허용할 Origin 목록 | 로컬 Origin 2개 |

## 2. Vercel: 대시보드

1. 같은 GitHub 저장소를 Vercel에 연결합니다.
2. **Root Directory**를 `frontend`로 설정합니다.
3. Production과 Preview 환경에 `BACKEND_URL`을 Render API의 HTTPS URL로 설정합니다. 예: `https://demand-signal-api.onrender.com`
4. 배포 후 `/api/v1/commax/evaluation`과 대시보드에서 품목별 비교가 동작하는지 확인합니다.

Next.js rewrite가 `/api/*` 요청을 `BACKEND_URL`로 전달하므로, 브라우저는 동일한 Vercel Origin에서 API를 호출합니다. Vercel은 외부 Origin으로의 rewrite를 지원합니다.

## 공개 전 확인

- Render API의 `/health` 응답 확인
- Vercel 대시보드에서 최소 2개 품목의 실제 vs 당시 예측 비교 확인
- 브라우저 콘솔 및 Render 로그에 오류가 없는지 확인
- 원본 CSV, MLflow run, `.env`, Grafana 비밀번호가 이미지·저장소·로그에 포함되지 않았는지 확인
- 필요 시 `ALLOWED_ORIGINS`를 실제 Vercel 도메인으로 제한

## 범위와 비용

초기 공개 데모에는 대시보드와 분석 API만 배포합니다. MLflow, Prometheus, Grafana는 로컬 재현·엔지니어링 증거로 유지하고 공개 데모의 운영 의존성에서는 제외합니다. Render의 무료 인스턴스는 유휴 상태에서 재시작될 수 있으므로, 첫 API 요청이 느릴 수 있습니다.

## 참고

- [Render Blueprint YAML reference](https://render.com/docs/blueprint-spec)
- [Render Docker deployment](https://render.com/docs/docker)
- [Vercel external rewrites](https://vercel.com/docs/routing/rewrites)
