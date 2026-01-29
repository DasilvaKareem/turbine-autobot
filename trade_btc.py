#!/usr/bin/env python3
"""
Place a trade on a Turbine Bitcoin prediction market.
Uses the Turbine client with gasless order submission.
"""

import os
import sys
import requests

# Add parent directory for turbine_client package
sys.path.insert(0, '/home/keneru/autobot')

from dotenv import load_dotenv
load_dotenv('/home/keneru/autobot/dashboard/.env.local')

from turbine_client import TurbineClient
from turbine_client.types import Outcome, Side

def main():
    # Get configuration from environment
    private_key = os.getenv('TURBINE_PRIVATE_KEY')
    api_key_id = os.getenv('TURBINE_API_KEY_ID')
    api_private_key = os.getenv('TURBINE_API_PRIVATE_KEY')

    if not private_key:
        print("Error: TURBINE_PRIVATE_KEY not set in .env.local")
        return
    if not api_key_id or not api_private_key:
        print("Error: TURBINE_API_KEY_ID and TURBINE_API_PRIVATE_KEY required")
        return

    chain_id = 137  # Polygon mainnet
    host = "https://api.turbinefi.com"

    print("=" * 60)
    print("TURBINE BTC MARKET TRADE")
    print("=" * 60)

    # Initialize client with signing capability AND API auth
    client = TurbineClient(
        host=host,
        chain_id=chain_id,
        private_key=private_key,
        api_key_id=api_key_id,
        api_private_key=api_private_key,
    )

    # Get the current active BTC quick market via REST API
    print("\nFetching active BTC quick market...")
    resp = requests.get(f"{host}/api/v1/quick-markets/BTC?chain_id={chain_id}")
    qm_data = resp.json()

    if not qm_data.get('active'):
        print("No active BTC quick market!")
        return

    quick_market = qm_data['quickMarket']
    market_id = quick_market['marketId']

    # Get market details to find settlement address
    markets = client.get_markets()
    market = next((m for m in markets if m.id == market_id), None)

    if not market:
        print(f"Could not find market {market_id} in markets list")
        return

    settlement_address = market.settlement_address
    strike_price = quick_market['startPrice'] / 1e8  # Convert from cents to dollars

    print(f"\nMarket Found:")
    print(f"  ID: {market_id[:30]}...")
    print(f"  Question: {market.question}")
    print(f"  Strike Price: ${strike_price:,.2f}")
    print(f"  Settlement: {settlement_address}")

    # Get orderbook
    print("\nFetching orderbook...")
    orderbook = client.get_orderbook(market_id)

    print(f"\nOrderbook:")
    if orderbook.bids:
        best_bid = orderbook.bids[0]
        print(f"  Best Bid (YES): ${best_bid.price / 1e6:.4f} ({best_bid.size / 1e6:.2f} contracts)")
    else:
        print("  No bids")

    if orderbook.asks:
        best_ask = orderbook.asks[0]
        print(f"  Best Ask (YES): ${best_ask.price / 1e6:.4f} ({best_ask.size / 1e6:.2f} contracts)")
    else:
        print("  No asks")
        print("No asks available - cannot place buy order")
        return

    # Check user wallet
    print("\n" + "=" * 60)
    print("YOUR POSITION")
    print("=" * 60)

    wallet_address = client._signer.address if client._signer else "Unknown"
    print(f"Wallet: {wallet_address}")

    # Trade parameters - buy $0.50 worth of YES tokens
    trade_amount_usdc = 0.50

    # Get best ask price (price to buy YES)
    buy_price = orderbook.asks[0].price / 1e6

    # Calculate size: cost = price * size, so size = cost / price
    size = int((trade_amount_usdc / buy_price) * 1e6)
    price = int(buy_price * 1e6)

    print(f"\nTrade Plan:")
    print(f"  Action: BUY YES")
    print(f"  Price: ${buy_price:.4f}")
    print(f"  Size: {size / 1e6:.4f} contracts")
    print(f"  Total Cost: ${trade_amount_usdc:.2f} USDC")
    print(f"  Potential Win: ${size / 1e6:.4f} USDC (if BTC > ${strike_price:,.2f})")

    # Execute trade
    print("\n" + "=" * 60)
    print("Executing trade...")

    print("\nCreating signed order...")
    try:
        signed_order = client.create_limit_buy(
            market_id=market_id,
            outcome=Outcome.YES,
            price=price,
            size=size,
            settlement_address=settlement_address,
        )
        print(f"Order hash: {signed_order.order_hash}")

        print("\nSubmitting order to Turbine...")
        result = client.post_order(signed_order)
        print(f"\n✓ Order submitted successfully!")
        print(f"Result: {result}")

    except Exception as e:
        print(f"\nError placing order: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
