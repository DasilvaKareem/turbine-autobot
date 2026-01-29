import ChatPanel from '@/components/ChatPanel';
import MarketsPanel from '@/components/MarketsPanel';
import StatsPanel from '@/components/StatsPanel';
import StatusBar from '@/components/StatusBar';

export default function Home() {
  return (
    <div className="h-screen flex flex-col bg-black text-white overflow-hidden">
      <StatusBar />

      <main className="flex-1 flex flex-col min-h-0 p-4 pb-12">
        {/* Stats Row */}
        <div className="flex-shrink-0 mb-4">
          <StatsPanel />
        </div>

        {/* Main Content Grid */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
          {/* Markets Panel */}
          <MarketsPanel />

          {/* Chat Panel */}
          <ChatPanel />
        </div>
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-zinc-900 border-t border-zinc-800 px-4 py-2 z-10">
        <div className="container mx-auto flex items-center justify-between text-xs text-zinc-500">
          <span>Turbine Trading Bot Dashboard • Polygon Mainnet</span>
          <div className="flex items-center gap-4">
            <a
              href="https://beta.turbinefi.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white transition-colors"
            >
              Turbine Web App
            </a>
            <a
              href="https://github.com/nautechsystems/nautilus_trader"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white transition-colors"
            >
              NautilusTrader
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
