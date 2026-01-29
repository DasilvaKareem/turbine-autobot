import { NextResponse } from 'next/server';

const TURBINE_API = process.env.TURBINE_API_URL || 'https://api.turbinefi.com';

export async function GET() {
  try {
    const response = await fetch(`${TURBINE_API}/api/v1/health`, {
      next: { revalidate: 10 },
    });

    const data = await response.json();

    // Check if we got a valid response (even with auth errors, API is reachable)
    const isReachable = response.status === 200 || response.status === 401 || data.status === 'ok';

    return NextResponse.json({
      status: isReachable ? 'ok' : 'error',
      turbine: data.status === 'ok' ? data : { status: 'ok', note: 'API reachable' },
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    return NextResponse.json({
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
}
