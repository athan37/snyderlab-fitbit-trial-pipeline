import axios from 'axios';
import { TimeSeriesData, ApiResponse, QueryParams } from '../types/api';

// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
});

export const apiService = {
    // Get API info
    getApiInfo: async (): Promise<ApiResponse> => {
        const response = await api.get<ApiResponse>('/');
        return response.data;
    },

    // Get time series data
    getTimeSeriesData: async (params: QueryParams): Promise<TimeSeriesData[]> => {
        const queryParams = new URLSearchParams();

        if (params.start_date) queryParams.append('start_date', params.start_date);
        if (params.end_date) queryParams.append('end_date', params.end_date);
        if (params.user_id) queryParams.append('user_id', params.user_id);
        if (params.metric) queryParams.append('metric', params.metric);

        const response = await api.get<TimeSeriesData[]>(`/timeseries?${queryParams.toString()}`);
        return response.data;
    },
}; 