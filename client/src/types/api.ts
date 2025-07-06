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
    metric?: string;
} 