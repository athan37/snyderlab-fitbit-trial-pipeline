import { apiService, MultiUserTimeSeriesData, QueryInfo } from '../services/api';

// Date formatting utility
export const formatDate = (date: Date): string => date.toISOString().slice(0, 19);

// Generic error handler
const handleError = (error: unknown, setErrors: (errors: any) => void, errorKey: string, fallbackMessage: string) => {
    setErrors((prev: any) => ({
        ...prev,
        [errorKey]: error instanceof Error ? error.message : fallbackMessage
    }));
};

// Generic loading state handler
const setLoadingState = (setLoading: (loading: any) => void, key: string, isLoading: boolean) => {
    setLoading((prev: any) => ({ ...prev, [key]: isLoading }));
};

// Data fetching utilities
export const fetchAvailableUsers = async (
    setAvailableUsers: (users: string[]) => void,
    setSelectedUsers: (users: string[]) => void,
    setLoading: (loading: any) => void,
    setErrors: (errors: any) => void,
    selectedUsers: string[]
) => {
    setLoadingState(setLoading, 'users', true);
    setErrors((prev: any) => ({ ...prev, users: null }));

    try {
        const response = await apiService.getAvailableUsers();
        setAvailableUsers(response.users);
        if (response.users.length > 0 && selectedUsers.length === 0) {
            setSelectedUsers([response.users[0]]);
        }
    } catch (error) {
        handleError(error, setErrors, 'users', 'Failed to fetch users');
        setAvailableUsers(['user1', 'user2']);
        setSelectedUsers(['user1']);
    } finally {
        setLoadingState(setLoading, 'users', false);
    }
};

export const fetchTimeSeriesData = async (
    selectedUsers: string[],
    dateRange: [Date, Date],
    setTimeSeriesData: (data: MultiUserTimeSeriesData[]) => void,
    setQueryInfo: (info: QueryInfo | null) => void,
    setLoading: (loading: any) => void,
    setErrors: (errors: any) => void
) => {
    if (selectedUsers.length === 0) return;

    setLoadingState(setLoading, 'timeSeries', true);
    setErrors((prev: any) => ({ ...prev, timeSeries: null }));

    try {
        const params = { start_date: formatDate(dateRange[0]), end_date: formatDate(dateRange[1]) };

        if (selectedUsers.length === 1) {
            const response = await apiService.getSingleUserTimeSeriesData({ ...params, user_id: selectedUsers[0] });
            setTimeSeriesData([{ user_id: selectedUsers[0], data: response.data, count: response.data.length }]);
            setQueryInfo(response.metadata.query_info || null);
        } else {
            const response = await apiService.getMultiUserTimeSeriesData({ ...params, user_ids: selectedUsers.join(',') });
            setTimeSeriesData(response.data);
            if (response.data.length > 0) setQueryInfo(response.metadata.query_info || null);
        }
    } catch (error) {
        handleError(error, setErrors, 'timeSeries', 'Failed to fetch time series data');
        setTimeSeriesData([]);
    } finally {
        setLoadingState(setLoading, 'timeSeries', false);
    }
};

// Event handler utilities
export const handleUserSelection = (
    userId: string,
    checked: boolean,
    selectedUsers: string[],
    setSelectedUsers: (users: string[]) => void
) => {
    setSelectedUsers(checked ? [...selectedUsers, userId] : selectedUsers.filter(id => id !== userId));
};

export const handleDateRangeChange = (
    startDate: Date,
    endDate: Date,
    setDateRange: (range: [Date, Date]) => void
) => {
    setDateRange([startDate, endDate]);
}; 