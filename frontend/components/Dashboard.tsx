"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  CommaxBacktestResponse,
  CommaxEvaluationResponse,
  CommaxInventoryPlanResponse,
  CommaxItem,
  api,
} from "../lib/api";

const DEFAULT_ITEM = "SDC000036AXX";

const modelLabels: Record<string, string> = {
  croston_sba: "Croston/SBA",
  seasonal_croston_sba: "Seasonal Croston/SBA",
  seasonal_naive: "Seasonal naive",
  prophet: "Prophet",
  tsb: "TSB",
};

const patternLabels: Record<string, string> = {
  Erratic: "변동형",
  Intermittent: "간헐형",
  Lumpy: "복합 간헐형",
  Smooth: "안정형",
};

const riskLabels = {
  low: "낮음",
  medium: "보통",
  high: "높음",
};

const formatNumber = (value: number) =>
  new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 1 }).format(value);

export default function Dashboard() {
  const [evaluation, setEvaluation] = useState<CommaxEvaluationResponse | null>(null);
  const [items, setItems] = useState<CommaxItem[]>([]);
  const [itemCode, setItemCode] = useState(DEFAULT_ITEM);
  const [backtest, setBacktest] = useState<CommaxBacktestResponse | null>(null);
  const [inventoryPlan, setInventoryPlan] = useState<CommaxInventoryPlanResponse | null>(null);
  const [onHandInventory, setOnHandInventory] = useState(0);
  const [incomingInventory, setIncomingInventory] = useState(0);
  const [leadTimeMonths, setLeadTimeMonths] = useState(1);
  const [serviceLevel, setServiceLevel] = useState(0.8);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [inventoryError, setInventoryError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
      setLoading(true);
      setError("");
      try {
        const [evaluationResult, itemResult, backtestResult] = await Promise.all([
          api.getCommaxEvaluation(),
          api.getCommaxItems(),
          api.getCommaxBacktest(DEFAULT_ITEM, 6),
        ]);
        setEvaluation(evaluationResult);
        setItems(itemResult);
        setBacktest(backtestResult);
      } catch {
        setError("분석 결과를 불러오지 못했습니다. 무료 데모 서버가 시작되는 중일 수 있으니 잠시 후 다시 시도해 주세요.");
      } finally {
        setLoading(false);
      }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const selectedItem = items.find((item) => item.item_code === itemCode);
  const groupedItems = useMemo(
    () =>
      ["Erratic", "Intermittent", "Lumpy", "Smooth"].map((pattern) => ({
        pattern,
        items: items.filter((item) => item.pattern === pattern),
      })),
    [items],
  );

  const modelResults = useMemo(
    () =>
      evaluation
        ? Object.entries(evaluation.models).sort(([, left], [, right]) => left.wape - right.wape)
        : [],
    [evaluation],
  );
  const globalChampion = evaluation?.champion_manifest.global_fallback;
  const inventoryPolicy = globalChampion ? evaluation?.inventory_policy_metrics.models[globalChampion] : undefined;

  const loadBacktest = async () => {
    setLoading(true);
    setError("");
    try {
      setBacktest(await api.getCommaxBacktest(itemCode, 6));
    } catch {
      setError("선택한 품목의 검증 결과를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const loadInventoryPlan = async () => {
    setInventoryLoading(true);
    setInventoryError("");
    try {
      setInventoryPlan(await api.getCommaxInventoryPlan(itemCode, onHandInventory, incomingInventory, leadTimeMonths, serviceLevel));
    } catch {
      setInventoryError("재고 시뮬레이션 결과를 불러오지 못했습니다.");
    } finally {
      setInventoryLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
          <a href="#top" className="flex items-center gap-3 font-semibold tracking-tight">
            <span className="h-2.5 w-2.5 rounded-full bg-teal-700" aria-hidden="true" />
            Demand Signal
          </a>
          <nav className="flex items-center gap-5 text-sm text-slate-600" aria-label="프로젝트 링크">
            <a className="transition hover:text-teal-700" href="#validation">검증 결과</a>
            <a
              className="transition hover:text-teal-700"
              href="https://github.com/Samuel-0930/AI-Driven-Retail-Demand-Forecasting-Platform"
              target="_blank"
              rel="noreferrer"
            >
              GitHub ↗
            </a>
          </nav>
        </div>
      </header>

      <main id="top" className="mx-auto max-w-6xl px-5 pb-20 pt-14 sm:px-8 sm:pt-20">
        <section className="max-w-4xl">
          <p className="mb-5 text-sm font-semibold tracking-wide text-teal-700">
            RETAIL DEMAND FORECASTING · DATA ANALYSIS PORTFOLIO
          </p>
          <h1 className="text-balance text-4xl font-semibold leading-tight tracking-[-0.035em] sm:text-6xl">
            간헐 수요는 하나의 모델로<br className="hidden sm:block" /> 설명할 수 없습니다.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            COMMAX 실제 출하 데이터의 수요 패턴을 분류하고, 시계열 교차 검증으로 품목군마다 더 적합한 예측 모델을 선택했습니다.
          </p>
          <dl className="mt-10 grid max-w-3xl grid-cols-2 gap-x-8 gap-y-6 border-y border-slate-200 py-6 sm:grid-cols-4">
            <div>
              <dt className="text-sm text-slate-500">관측치</dt>
              <dd className="mt-1 text-xl font-semibold">20,096</dd>
            </div>
            <div>
              <dt className="text-sm text-slate-500">전체 품목</dt>
              <dd className="mt-1 text-xl font-semibold">157</dd>
            </div>
            <div>
              <dt className="text-sm text-slate-500">평가 품목</dt>
              <dd className="mt-1 text-xl font-semibold">Top 20</dd>
            </div>
            <div>
              <dt className="text-sm text-slate-500">검증 설계</dt>
              <dd className="mt-1 text-xl font-semibold">3 × 6개월</dd>
            </div>
          </dl>
        </section>

        {error && (
          <div role="alert" className="mt-10 flex flex-wrap items-center justify-between gap-4 border-l-2 border-red-600 bg-white px-4 py-3 text-sm text-red-700">
            <span>{error}</span>
            <button
              type="button"
              onClick={() => void loadDashboard()}
              disabled={loading}
              className="font-semibold text-teal-700 underline underline-offset-4 disabled:cursor-not-allowed disabled:text-slate-400"
            >
              다시 시도
            </button>
          </div>
        )}

        <section id="validation" className="scroll-mt-8 pt-20">
          <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr]">
            <div>
              <p className="text-sm font-semibold text-teal-700">01 · 핵심 결과</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight">패턴별 champion 모델</h2>
              <p className="mt-4 leading-7 text-slate-600">
                전체 평균만 비교하지 않고 수요 패턴별 WAPE가 가장 낮은 모델을 선택했습니다. 변동형에는 계절 Croston, 나머지 패턴에는 Croston/SBA가 우세했습니다.
              </p>
              <p className="mt-4 border-l-2 border-slate-300 pl-4 text-sm leading-6 text-slate-500">
                <span className="font-semibold text-slate-700">WAPE란?</span> 전체 실제 출하량 대비 절대 예측 오차의 비율입니다. <span className="font-semibold text-teal-700">낮을수록 실제값에 가까운 예측</span>입니다.
              </p>
              <div className="mt-8 border-l-2 border-teal-700 pl-5">
                <p className="text-sm text-slate-500">분석 결론</p>
                <p className="mt-2 text-lg font-medium leading-7">
                  복잡한 Prophet보다 간헐 수요 특화 baseline이 더 정확했습니다.
                </p>
              </div>
            </div>

            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
                  <tr>
                    <th className="px-5 py-4 font-medium">수요 패턴</th>
                    <th className="px-5 py-4 font-medium">품목</th>
                    <th className="px-5 py-4 font-medium">선택 모델</th>
                    <th className="px-5 py-4 text-right font-medium">WAPE</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {evaluation?.pattern_results.map((result) => (
                    <tr key={result.pattern}>
                      <td className="px-5 py-4 font-medium">
                        {patternLabels[result.pattern] ?? result.pattern}
                        <span className="ml-2 text-xs font-normal text-slate-400">{result.pattern}</span>
                      </td>
                      <td className="px-5 py-4 text-slate-600">{result.items}</td>
                      <td className="px-5 py-4 text-slate-700">{modelLabels[result.champion] ?? result.champion}</td>
                      <td className="px-5 py-4 text-right font-semibold text-teal-700">
                        {result.models[result.champion]?.wape.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                  {!evaluation && (
                    <tr><td colSpan={4} className="px-5 py-10 text-center text-slate-400">{loading ? "결과를 불러오는 중입니다." : "결과가 없습니다."}</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-14 grid gap-10 border-t border-slate-200 pt-10 lg:grid-cols-2">
            <div>
              <h3 className="font-semibold">전체 모델 비교</h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">
                MAE는 평균 절대 오차(출하량 단위), MASE는 naive 기준으로 스케일링한 오차입니다. 세 지표 모두 낮을수록 좋습니다.
              </p>
              <div className="mt-5 overflow-hidden rounded-lg border border-slate-200 bg-white">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-200 bg-slate-50 text-slate-500">
                    <tr>
                      <th className="px-4 py-3 font-medium">모델</th>
                      <th className="px-4 py-3 text-right font-medium">WAPE</th>
                      <th className="px-4 py-3 text-right font-medium">MAE</th>
                      <th className="px-4 py-3 text-right font-medium">MASE</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {modelResults.map(([model, metrics], index) => (
                      <tr key={model} className={index === 0 ? "bg-teal-50/50" : ""}>
                        <td className={index === 0 ? "px-4 py-3 font-semibold text-slate-900" : "px-4 py-3 text-slate-600"}>
                          {modelLabels[model] ?? model}
                        </td>
                        <td className={index === 0 ? "px-4 py-3 text-right font-semibold text-teal-700" : "px-4 py-3 text-right tabular-nums text-slate-600"}>
                          {metrics.wape.toFixed(2)}%
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-slate-600">{formatNumber(metrics.mae)}</td>
                        <td className="px-4 py-3 text-right tabular-nums text-slate-600">{metrics.mase?.toFixed(3) ?? "계산 불가"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div>
              <h3 className="font-semibold">검증 방법</h3>
              <dl className="mt-5 grid gap-5 text-sm sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
                <div>
                  <dt className="text-slate-500">시간 분할</dt>
                  <dd className="mt-1 font-medium">Rolling origin 3회</dd>
                </div>
                <div>
                  <dt className="text-slate-500">예측 구간</dt>
                  <dd className="mt-1 font-medium">회차별 6개월</dd>
                </div>
                <div>
                  <dt className="text-slate-500">선택 기준</dt>
                  <dd className="mt-1 font-medium">패턴별 최저 WAPE</dd>
                </div>
              </dl>
              <p className="mt-6 text-sm leading-6 text-slate-500">
                평가 대상은 누적 출하량 상위 20개 품목입니다. 이 결과를 전체 157개 품목의 운영 성능으로 일반화하지 않았습니다.
              </p>
            </div>
          </div>
        </section>

        <section className="pt-24">
          <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
            <div>
              <p className="text-sm font-semibold text-teal-700">03 · 품목별 검증</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight">실제 출하량 vs 당시 예측</h2>
              <p className="mt-3 max-w-2xl leading-7 text-slate-600">
                가장 최근 6개월을 숨긴 뒤, 그 시점에 알 수 있었던 데이터만으로 생성한 예측과 실제 출하량을 비교합니다. 예측 범위는 그 이전 검증 오차만으로 계산했습니다.
              </p>
            </div>
            <div className="flex w-full gap-2 sm:w-auto">
              <label className="sr-only" htmlFor="item-code">품목 선택</label>
              <select
                id="item-code"
                value={itemCode}
                onChange={(event) => {
                  setItemCode(event.target.value);
                  setInventoryPlan(null);
                }}
                className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-teal-700 focus:ring-2 focus:ring-teal-700/15 sm:w-72"
              >
                {groupedItems.map((group) => (
                  <optgroup key={group.pattern} label={`${patternLabels[group.pattern]} · ${group.pattern}`}>
                    {group.items.map((item) => (
                      <option key={item.item_code} value={item.item_code}>{item.item_name}</option>
                    ))}
                  </optgroup>
                ))}
              </select>
              <button
                type="button"
                onClick={() => void loadBacktest()}
                disabled={loading}
                className="shrink-0 rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "불러오는 중" : "비교 보기"}
              </button>
            </div>
          </div>

          {inventoryPolicy && evaluation && globalChampion && (
            <div className="mt-10 rounded-xl border border-teal-100 bg-teal-50/50 p-6 sm:p-7">
              <p className="text-sm font-semibold text-teal-700">02 · 주문 의사결정 backtest</p>
              <h3 className="mt-2 text-xl font-semibold">{modelLabels[globalChampion] ?? globalChampion}의 안전재고 정책 효과</h3>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
                같은 360개 holdout 월에서 point forecast 주문량과 80% split-conformal 안전재고 주문량을 비교했습니다. 부족 비용 : 잉여 비용은 {evaluation.inventory_policy_metrics.assumptions.cost_ratio}으로 가정한 시뮬레이션이며, 실제 금액이나 운영 성과를 뜻하지 않습니다.
              </p>
              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                <div className="rounded-lg bg-white p-4 ring-1 ring-teal-100">
                  <p className="text-xs text-slate-500">부족 수량</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums">{formatNumber(inventoryPolicy.point_forecast.stockout_units)} → {formatNumber(inventoryPolicy["80"].stockout_units)}</p>
                </div>
                <div className="rounded-lg bg-white p-4 ring-1 ring-teal-100">
                  <p className="text-xs text-slate-500">충족률</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums">{inventoryPolicy.point_forecast.fill_rate.toFixed(1)}% → {inventoryPolicy["80"].fill_rate.toFixed(1)}%</p>
                </div>
                <div className="rounded-lg bg-white p-4 ring-1 ring-teal-100">
                  <p className="text-xs text-slate-500">가정 비용</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums">{formatNumber(inventoryPolicy.point_forecast.assumed_cost)} → {formatNumber(inventoryPolicy["80"].assumed_cost)}</p>
                </div>
              </div>
              <p className="mt-4 text-xs leading-5 text-slate-500">80% 정책은 품절 위험을 낮추는 대신 잉여 재고를 늘릴 수 있습니다. 비용 비율과 리드타임은 실제 운영 데이터로 재설정해야 합니다.</p>
            </div>
          )}

          {backtest && (
            <>
              <div className="mt-8 overflow-hidden rounded-xl border border-slate-200 bg-white">
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 px-5 py-4 sm:px-7">
                <div>
                  <p className="font-semibold">{selectedItem?.item_name ?? backtest.item_code}</p>
                  <p className="mt-1 text-sm text-slate-500">
                    {patternLabels[backtest.pattern] ?? backtest.pattern} · {modelLabels[backtest.champion] ?? backtest.champion}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Holdout WAPE</p>
                  <p className="mt-1 text-2xl font-semibold text-teal-700">{backtest.holdout_wape.toFixed(2)}%</p>
                </div>
                </div>

                <div className="grid divide-y divide-slate-200 border-b border-slate-200 bg-slate-50 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
                <div className="px-5 py-4 sm:px-7">
                  <p className="text-xs text-slate-500">{backtest.interval_level}% 예측 구간 적중률</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums">{backtest.interval_coverage.toFixed(1)}%</p>
                  <p className="mt-1 text-xs text-slate-500">직전 {backtest.calibration_residuals}개 오차로 보정</p>
                </div>
                <div className="px-5 py-4 sm:px-7">
                  <p className="text-xs text-slate-500">수요 변동 리스크</p>
                  <p className="mt-1 text-lg font-semibold text-teal-700">{riskLabels[backtest.demand_variability_risk]}</p>
                </div>
                <div className="px-5 py-4 sm:px-7">
                  <p className="text-xs text-slate-500">보수적 6개월 수요 기준</p>
                  <p className="mt-1 text-lg font-semibold tabular-nums">{formatNumber(backtest.planning_upper_total)}</p>
                </div>
                </div>

                <div className="border-b border-slate-200 px-5 py-4 text-sm leading-6 text-slate-600 sm:px-7">
                <span className="font-semibold text-slate-800">해석:</span> {backtest.risk_message} 현재 재고와 리드타임 정보가 없으므로 품절 가능성을 단정하지 않으며, 위 기준은 재고 검토를 위한 수요 상한 참고값입니다.
                </div>

                <div className="h-[360px] px-2 py-7 sm:px-5">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={backtest.points} margin={{ top: 8, right: 18, left: 4, bottom: 0 }}>
                    <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 12 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: "#64748b", fontSize: 12 }} tickLine={false} axisLine={false} width={55} />
                    <Tooltip
                      contentStyle={{ border: "1px solid #e2e8f0", borderRadius: 8, boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)" }}
                      formatter={(value) => formatNumber(Number(value))}
                    />
                    <Legend wrapperStyle={{ fontSize: 12, paddingTop: 16 }} />
                    <Area type="monotone" dataKey="lower_bound" name="예측 구간 하한" stroke="none" fill="transparent" stackId="interval" legendType="none" />
                    <Area type="monotone" dataKey={(point) => point.upper_bound - point.lower_bound} name={`${backtest.interval_level}% 예측 구간`} stroke="none" fill="#99f6e4" fillOpacity={0.55} stackId="interval" />
                    <Line type="monotone" dataKey="actual" name="실제 출하량" stroke="#0f766e" strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                    <Line type="monotone" dataKey="forecast" name="당시 예측" stroke="#475569" strokeWidth={2} strokeDasharray="6 5" dot={{ r: 3 }} />
                  </ComposedChart>
                </ResponsiveContainer>
                </div>

                <div className="overflow-x-auto border-t border-slate-200">
                <table className="w-full min-w-[620px] text-left text-sm">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      <th className="px-5 py-3 font-medium sm:px-7">월</th>
                      <th className="px-5 py-3 text-right font-medium">실제</th>
                      <th className="px-5 py-3 text-right font-medium">예측</th>
                      <th className="px-5 py-3 text-right font-medium">{backtest.interval_level}% 구간</th>
                      <th className="px-5 py-3 text-right font-medium sm:px-7">절대 오차</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {backtest.points.map((point) => (
                      <tr key={point.date}>
                        <td className="px-5 py-3 font-medium sm:px-7">{point.date}</td>
                        <td className="px-5 py-3 text-right tabular-nums">{formatNumber(point.actual)}</td>
                        <td className="px-5 py-3 text-right tabular-nums">{formatNumber(point.forecast)}</td>
                        <td className="px-5 py-3 text-right tabular-nums text-slate-500">{formatNumber(point.lower_bound)}–{formatNumber(point.upper_bound)}</td>
                        <td className="px-5 py-3 text-right tabular-nums text-slate-500 sm:px-7">{formatNumber(point.absolute_error)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>
              </div>

              <section className="mt-10 rounded-xl border border-slate-200 bg-white p-5 sm:p-7">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-teal-700">03 · 재고 시뮬레이션</p>
                    <h3 className="mt-2 text-2xl font-semibold tracking-tight">입력값 기반 권장 발주량</h3>
                    <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">현재고와 입고 예정 재고를 입력하면, 리드타임 동안의 예측 수요와 선택한 서비스 수준을 기준으로 발주 참고값을 계산합니다.</p>
                  </div>
                </div>

                <form
                  className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void loadInventoryPlan();
                  }}
                >
                  <label className="text-sm text-slate-600">
                    현재 가용 재고
                    <input type="number" min="0" value={onHandInventory} onChange={(event) => setOnHandInventory(Number(event.target.value))} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-900 outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-700/15" />
                  </label>
                  <label className="text-sm text-slate-600">
                    입고 예정 수량
                    <input type="number" min="0" value={incomingInventory} onChange={(event) => setIncomingInventory(Number(event.target.value))} className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-900 outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-700/15" />
                  </label>
                  <label className="text-sm text-slate-600">
                    리드타임
                    <select value={leadTimeMonths} onChange={(event) => setLeadTimeMonths(Number(event.target.value))} className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-700/15">
                      {[1, 2, 3, 4, 5, 6].map((months) => <option key={months} value={months}>{months}개월</option>)}
                    </select>
                  </label>
                  <label className="text-sm text-slate-600">
                    목표 서비스 수준
                    <select value={serviceLevel} onChange={(event) => setServiceLevel(Number(event.target.value))} className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-700/15">
                      <option value={0.8}>80%</option>
                      <option value={0.9}>90%</option>
                      <option value={0.95}>95%</option>
                    </select>
                  </label>
                  <button type="submit" disabled={inventoryLoading} className="self-end rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-50">
                    {inventoryLoading ? "계산 중" : "발주량 계산"}
                  </button>
                </form>

                {inventoryError && <p role="alert" className="mt-4 text-sm text-red-700">{inventoryError}</p>}

                {inventoryPlan && (
                  <div className="mt-7 border-t border-slate-200 pt-6">
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                      <div><p className="text-xs text-slate-500">리드타임 예측 수요</p><p className="mt-1 text-xl font-semibold tabular-nums">{formatNumber(inventoryPlan.forecast_demand)}</p></div>
                      <div><p className="text-xs text-slate-500">안전 재고 ({inventoryPlan.service_level}%)</p><p className="mt-1 text-xl font-semibold tabular-nums">{formatNumber(inventoryPlan.safety_stock)}</p></div>
                      <div><p className="text-xs text-slate-500">가용 재고</p><p className="mt-1 text-xl font-semibold tabular-nums">{formatNumber(inventoryPlan.available_inventory)}</p></div>
                      <div><p className="text-xs text-slate-500">권장 발주량</p><p className="mt-1 text-xl font-semibold tabular-nums text-teal-700">{formatNumber(inventoryPlan.recommended_order)}</p></div>
                    </div>
                    <div className="mt-6 border-l-2 border-teal-700 pl-4 text-sm leading-6 text-slate-600">
                      <span className="font-semibold text-slate-800">재고 커버리지 리스크 · {riskLabels[inventoryPlan.inventory_risk]}</span> — {inventoryPlan.risk_message}<br />
                      <span className="text-slate-500">계획 수요 {formatNumber(inventoryPlan.planning_demand)} · {inventoryPlan.assumption}</span>
                    </div>
                  </div>
                )}
              </section>
            </>
          )}
        </section>

        <section className="mt-24 border-t border-slate-200 pt-10">
          <div className="grid gap-8 sm:grid-cols-[1fr_auto] sm:items-start">
            <div>
              <p className="font-semibold">프로젝트 범위</p>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
                FastAPI 예측 API, MLflow 실험 추적, Docker 개발 환경과 CI를 포함합니다. 합성 데이터 데모는 재현 가능한 파이프라인 검증용이며, 위 성능 수치는 COMMAX 실제 데이터 평가에서만 가져왔습니다.
              </p>
            </div>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="text-sm font-semibold text-teal-700 hover:text-teal-800"
            >
              API 문서 보기 ↗
            </a>
          </div>
        </section>
      </main>
    </div>
  );
}
