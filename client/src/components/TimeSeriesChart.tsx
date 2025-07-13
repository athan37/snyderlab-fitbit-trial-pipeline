import React, { useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import { MultiUserTimeSeriesData } from '../services/api';
import { TIME_SERIES_COLORS } from '../constants';

interface TimeSeriesChartProps {
    data: MultiUserTimeSeriesData[];
    selectedUsers: string[];
    loading: boolean;
    error: string | null;
}

const createTimeSeriesChartOptions = (title: string) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { position: 'top' as const },
        title: { display: true, text: title, font: { size: 16, weight: 'bold' as const } },
        tooltip: { mode: 'index' as const, intersect: false }
    },
    scales: {
        x: {
            type: 'time' as const,
            time: { unit: 'minute' as const },
            title: { display: true, text: 'Time' }
        },
        y: {
            title: { display: true, text: 'Heart Rate (BPM)' },
            beginAtZero: false
        }
    },
    interaction: { mode: 'nearest' as const, axis: 'x' as const, intersect: false }
});

const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({ data, selectedUsers, loading, error }) => {
    const chartData = useMemo(() => {
        if (!data.length) return null;
        return {
            datasets: data.map((userData, index) => ({
                label: `User ${userData.user_id}`,
                data: userData.data.map(point => ({ x: new Date(point.timestamp), y: point.value })),
                borderColor: TIME_SERIES_COLORS[index % TIME_SERIES_COLORS.length],
                backgroundColor: TIME_SERIES_COLORS[index % TIME_SERIES_COLORS.length],
                tension: 0.1
            }))
        };
    }, [data]);

    const chartTitle = selectedUsers.length === 1
        ? `Heart Rate Time Series - User ${selectedUsers[0]}`
        : `Heart Rate Time Series - Multiple Users`;

    // Memoize chart options to prevent chart recreation
    const chartOptions = useMemo(() => createTimeSeriesChartOptions(chartTitle), [chartTitle]);

    if (loading) {
        return (
            <div className="dashboard-chart-container">
                <h3>Chart 1: Heart Rate Time Series</h3>
                <div className="dashboard-loading-spinner">
                    <div className="dashboard-spinner"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="dashboard-chart-container">
                <h3>Chart 1: Heart Rate Time Series</h3>
                <div className="dashboard-message error">
                    <div>Error: {error}</div>
                </div>
            </div>
        );
    }

    if (!chartData) {
        return (
            <div className="dashboard-chart-container">
                <h3>Chart 1: Heart Rate Time Series</h3>
                <div className="dashboard-message empty">
                    <div>Select at least one user to view data</div>
                </div>
            </div>
        );
    }

    return (
        <div className="dashboard-chart-container">
            <h3>Chart 1: Heart Rate Time Series</h3>
            <div className="dashboard-chart-content">
                <Line
                    data={chartData}
                    options={chartOptions}
                />
            </div>
        </div>
    );
};

export default TimeSeriesChart; 