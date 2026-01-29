import { NextRequest, NextResponse } from 'next/server';

const TURBINE_API = process.env.TURBINE_API_URL || 'https://api.turbinefi.com';
const WALLET_ADDRESS = '0xDf746ec029aeFa783Ee001f9A594600b05786f31';

export async function GET(request: NextRequest) {
  try {
    const chainId = request.nextUrl.searchParams.get('chain_id') || '137';

    // Fetch user orders from Turbine
    const ordersResponse = await fetch(
      `${TURBINE_API}/api/v1/users/${WALLET_ADDRESS}/orders?chain_id=${chainId}`,
      { next: { revalidate: 10 } }
    );

    let orders: any[] = [];
    let openOrders = 0;

    if (ordersResponse.ok) {
      const ordersData = await ordersResponse.json();
      orders = ordersData.orders || [];
      // Count open orders (status could be 'open', 'pending', or empty for active)
      openOrders = orders.filter((o: any) =>
        !o.status || o.status === 'open' || o.status === 'pending' || o.status === 'accepted'
      ).length;
    }

    // Fetch markets to check for positions
    const marketsResponse = await fetch(
      `${TURBINE_API}/api/v1/markets?chain_id=${chainId}`,
      { next: { revalidate: 30 } }
    );

    let positions = 0;
    let totalValue = 1.0; // Starting with $1 USDC

    if (marketsResponse.ok) {
      const marketsData = await marketsResponse.json();
      const markets = marketsData.markets || [];

      // Check a few markets for positions (this is simplified)
      // In a real implementation, you'd track positions from filled orders
      for (const market of markets.slice(0, 10)) {
        try {
          const posResponse = await fetch(
            `${TURBINE_API}/api/v1/positions/${market.id}?user=${WALLET_ADDRESS}`,
            { next: { revalidate: 30 } }
          );
          if (posResponse.ok) {
            const posData = await posResponse.json();
            if (posData.positions && posData.positions.length > 0) {
              positions += posData.positions.length;
            }
          }
        } catch {
          // Skip if position fetch fails
        }
      }
    }

    // Calculate P&L (simplified - would need trade history for accurate calculation)
    const pnl = 0; // No realized P&L yet
    const pnlPercent = 0;

    return NextResponse.json({
      totalValue,
      positions,
      openOrders,
      pnl,
      pnlPercent,
      wallet: WALLET_ADDRESS,
      fetchedAt: new Date().toISOString(),
    });
  } catch (error: any) {
    console.error('Stats API error:', error);
    return NextResponse.json(
      {
        error: error.message,
        totalValue: 1.0,
        positions: 0,
        openOrders: 0,
        pnl: 0,
        pnlPercent: 0,
      },
      { status: 500 }
    );
  }
}
