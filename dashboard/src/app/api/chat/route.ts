import { NextRequest, NextResponse } from 'next/server';
import Groq from 'groq-sdk';

// Lazy initialization to avoid build-time errors
let groqClient: Groq | null = null;

function getGroqClient(): Groq {
  if (!groqClient) {
    const apiKey = process.env.GROQ_API_KEY;
    if (!apiKey) {
      throw new Error('GROQ_API_KEY environment variable is not set');
    }
    groqClient = new Groq({ apiKey });
  }
  return groqClient;
}

const TURBINE_API = process.env.TURBINE_API_URL || 'https://api.turbinefi.com';

// Fetch live market data from Turbine
async function fetchMarketData() {
  try {
    const response = await fetch(`${TURBINE_API}/api/v1/markets?chain_id=137`, {
      next: { revalidate: 60 },
    });
    const data = await response.json();
    const markets = data.markets || [];

    // Get summary stats
    const totalMarkets = markets.length;
    const activeMarkets = markets.filter((m: any) => !m.resolved).length;
    const resolvedMarkets = markets.filter((m: any) => m.resolved).length;

    // Get some sample markets (most recent)
    const sampleMarkets = markets.slice(0, 10).map((m: any) => ({
      question: m.question,
      category: m.category,
      resolved: m.resolved,
      expirationTime: m.expirationTime ? new Date(m.expirationTime * 1000).toISOString() : null,
    }));

    return {
      totalMarkets,
      activeMarkets,
      resolvedMarkets,
      sampleMarkets,
      fetchedAt: new Date().toISOString(),
    };
  } catch (error) {
    return { error: 'Failed to fetch market data' };
  }
}

// Fetch current BTC price
async function fetchBTCPrice() {
  try {
    const response = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true', {
      next: { revalidate: 30 },
    });
    const data = await response.json();
    return {
      price: data.bitcoin.usd,
      change24h: data.bitcoin.usd_24h_change?.toFixed(2),
    };
  } catch (error) {
    return { error: 'Failed to fetch BTC price' };
  }
}

// System prompt with context about the trading bot
const SYSTEM_PROMPT = `You are an AI assistant for a Turbine prediction market trading bot built with NautilusTrader.

About the system:
- Turbine is a Bitcoin prediction market platform on Polygon (mainnet)
- NautilusTrader is a high-performance algorithmic trading framework in Rust/Python
- The bot trades YES/NO outcome tokens on prediction markets
- Prices range from 0.001 to 0.999 (probability of outcome)
- All amounts are in USDC with 6 decimal precision
- Markets are typically 15-minute BTC price prediction markets

You can help users understand:
- Current market conditions and prices
- Trading strategy explanations (market making, arbitrage, etc.)
- How prediction markets work
- Risk management concepts
- Technical analysis of market opportunities

When given live data, analyze it and provide actionable insights. Be concise but thorough.
Format your responses with markdown for better readability (use **bold**, *italic*, \`code\`, lists, etc.).`;

export async function POST(request: NextRequest) {
  try {
    const { messages, tradingContext } = await request.json();

    // Fetch live data in parallel
    const [marketData, btcPrice] = await Promise.all([
      fetchMarketData(),
      fetchBTCPrice(),
    ]);

    // Build context with live data
    const liveContext = {
      btcPrice,
      marketData,
      tradingContext,
      currentTime: new Date().toISOString(),
    };

    // Build system message with live context
    const systemMessage = `${SYSTEM_PROMPT}

## LIVE DATA (as of ${new Date().toLocaleString()}):

### Bitcoin Price:
${btcPrice.error ? 'Unable to fetch' : `$${btcPrice.price?.toLocaleString()} (${btcPrice.change24h}% 24h)`}

### Turbine Markets (Polygon):
${marketData.error ? 'Unable to fetch' : `
- Total Markets: ${marketData.totalMarkets}
- Active Markets: ${marketData.activeMarkets}
- Resolved Markets: ${marketData.resolvedMarkets}

### Sample Active Markets:
${marketData.sampleMarkets?.slice(0, 5).map((m: any, i: number) =>
  `${i + 1}. "${m.question}" ${m.resolved ? '(RESOLVED)' : '(ACTIVE)'}`
).join('\n') || 'No markets available'}
`}

${tradingContext ? `### Trading Context:\n${JSON.stringify(tradingContext, null, 2)}` : ''}

Use this live data to provide accurate, up-to-date responses.`;

    const groq = getGroqClient();
    const completion = await groq.chat.completions.create({
      model: 'llama-3.3-70b-versatile',
      messages: [
        { role: 'system', content: systemMessage },
        ...messages,
      ],
      temperature: 0.7,
      max_tokens: 1500,
    });

    return NextResponse.json({
      message: completion.choices[0]?.message?.content || 'No response generated',
      context: {
        btcPrice: btcPrice.error ? null : btcPrice,
        marketsCount: marketData.error ? null : marketData.totalMarkets,
      },
    });
  } catch (error: any) {
    console.error('Groq API error:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to get AI response' },
      { status: 500 }
    );
  }
}
