import axios from 'axios';

const API_BASE_URL = '/api/v1';
const COMMAX_REQUEST_TIMEOUT_MS = 75_000;

export interface PredictionRequest {
    store_id: number;
    product_id: number;
    start_date: string;
    end_date: string;
    is_promo?: boolean;
}

export interface PredictionPoint {
    date: string;
    forecast: number;
    lower_bound: number;
    upper_bound: number;
}

export interface PredictionResponse {
    store_id: number;
    product_id: number;
    predictions: PredictionPoint[];
}

export interface MetricSummary {
    mae: number;
    wape: number;
    mase: number;
}

export interface BacktestFold {
    fold: number;
    train_end: string;
    test_start: string;
    test_end: string;
    prophet: MetricSummary;
    seasonal_naive: MetricSummary;
}

export interface BacktestResponse {
    store_id: number;
    product_id: number;
    dataset_type: string;
    evaluation_method: string;
    horizon_days: number;
    folds: number;
    prophet: MetricSummary;
    seasonal_naive: MetricSummary;
    fold_results: BacktestFold[];
}

export interface CommaxEvaluationResponse {
    dataset_type: string;
    scope: string;
    period: string;
    evaluation_method: string;
    items: number;
    horizon_months: number;
    folds: number;
    models: Record<string, MetricSummary>;
    pattern_results: Array<{
        pattern: string;
        items: number;
        champion: string;
        models: Record<string, MetricSummary>;
    }>;
}

export interface CommaxItem { item_code: string; item_name: string; pattern: string; }
export interface CommaxForecastResponse {
    item_code: string; item_name: string; pattern: string; champion: string; benchmark_wape: number;
    predictions: Array<{ date: string; forecast: number }>;
}
export interface CommaxBacktestResponse {
    item_code: string; pattern: string; champion: string; benchmark_wape: number; holdout_wape: number;
    interval_level: number;
    interval_coverage: number;
    demand_variability_risk: "low" | "medium" | "high";
    risk_message: string;
    planning_upper_total: number;
    forecast_total: number;
    points: Array<{ date: string; actual: number; forecast: number; lower_bound: number; upper_bound: number; absolute_error: number }>;
}
export interface CommaxInventoryPlanResponse {
    item_code: string;
    item_name: string;
    pattern: string;
    champion: string;
    lead_time_months: number;
    service_level: number;
    on_hand_inventory: number;
    incoming_inventory: number;
    available_inventory: number;
    forecast_demand: number;
    safety_stock: number;
    planning_demand: number;
    recommended_order: number;
    inventory_risk: "low" | "medium" | "high";
    risk_message: string;
    assumption: string;
}

export class ApiError extends Error {
    constructor(
        message: string,
        public readonly status?: number,
    ) {
        super(message);
    }
}

export const api = {
    predict: async (data: PredictionRequest): Promise<PredictionResponse> => {
        try {
            const response = await axios.post<PredictionResponse>(`${API_BASE_URL}/predict`, data, { timeout: 10_000 });
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error)) {
                const detail = error.response?.data?.detail;
                throw new ApiError(typeof detail === 'string' ? detail : 'Prediction request failed', error.response?.status);
            }
            throw error;
        }
    },

    getEvaluation: async (storeId: number, productId: number): Promise<BacktestResponse> => {
        try {
            const response = await axios.get<BacktestResponse>(`${API_BASE_URL}/evaluation`, {
                params: { store_id: storeId, product_id: productId },
                timeout: 10_000,
            });
            return response.data;
        } catch (error) {
            if (axios.isAxiosError(error)) {
                const detail = error.response?.data?.detail;
                throw new ApiError(typeof detail === 'string' ? detail : 'Evaluation request failed', error.response?.status);
            }
            throw error;
        }
    },

    getCommaxEvaluation: async (): Promise<CommaxEvaluationResponse> => {
        const response = await axios.get<CommaxEvaluationResponse>(`${API_BASE_URL}/commax/evaluation`, { timeout: COMMAX_REQUEST_TIMEOUT_MS });
        return response.data;
    },

    getCommaxItems: async (): Promise<CommaxItem[]> => (await axios.get(`${API_BASE_URL}/commax/items`, { timeout: COMMAX_REQUEST_TIMEOUT_MS })).data,
    getCommaxForecast: async (itemCode: string, horizonMonths: number): Promise<CommaxForecastResponse> => (await axios.get(`${API_BASE_URL}/commax/forecast`, { params: { item_code: itemCode, horizon_months: horizonMonths }, timeout: COMMAX_REQUEST_TIMEOUT_MS })).data,
    getCommaxBacktest: async (itemCode: string, horizonMonths: number): Promise<CommaxBacktestResponse> => (await axios.get(`${API_BASE_URL}/commax/backtest`, { params: { item_code: itemCode, horizon_months: horizonMonths }, timeout: COMMAX_REQUEST_TIMEOUT_MS })).data,
    getCommaxInventoryPlan: async (itemCode: string, onHandInventory: number, incomingInventory: number, leadTimeMonths: number, serviceLevel: number): Promise<CommaxInventoryPlanResponse> => (await axios.get(`${API_BASE_URL}/commax/inventory-plan`, {
        params: {
            item_code: itemCode,
            on_hand_inventory: onHandInventory,
            incoming_inventory: incomingInventory,
            lead_time_months: leadTimeMonths,
            service_level: serviceLevel,
        },
        timeout: COMMAX_REQUEST_TIMEOUT_MS,
    })).data,

    checkHealth: async (): Promise<{ status: string }> => {
        const response = await axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
        return response.data;
    }
};
