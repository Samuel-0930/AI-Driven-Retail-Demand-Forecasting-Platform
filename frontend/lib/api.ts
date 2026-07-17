import axios from 'axios';

const API_BASE_URL = '/api/v1';

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
    prophet: MetricSummary;
    seasonal_naive: MetricSummary;
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
        const response = await axios.get<CommaxEvaluationResponse>(`${API_BASE_URL}/commax/evaluation`, { timeout: 10_000 });
        return response.data;
    },

    checkHealth: async (): Promise<{ status: string }> => {
        const response = await axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
        return response.data;
    }
};
