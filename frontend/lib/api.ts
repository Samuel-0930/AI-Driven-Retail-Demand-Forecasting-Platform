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

    checkHealth: async (): Promise<{ status: string }> => {
        const response = await axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
        return response.data;
    }
};
