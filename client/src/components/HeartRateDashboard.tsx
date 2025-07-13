import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
    Chart as ChartJS,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    TimeScale,
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import DateRangePicker from './DateRangePicker';
import TimeSeriesChart from './TimeSeriesChart';
import {
    MultiUserTimeSeriesData,
    QueryInfo,
} from '../services/api';
import {
    fetchAvailableUsers,
    fetchTimeSeriesData,
    handleUserSelection,
    handleDateRangeChange
} from '../utils/dashboardUtils';

ChartJS.register(
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    TimeScale,
);

// Main Dashboard Component
const HeartRateDashboard: React.FC = () => {
    // State
    const [availableUsers, setAvailableUsers] = useState<string[]>([]);
    const [selectedUsers, setSelectedUsers] = useState<string[]>(['user1']);
    const [dateRange, setDateRange] = useState<[Date, Date]>([
        new Date('2025-07-06T01:03:00'),
        new Date('2025-07-06T01:04:00')
    ]);
    const [timeSeriesData, setTimeSeriesData] = useState<MultiUserTimeSeriesData[]>([]);
    const [loading, setLoading] = useState({ timeSeries: false, users: false });
    const [errors, setErrors] = useState({ timeSeries: null as string | null, users: null as string | null });
    const [queryInfo, setQueryInfo] = useState<QueryInfo | null>(null);

    // Date range validation
    const isDateRangeValid = useMemo(() => {
        return dateRange[1] > dateRange[0];
    }, [dateRange]);

    // Data fetching function
    const fetchChartData = useCallback(async () => {
        if (selectedUsers.length === 0 || !isDateRangeValid) return;
        await fetchTimeSeriesData(selectedUsers, dateRange, setTimeSeriesData, setQueryInfo, setLoading, setErrors);
    }, [selectedUsers, dateRange, isDateRangeValid]);

    // Effects
    useEffect(() => {
        fetchAvailableUsers(setAvailableUsers, setSelectedUsers, setLoading, setErrors, selectedUsers);
    }, []);

    useEffect(() => {
        if (selectedUsers.length >= 1) {
            fetchChartData();
        }
    }, [selectedUsers, dateRange, fetchChartData]);

    // Event handlers
    const handleUserSelectionCallback = useCallback((userId: string, checked: boolean) => {
        handleUserSelection(userId, checked, selectedUsers, setSelectedUsers);
    }, [selectedUsers]);

    const handleDateRangeChangeCallback = useCallback((startDate: Date, endDate: Date) => {
        handleDateRangeChange(startDate, endDate, setDateRange);
    }, []);

    return (
        <div className="dashboard-container">
            <h1 className="dashboard-title">Heart Rate Analytics Dashboard</h1>

            {/* Controls */}
            <div className="dashboard-controls">
                <DateRangePicker
                    dateRange={dateRange}
                    onDateRangeChange={handleDateRangeChangeCallback}
                />
            </div>

            {/* User Selection */}
            <div className="dashboard-user-selection">
                <h3 className="dashboard-user-selection-title">User Selection</h3>
                <div className="dashboard-user-checkboxes">
                    {availableUsers.map(userId => (
                        <label
                            key={userId}
                            className={`dashboard-user-label${selectedUsers.includes(userId) ? ' selected' : ''}`}
                        >
                            <input
                                type="checkbox"
                                checked={selectedUsers.includes(userId)}
                                onChange={(e) => handleUserSelectionCallback(userId, e.target.checked)}
                                className="dashboard-checkbox"
                            />
                            <span className="dashboard-user-name">{userId}</span>
                        </label>
                    ))}
                </div>
                {loading.users && <div className="dashboard-loading-message">Loading users...</div>}
                {errors.users && <div className="dashboard-error-message">{errors.users}</div>}
            </div>

            {/* Query Info */}
            {queryInfo && isDateRangeValid && (
                <div className="dashboard-query-info">
                    <strong>Current Query:</strong> {queryInfo.interval} ({queryInfo.table_used}) - {queryInfo.table_description}
                </div>
            )}

            {/* Chart */}
            <TimeSeriesChart
                data={timeSeriesData}
                selectedUsers={selectedUsers}
                loading={loading.timeSeries}
                error={errors.timeSeries}
            />
        </div>
    );
};

export default HeartRateDashboard;