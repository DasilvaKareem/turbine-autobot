'use client';

import { useEffect, useState } from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  change?: string;
  positive?: boolean;
  icon?: string;
}

function StatCard({ label, value, change, positive, icon }: StatCardProps) {
  return (
    <div className="bg-zinc-800 rounded-lg p-4 border border-zinc-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-zinc-400 text-sm">{label}</span>
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
      {change && (
        <div
          className={`text-sm mt-1 ${
            positive ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {change}
        </div>
      )}
    </div>
  );
}

interface Stats {
  totalValue: number;
  positions: number;
  openOrders: number;
  pnl: number;
  pnlPercent: number;
  wallet?: string;
}

export default function StatsPanel() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/stats?chain_id=137');
        const data = await response.json();

        if (data.error && !data.totalValue) {
          setError(data.error);
        } else {
          setStats({
            totalValue: data.totalValue || 0,
            positions: data.positions || 0,
            openOrders: data.openOrders || 0,
            pnl: data.pnl || 0,
            pnlPercent: data.pnlPercent || 0,
            wallet: data.wallet,
          });
          setError(null);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 15000); // Refresh every 15 seconds

    return () => clearInterval(interval);
  }, []);

  const displayStats = stats || {
    totalValue: 0,
    positions: 0,
    openOrders: 0,
    pnl: 0,
    pnlPercent: 0,
  };

  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="text-2xl">📈</span>
          Bot Statistics
        </h2>
        {stats?.wallet && (
          <span className="text-xs text-zinc-500 font-mono">
            {stats.wallet.slice(0, 6)}...{stats.wallet.slice(-4)}
          </span>
        )}
      </div>

      {loading ? (
        <div className="text-zinc-500 text-center py-4">Loading stats...</div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Portfolio Value"
              value={`$${displayStats.totalValue.toFixed(2)}`}
              icon="💰"
            />
            <StatCard
              label="Open Positions"
              value={displayStats.positions}
              icon="📊"
            />
            <StatCard
              label="Open Orders"
              value={displayStats.openOrders}
              icon="📝"
            />
            <StatCard
              label="Total P&L"
              value={`$${displayStats.pnl.toFixed(2)}`}
              change={`${displayStats.pnlPercent >= 0 ? '+' : ''}${displayStats.pnlPercent.toFixed(2)}%`}
              positive={displayStats.pnlPercent >= 0}
              icon={displayStats.pnl >= 0 ? '📈' : '📉'}
            />
          </div>

          {error && (
            <div className="mt-4 p-3 bg-yellow-900/30 rounded-lg border border-yellow-800">
              <p className="text-yellow-400 text-sm">
                ⚠️ Could not fetch some data: {error}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
