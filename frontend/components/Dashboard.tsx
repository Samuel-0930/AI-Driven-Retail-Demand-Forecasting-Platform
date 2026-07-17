"use client";

import React, { useState } from 'react';
import { api, ApiError, PredictionResponse } from '../lib/api';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ComposedChart } from 'recharts';
import { Calendar, ShoppingBag, Store, TrendingUp, Activity } from 'lucide-react';

export default function Dashboard() {
    const [storeId, setStoreId] = useState('1');
    const [productId, setProductId] = useState('1');
    const [startDate, setStartDate] = useState('2025-01-01');
    const [endDate, setEndDate] = useState('2025-01-30');
    const [isPromo, setIsPromo] = useState(false);
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<PredictionResponse | null>(null);
    const [error, setError] = useState('');
    const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

    const chartData = data?.predictions.map((point) => ({
        ...point,
        confidenceInterval: [
            Math.min(point.lower_bound, point.upper_bound),
            Math.max(point.lower_bound, point.upper_bound),
        ] as [number, number],
    }));

    const validateForm = () => {
        const errors: Record<string, string> = {};
        const parsedStoreId = Number(storeId);
        const parsedProductId = Number(productId);

        if (!Number.isInteger(parsedStoreId) || parsedStoreId <= 0) errors.storeId = 'Enter a positive whole-number store ID.';
        if (!Number.isInteger(parsedProductId) || parsedProductId <= 0) errors.productId = 'Enter a positive whole-number product ID.';
        if (!startDate) errors.startDate = 'Choose a start date.';
        if (!endDate) errors.endDate = 'Choose an end date.';
        if (startDate && endDate) {
            const duration = (Date.parse(`${endDate}T00:00:00Z`) - Date.parse(`${startDate}T00:00:00Z`)) / 86_400_000 + 1;
            if (duration < 1) errors.endDate = 'End date must be on or after start date.';
            if (duration > 90) errors.endDate = 'Forecasts are limited to 90 days.';
        }

        setFieldErrors(errors);
        return Object.keys(errors).length === 0 ? { parsedStoreId, parsedProductId } : null;
    };

    const handlePredict = async (e: React.FormEvent) => {
        e.preventDefault();
        const validated = validateForm();
        if (!validated) return;
        setLoading(true);
        setError('');
        try {
            const result = await api.predict({
                store_id: validated.parsedStoreId,
                product_id: validated.parsedProductId,
                start_date: startDate,
                end_date: endDate,
                is_promo: isPromo,
            });
            setData(result);
        } catch (err) {
            if (err instanceof ApiError && err.status === 404) setError('No trained model exists for this store and product yet.');
            else if (err instanceof ApiError && err.status === 422) setError('Check the forecasting inputs and try again.');
            else setError('The prediction service is temporarily unavailable. Please try again.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
            {/* Header */}
            <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="bg-blue-600 p-2 rounded-lg">
                            <TrendingUp className="h-6 w-6 text-white" />
                        </div>
                        <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                            Demand Sense
                        </h1>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-slate-500">
                        <span className="flex items-center"><Activity className="w-4 h-4 mr-1" /> v1.0.0</span>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* Sidebar / Controls */}
                    <div className="lg:col-span-3 space-y-6">
                        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center">
                                <Calendar className="w-5 h-5 mr-2 text-blue-600" />
                                Configuration
                            </h2>
                            <form onSubmit={handlePredict} className="space-y-4">
                                <div>
                                    <label htmlFor="store-id" className="block text-sm font-medium text-slate-700 mb-1">Store ID</label>
                                    <div className="relative">
                                        <Store className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                        <input
                                            id="store-id"
                                            type="number"
                                            min="1"
                                            step="1"
                                            value={storeId}
                                            onChange={(e) => setStoreId(e.target.value)}
                                            aria-invalid={Boolean(fieldErrors.storeId)}
                                            aria-describedby={fieldErrors.storeId ? 'store-id-error' : undefined}
                                            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                        />
                                    </div>
                                    {fieldErrors.storeId && <p id="store-id-error" className="mt-1 text-sm text-red-600">{fieldErrors.storeId}</p>}
                                </div>

                                <div>
                                    <label htmlFor="product-id" className="block text-sm font-medium text-slate-700 mb-1">Product ID</label>
                                    <div className="relative">
                                        <ShoppingBag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                        <input
                                            id="product-id"
                                            type="number"
                                            min="1"
                                            step="1"
                                            value={productId}
                                            onChange={(e) => setProductId(e.target.value)}
                                            aria-invalid={Boolean(fieldErrors.productId)}
                                            aria-describedby={fieldErrors.productId ? 'product-id-error' : undefined}
                                            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                        />
                                    </div>
                                    {fieldErrors.productId && <p id="product-id-error" className="mt-1 text-sm text-red-600">{fieldErrors.productId}</p>}
                                </div>

                                <div>
                                    <label htmlFor="start-date" className="block text-sm font-medium text-slate-700 mb-1">Start Date</label>
                                    <input
                                        id="start-date"
                                        type="date"
                                        value={startDate}
                                        onChange={(e) => setStartDate(e.target.value)}
                                        required
                                        aria-invalid={Boolean(fieldErrors.startDate)}
                                        aria-describedby={fieldErrors.startDate ? 'start-date-error' : undefined}
                                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                    />
                                    {fieldErrors.startDate && <p id="start-date-error" className="mt-1 text-sm text-red-600">{fieldErrors.startDate}</p>}
                                </div>

                                <div>
                                    <label htmlFor="end-date" className="block text-sm font-medium text-slate-700 mb-1">End Date</label>
                                    <input
                                        id="end-date"
                                        type="date"
                                        value={endDate}
                                        onChange={(e) => setEndDate(e.target.value)}
                                        min={startDate}
                                        required
                                        aria-invalid={Boolean(fieldErrors.endDate)}
                                        aria-describedby={fieldErrors.endDate ? 'end-date-error' : undefined}
                                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                                    />
                                    {fieldErrors.endDate && <p id="end-date-error" className="mt-1 text-sm text-red-600">{fieldErrors.endDate}</p>}
                                </div>

                                <div className="flex items-center space-x-2 pt-2">
                                    <input
                                        type="checkbox"
                                        id="promo"
                                        checked={isPromo}
                                        onChange={(e) => setIsPromo(e.target.checked)}
                                        className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                                    />
                                    <label htmlFor="promo" className="text-sm font-medium text-slate-700">Apply Promotion</label>
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center"
                                >
                                    {loading ? (
                                        <>
                                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        <span className="ml-2">Generating forecast…</span>
                                        </>
                                    ) : (
                                        "Generate Forecast"
                                    )}
                                </button>
                            </form>
                        </div>
                    </div>

                    {/* Main Content / Chart */}
                    <div className="lg:col-span-9 space-y-6">
                        {error && (
                            <div role="alert" className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
                                <div className="flex">
                                    <div className="flex-shrink-0">
                                        <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                        </svg>
                                    </div>
                                    <div className="ml-3">
                                        <p className="text-sm text-red-700">{error}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 min-h-[500px]">
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-xl font-bold text-slate-800">Demand Forecast</h2>
                                {data && (
                                    <div className="flex space-x-4 text-sm">
                                        <div className="flex items-center">
                                            <span className="w-3 h-3 rounded-full bg-blue-500 mr-2"></span>
                                            <span className="text-slate-600">Forecast</span>
                                        </div>
                                        <div className="flex items-center">
                                            <span className="w-3 h-3 rounded-full bg-blue-100 mr-2"></span>
                                            <span className="text-slate-600">Confidence Interval</span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {chartData && chartData.length > 0 ? (
                                <div className="h-[400px] w-full">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                            <defs>
                                                <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1} />
                                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                            <XAxis
                                                dataKey="date"
                                                stroke="#64748b"
                                                fontSize={12}
                                                tickLine={false}
                                                axisLine={false}
                                                tickFormatter={(value) => value}
                                            />
                                            <YAxis
                                                stroke="#64748b"
                                                fontSize={12}
                                                tickLine={false}
                                                axisLine={false}
                                                tickFormatter={(value) => `${value}`}
                                            />
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                                itemStyle={{ color: '#1e293b' }}
                                                labelStyle={{ color: '#64748b', marginBottom: '0.5rem' }}
                                                formatter={(value, name) => {
                                                    if (Array.isArray(value)) return [`${value[0].toFixed(0)}–${value[1].toFixed(0)}`, '95% prediction interval'];
                                                    return [Number(value).toFixed(0), name === 'forecast' ? 'Forecast' : String(name)];
                                                }}
                                                labelFormatter={(label) => label}
                                            />
                                            <Area
                                                type="monotone"
                                                dataKey="confidenceInterval"
                                                stroke="none"
                                                fill="#3b82f6"
                                                fillOpacity={0.14}
                                                isAnimationActive={false}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey="forecast"
                                                stroke="#3b82f6"
                                                strokeWidth={3}
                                                dot={{ r: 4, fill: '#3b82f6', strokeWidth: 2, stroke: '#fff' }}
                                                activeDot={{ r: 6, strokeWidth: 0 }}
                                            />
                                        </ComposedChart>
                                    </ResponsiveContainer>
                                </div>
                            ) : (
                                <div className="h-[400px] w-full flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-lg">
                                    <Activity className="w-12 h-12 mb-4 opacity-50" />
                                    <p className="text-lg font-medium">Ready to forecast</p>
                                    <p className="text-sm">Configure parameters and click Generate</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
