'use client';

import { useEffect, useState } from 'react';

interface HealthStatus {
  status: string;
  turbine?: {
    status: string;
    service?: string;
  };
  timestamp: string;
  error?: string;
}

export default function StatusBar() {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('/api/health');
        const data = await response.json();
        setHealth(data);
      } catch (error) {
        setHealth({
          status: 'error',
          error: 'Failed to connect',
          timestamp: new Date().toISOString(),
        });
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const isOnline = health?.status === 'ok';

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-zinc-900 border-b border-zinc-800">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="text-2xl">⚡</span>
          Turbine Trading Dashboard
        </h1>
        <span className="text-xs text-zinc-500">NautilusTrader</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`}
          />
          <span className={`text-sm ${isOnline ? 'text-green-400' : 'text-red-400'}`}>
            {isOnline ? 'Connected' : 'Disconnected'}
          </span>
        </div>

        {health?.timestamp && (
          <span className="text-xs text-zinc-600">
            Last update: {new Date(health.timestamp).toLocaleTimeString()}
          </span>
        )}
      </div>
    </div>
  );
}
