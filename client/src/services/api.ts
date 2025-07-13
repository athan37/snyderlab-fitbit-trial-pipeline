import axios, { AxiosInstance, AxiosResponse } from 'axios';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface TimeSeriesData {
    timestamp: string;
    value: number;
    user_id: string;
}

export interface ApiResponse {
    message: string;
    version: string;
    description: string;
    endpoints: Record<string, string>;
}

export interface QueryParams {
    start_date?: string;
    end_date?: string;
    user_id?: string;
    user_ids?: string;
    metric?: string;
    interval?: string;
}

export interface QueryInfo {
    table_used: string;
    table_description: string;
    interval: string;
}

export interface TimeSeriesResponse {
    data: TimeSeriesData[];
    metadata: {
        query_info?: QueryInfo;
    };
}

export interface MultiUserTimeSeriesData {
    user_id: string;
    data: TimeSeriesData[];
    count: number;
}

export interface MultiUserTimeSeriesResponse {
    data: MultiUserTimeSeriesData[];
    metadata: {
        query_info?: QueryInfo;
    };
}

// ============================================================================
// API SERVICE IMPLEMENTATION
// ============================================================================

// Hard-coded API URL for local development
const API_BASE_URL = 'http://localhost:8000';

class ApiService {
    private api: AxiosInstance;

    constructor() {
        this.api = axios.create({
            baseURL: API_BASE_URL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Setup response interceptor for error handling
        this.api.interceptors.response.use(
            (response) => response,
            (error) => {
                return Promise.reject(error);
            }
        );
    }

    private async makeRequest<T>(endpoint: string, params: any = {}): Promise<T> {
        const queryParams = new URLSearchParams();

        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                queryParams.append(key, String(value));
            }
        });

        const url = queryParams.toString() ? `${endpoint}?${queryParams.toString()}` : endpoint;
        const response: AxiosResponse<T> = await this.api.get(url);
        return response.data;
    }

    // Get API info
    async getApiInfo(): Promise<ApiResponse> {
        return this.makeRequest<ApiResponse>('/');
    }

    // Get available users
    async getAvailableUsers(): Promise<{ users: string[], total_count: number, last_updated: string }> {
        return this.makeRequest<{ users: string[], total_count: number, last_updated: string }>('/users');
    }

    // Get time series data
    async getTimeSeriesData(params: QueryParams): Promise<TimeSeriesResponse> {
        return this.makeRequest<TimeSeriesResponse>('/timeseries', params);
    }

    // Get multi-user time series data
    async getMultiUserTimeSeriesData(params: QueryParams): Promise<MultiUserTimeSeriesResponse> {
        return this.makeRequest<MultiUserTimeSeriesResponse>('/multi-user/timeseries', params);
    }

    // Get single user time series data (alias for getTimeSeriesData for clarity)
    async getSingleUserTimeSeriesData(params: QueryParams): Promise<TimeSeriesResponse> {
        return this.getTimeSeriesData(params);
    }
}

// Create singleton instance
export const apiService = new ApiService(); 