'use client';

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

interface StatsPanelProps {
  stats?: {
    totalValue?: number;
    positions?: number;
    openOrders?: number;
    pnl?: number;
    pnlPercent?: number;
  };
}

export default function StatsPanel({ stats }: StatsPanelProps) {
  // Default/demo stats when bot is not running
  const displayStats = {
    totalValue: stats?.totalValue ?? 0,
    positions: stats?.positions ?? 0,
    openOrders: stats?.openOrders ?? 0,
    pnl: stats?.pnl ?? 0,
    pnlPercent: stats?.pnlPercent ?? 0,
  };

  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
      <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <span className="text-2xl">📈</span>
        Bot Statistics
      </h2>

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
          icon="📉"
        />
      </div>

      {!stats && (
        <div className="mt-4 p-3 bg-zinc-800 rounded-lg border border-zinc-700">
          <p className="text-zinc-400 text-sm">
            💡 Bot statistics will appear here when the trading bot is running.
            Start the bot with: <code className="bg-zinc-700 px-1 rounded">python examples/turbine_market_maker.py</code>
          </p>
        </div>
      )}
    </div>
  );
}
