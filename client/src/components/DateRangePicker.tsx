import React, { useState, useEffect } from 'react';

interface DateRangePickerProps {
    dateRange: [Date, Date];
    onDateRangeChange: (startDate: Date, endDate: Date) => void;
    label?: string;
}

const DateRangePicker: React.FC<DateRangePickerProps> = ({
    dateRange,
    onDateRangeChange,
    label = "Date Range:"
}) => {
    const [isValid, setIsValid] = useState(true);

    const formatDateForInput = (date: Date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
    };

    // Validate date range whenever it changes
    useEffect(() => {
        const isValidRange = dateRange[1] > dateRange[0];
        setIsValid(isValidRange);
    }, [dateRange]);

    const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newStartDate = new Date(e.target.value);
        onDateRangeChange(newStartDate, dateRange[1]);
    };

    const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newEndDate = new Date(e.target.value);
        onDateRangeChange(dateRange[0], newEndDate);
    };

    return (
        <div>
            <label className="dashboard-label">
                {label}
            </label>
            <div className="date-picker-container">
                <input
                    type="datetime-local"
                    step="1"
                    value={formatDateForInput(dateRange[0])}
                    onChange={handleStartDateChange}
                    className={`dashboard-input ${!isValid ? 'invalid' : ''}`}
                />
                <input
                    type="datetime-local"
                    step="1"
                    value={formatDateForInput(dateRange[1])}
                    onChange={handleEndDateChange}
                    className={`dashboard-input ${!isValid ? 'invalid' : ''}`}
                />
            </div>
            {!isValid && (
                <div className="date-range-error">
                    Invalid date range: End date must be greater than start date
                </div>
            )}
        </div>
    );
};

export default DateRangePicker; 