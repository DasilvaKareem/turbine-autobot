'use client';

import { useEffect, useState } from 'react';
import MarketCard from './MarketCard';

interface Market {
  id: string;
  question: string;
  description?: string;
  category?: string;
  expirationTime?: number;
  resolved?: boolean;
  winningOutcome?: number | null;
}

export default function MarketsPanel() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMarkets = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/markets?chain_id=137'); // Polygon mainnet
        const data = await response.json();

        if (data.error) {
          setError(data.error);
        } else {
          setMarkets(data.markets || []);
          setError(null);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMarkets();
    const interval = setInterval(fetchMarkets, 60000); // Refresh every minute

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 h-full flex flex-col min-h-0 overflow-hidden">
      <div className="flex-shrink-0 px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="text-2xl">📊</span>
          Markets
        </h2>
        <span className="text-sm text-zinc-500">
          {markets.length} available
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 min-h-0">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="text-zinc-500">Loading markets...</div>
          </div>
        )}

        {error && (
          <div className="bg-red-900/30 border border-red-800 rounded-lg p-4 text-red-300">
            <p className="font-medium">Error loading markets</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {!loading && !error && markets.length === 0 && (
          <div className="text-center py-8 text-zinc-500">
            <p className="text-lg mb-2">No markets available</p>
            <p className="text-sm">Markets will appear here when they are created on Turbine</p>
          </div>
        )}

        <div className="space-y-3">
          {markets.map((market) => (
            <MarketCard key={market.id} market={market} />
          ))}
        </div>
      </div>
    </div>
  );
}
