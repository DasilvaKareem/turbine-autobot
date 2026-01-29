'use client';

interface Market {
  id: string;
  question: string;
  description?: string;
  category?: string;
  expirationTime?: number;
  resolved?: boolean;
  winningOutcome?: number | null;
}

interface MarketCardProps {
  market: Market;
}

export default function MarketCard({ market }: MarketCardProps) {
  const formatDate = (timestamp: number) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-zinc-800 rounded-lg p-4 border border-zinc-700 hover:border-zinc-600 transition-colors">
      <div className="flex items-start justify-between gap-2 mb-2">
        <span
          className={`px-2 py-0.5 text-xs font-medium rounded ${
            market.resolved
              ? 'bg-green-900 text-green-300'
              : 'bg-blue-900 text-blue-300'
          }`}
        >
          {market.resolved ? 'Resolved' : 'Active'}
        </span>
        {market.category && (
          <span className="px-2 py-0.5 text-xs bg-zinc-700 text-zinc-300 rounded">
            {market.category}
          </span>
        )}
      </div>

      <h3 className="text-white font-medium mb-2 line-clamp-2">
        {market.question || 'Untitled Market'}
      </h3>

      {market.description && (
        <p className="text-zinc-400 text-sm mb-3 line-clamp-2">
          {market.description}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-zinc-500">
        <span>Expires: {formatDate(market.expirationTime || 0)}</span>
        <span className="font-mono">{market.id.slice(0, 10)}...</span>
      </div>

      {market.resolved && market.winningOutcome !== null && (
        <div className="mt-3 pt-3 border-t border-zinc-700">
          <span className="text-sm">
            Winner:{' '}
            <span className={market.winningOutcome === 0 ? 'text-green-400' : 'text-red-400'}>
              {market.winningOutcome === 0 ? 'YES' : 'NO'}
            </span>
          </span>
        </div>
      )}
    </div>
  );
}
