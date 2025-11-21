import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

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

export const api = {
    predict: async (data: PredictionRequest): Promise<PredictionResponse> => {
        const response = await axios.post<PredictionResponse>(`${API_BASE_URL}/predict`, data);
        return response.data;
    },

    checkHealth: async (): Promise<{ status: string }> => {
        const response = await axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
        return response.data;
    }
};
