import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';

const queryClient = new QueryClient();

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface RunInfo {
    run_id: string;
    name: string;
    algorithm: string;
    scenario: string;
    status: string;
    host: string;
    port: number;
    started_at: number;
    colonists: number;
    current_reward: number;
}

interface RunsResponse {
    runs: RunInfo[];
    total: number;
}

function RunCard({ run }: { run: RunInfo }) {
    const statusColors = {
        active: 'bg-green-500',
        stale: 'bg-yellow-500',
        pending: 'bg-blue-500',
        completed: 'bg-gray-500',
        failed: 'bg-red-500',
    };

    const statusColor = statusColors[run.status as keyof typeof statusColors] || 'bg-gray-500';

    return (
        <div className="bg-gray-800 rounded-lg shadow-xl p-6 border border-gray-700 hover:border-green-500 transition-colors">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="text-xl font-bold text-white">{run.name}</h3>
                    <p className="text-sm text-gray-400">{run.run_id}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold text-white ${statusColor}`}>
                    {run.status}
                </span>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <p className="text-gray-400">Algorithm</p>
                    <p className="text-white font-semibold">{run.algorithm}</p>
                </div>
                <div>
                    <p className="text-gray-400">Scenario</p>
                    <p className="text-white font-semibold">{run.scenario}</p>
                </div>
                <div>
                    <p className="text-gray-400">Colonists</p>
                    <p className="text-white font-semibold">{run.colonists}</p>
                </div>
                <div>
                    <p className="text-gray-400">Reward</p>
                    <p className="text-white font-semibold">{run.current_reward.toFixed(2)}</p>
                </div>
            </div>

            <div className="mt-4 text-xs text-gray-500">
                <p>
                    {run.host}:{run.port} • Started {new Date(run.started_at * 1000).toLocaleString()}
                </p>
            </div>
        </div>
    );
}

function Dashboard() {
    const { data, isLoading, error, refetch } = useQuery<RunsResponse>({
        queryKey: ['runs'],
        queryFn: async () => {
            const response = await fetch(`${API_URL}/api/v1/runs`);
            if (!response.ok) {
                throw new Error('Failed to fetch runs');
            }
            return response.json();
        },
        refetchInterval: 2000, // Refresh every 2 seconds
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-xl text-gray-400">Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-xl text-red-400">Error: {(error as Error).message}</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900">
            <header className="bg-gray-800 shadow-lg border-b border-gray-700">
                <div className="max-w-7xl mx-auto py-6 px-4">
                    <div className="flex justify-between items-center">
                        <h1 className="text-3xl font-bold text-green-400">RimWorld ML Dashboard</h1>
                        <div className="text-sm text-gray-400">
                            {data?.total || 0} Active Run{data?.total !== 1 ? 's' : ''}
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto py-6 px-4">
                {data && data.runs.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {data.runs.map((run) => (
                            <RunCard key={run.run_id} run={run} />
                        ))}
                    </div>
                ) : (
                    <div className="bg-gray-800 rounded-lg shadow-xl p-12 text-center">
                        <svg
                            className="mx-auto h-16 w-16 text-gray-600 mb-4"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                            />
                        </svg>
                        <h3 className="text-xl font-semibold text-gray-300 mb-2">No Training Runs</h3>
                        <p className="text-gray-500 mb-4">
                            No active training runs detected. Start a RimWorld training session to begin monitoring.
                        </p>
                        <button
                            onClick={() => refetch()}
                            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                        >
                            Refresh
                        </button>
                    </div>
                )}

                <div className="mt-8 bg-gray-800 rounded-lg shadow-xl p-6">
                    <h2 className="text-xl font-semibold text-white mb-4">Quick Stats</h2>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-gray-700 rounded-lg p-4">
                            <p className="text-sm text-gray-400 mb-1">Total Runs</p>
                            <p className="text-2xl font-bold text-white">{data?.total || 0}</p>
                        </div>
                        <div className="bg-gray-700 rounded-lg p-4">
                            <p className="text-sm text-gray-400 mb-1">Active</p>
                            <p className="text-2xl font-bold text-green-400">
                                {data?.runs.filter((r) => r.status === 'active').length || 0}
                            </p>
                        </div>
                        <div className="bg-gray-700 rounded-lg p-4">
                            <p className="text-sm text-gray-400 mb-1">Total Colonists</p>
                            <p className="text-2xl font-bold text-white">
                                {data?.runs.reduce((sum, r) => sum + r.colonists, 0) || 0}
                            </p>
                        </div>
                        <div className="bg-gray-700 rounded-lg p-4">
                            <p className="text-sm text-gray-400 mb-1">Avg Reward</p>
                            <p className="text-2xl font-bold text-white">
                                {data && data.runs.length > 0
                                    ? (
                                          data.runs.reduce((sum, r) => sum + r.current_reward, 0) /
                                          data.runs.length
                                      ).toFixed(2)
                                    : '0.00'}
                            </p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <Dashboard />
        </QueryClientProvider>
    );
}

export default App;
