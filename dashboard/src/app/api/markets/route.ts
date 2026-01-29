import { NextRequest, NextResponse } from 'next/server';

const TURBINE_API = process.env.TURBINE_API_URL || 'https://api.turbinefi.com';

export async function GET(request: NextRequest) {
  try {
    const chainId = request.nextUrl.searchParams.get('chain_id') || '137'; // Default to Polygon mainnet

    const response = await fetch(`${TURBINE_API}/api/v1/markets?chain_id=${chainId}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      next: { revalidate: 30 }, // Cache for 30 seconds
    });

    if (!response.ok) {
      throw new Error(`Turbine API error: ${response.status}`);
    }

    const data = await response.json();

    return NextResponse.json({
      markets: data.markets || [],
      count: data.count || 0,
    });
  } catch (error: any) {
    console.error('Markets API error:', error);
    return NextResponse.json(
      { error: error.message, markets: [], count: 0 },
      { status: 500 }
    );
  }
}
