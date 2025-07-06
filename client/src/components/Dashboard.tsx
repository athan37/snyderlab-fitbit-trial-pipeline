import React, { useState, useEffect } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { apiService } from '../services/api';
import { TimeSeriesData, QueryParams } from '../types/api';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const Dashboard: React.FC = () => {
    const [data, setData] = useState<TimeSeriesData[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [apiInfo, setApiInfo] = useState<any>(null);

    // Form state
    const [startDate, setStartDate] = useState<string>('');
    const [endDate, setEndDate] = useState<string>('');
    const [userId, setUserId] = useState<string>('user1');
    const [metric, setMetric] = useState<string>('activities_heart_intraday');

    // Set default dates (7 days ago to today)
    useEffect(() => {
        const today = new Date();
        const sevenDaysAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

        setEndDate(today.toISOString().split('T')[0]);
        setStartDate(sevenDaysAgo.toISOString().split('T')[0]);
    }, []);

    // Get API info on component mount
    useEffect(() => {
        const fetchApiInfo = async () => {
            try {
                const info = await apiService.getApiInfo();
                setApiInfo(info);
            } catch (err) {
                console.error('Failed to fetch API info:', err);
            }
        };
        fetchApiInfo();
    }, []);

    // Fetch data automatically when any parameter changes
    useEffect(() => {
        // Only fetch if all params are set (dates are set after mount)
        if (startDate && endDate && userId && metric) {
            fetchData();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [startDate, endDate, userId, metric]);

    const fetchData = async () => {
        setLoading(true);
        setError(null);

        try {
            const params: QueryParams = {
                start_date: startDate,
                end_date: endDate,
                user_id: userId,
                metric: metric,
            };

            const response = await apiService.getTimeSeriesData(params);
            setData(response);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to fetch data');
            setData([]);
        } finally {
            setLoading(false);
        }
    };

    // Prepare chart data
    const chartData = {
        labels: data.map(item => new Date(item.timestamp).toLocaleString()),
        datasets: [
            {
                label: `${metric} - ${userId}`,
                data: data.map(item => item.value),
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                tension: 0.1,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: `Heart Rate Data - ${userId}`,
            },
        },
        scales: {
            y: {
                beginAtZero: false,
                title: {
                    display: true,
                    text: 'Heart Rate (BPM)',
                },
            },
            x: {
                title: {
                    display: true,
                    text: 'Time',
                },
            },
        },
    };

    return (
        <div className="container">
            <h1>Heart Rate Dashboard</h1>

            {apiInfo && (
                <div className="dashboard">
                    <strong>API Version:</strong> {apiInfo.version} |
                    <strong> Description:</strong> {apiInfo.description}
                </div>
            )}

            <div className="dashboard">
                <div className="form-grid">
                    <div className="form-group">
                        <label htmlFor="startDate">Start Date:</label>
                        <input
                            id="startDate"
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="endDate">End Date:</label>
                        <input
                            id="endDate"
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="userId">User ID:</label>
                        <select
                            id="userId"
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                        >
                            <option value="user1">User 1</option>
                            <option value="user2">User 2</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="metric">Metric:</label>
                        <select
                            id="metric"
                            value={metric}
                            onChange={(e) => setMetric(e.target.value)}
                        >
                            <option value="activities_heart_intraday">Intraday Heart Rate</option>
                            <option value="activities_heart_summary">Summary Heart Rate</option>
                        </select>
                    </div>
                </div>
            </div>

            {error && (
                <div className="error">
                    Error: {error}
                </div>
            )}

            {loading && (
                <div className="loading">
                    Loading data...
                </div>
            )}

            {data.length > 0 && (
                <div className="dashboard">
                    <h3>Data Points: {data.length}</h3>
                    <div style={{ height: '400px' }}>
                        <Line data={chartData} options={chartOptions} />
                    </div>
                </div>
            )}

            {!loading && !error && data.length === 0 && (
                <div className="no-data">
                    No data available for the selected parameters. Try different dates or user.
                </div>
            )}
        </div>
    );
};

export default Dashboard; 