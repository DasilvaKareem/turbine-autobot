#!/usr/bin/env python3
"""
Test script for the Turbine NautilusTrader adapter.

This script tests the basic functionality of the Turbine adapter
by loading instruments and connecting to the WebSocket.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'nautilus_trader'))

from dotenv import load_dotenv
load_dotenv()


async def test_turbine_client():
    """Test the Turbine Python client directly."""
    print("=" * 60)
    print("Testing Turbine Python Client")
    print("=" * 60)

    from turbine_client import TurbineClient

    # Create a read-only client (no auth needed for public endpoints)
    client = TurbineClient(
        host="https://api.turbinefi.com",
        chain_id=84532,  # Base Sepolia
    )

    try:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        health = client.get_health()
        print(f"   Health: {health}")

        # Test markets endpoint
        print("\n2. Loading markets...")
        markets = client.get_markets(chain_id=84532)
        print(f"   Found {len(markets)} markets")

        if markets:
            # Show first few markets
            print("\n   Sample markets:")
            for market in markets[:3]:
                print(f"   - {market.id[:20]}... : {market.question[:50]}...")

            # Test orderbook for first market
            print("\n3. Testing orderbook...")
            first_market = markets[0]
            orderbook = client.get_orderbook(first_market.id)
            print(f"   Market: {first_market.id[:20]}...")
            print(f"   Bids: {len(orderbook.bids)} levels")
            print(f"   Asks: {len(orderbook.asks)} levels")

            if orderbook.bids:
                best_bid = orderbook.bids[0]
                print(f"   Best bid: {best_bid.price / 1_000_000:.4f} @ {best_bid.size / 1_000_000:.2f}")

            if orderbook.asks:
                best_ask = orderbook.asks[0]
                print(f"   Best ask: {best_ask.price / 1_000_000:.4f} @ {best_ask.size / 1_000_000:.2f}")

        print("\n" + "=" * 60)
        print("Turbine Python Client: OK")
        print("=" * 60)

    except Exception as e:
        print(f"\n   Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


async def test_turbine_websocket():
    """Test the Turbine WebSocket client."""
    print("\n" + "=" * 60)
    print("Testing Turbine WebSocket Client")
    print("=" * 60)

    from turbine_client import TurbineClient, TurbineWSClient

    # Get a market to subscribe to
    client = TurbineClient(
        host="https://api.turbinefi.com",
        chain_id=84532,
    )

    try:
        markets = client.get_markets(chain_id=84532)
        if not markets:
            print("   No markets found")
            return

        market_id = markets[0].id
        print(f"\n   Subscribing to market: {market_id[:30]}...")

        # Connect to WebSocket
        ws_client = TurbineWSClient("https://api.turbinefi.com")

        async with ws_client.connect() as stream:
            await stream.subscribe(market_id)
            print("   Subscribed! Waiting for messages...")

            # Wait for a few messages
            message_count = 0
            timeout = 10  # seconds

            try:
                async for message in asyncio.timeout_iterator(stream, timeout=timeout):
                    message_count += 1
                    print(f"   Message {message_count}: type={message.type}")

                    if message_count >= 5:
                        break

            except asyncio.TimeoutError:
                print(f"   Received {message_count} messages in {timeout}s")

        print("\n" + "=" * 60)
        print("Turbine WebSocket Client: OK")
        print("=" * 60)

    except Exception as e:
        print(f"\n   Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


async def timeout_iterator(stream, timeout):
    """Iterate with a timeout."""
    import asyncio

    async def iterate():
        async for item in stream:
            yield item

    iterator = iterate()
    while True:
        try:
            item = await asyncio.wait_for(iterator.__anext__(), timeout=timeout)
            yield item
        except StopAsyncIteration:
            break


def test_adapter_imports():
    """Test that the adapter can be imported."""
    print("\n" + "=" * 60)
    print("Testing Adapter Imports")
    print("=" * 60)

    try:
        print("\n1. Importing constants...")
        from nautilus_trader.adapters.turbine import (
            TURBINE,
            TURBINE_VENUE,
            TURBINE_MAX_PRICE,
            TURBINE_MIN_PRICE,
        )
        print(f"   TURBINE = {TURBINE}")
        print(f"   TURBINE_VENUE = {TURBINE_VENUE}")
        print(f"   Price range: {TURBINE_MIN_PRICE} - {TURBINE_MAX_PRICE}")

        print("\n2. Importing configs...")
        from nautilus_trader.adapters.turbine import (
            TurbineDataClientConfig,
            TurbineExecClientConfig,
        )
        print(f"   TurbineDataClientConfig: OK")
        print(f"   TurbineExecClientConfig: OK")

        print("\n3. Importing factories...")
        from nautilus_trader.adapters.turbine import (
            TurbineLiveDataClientFactory,
            TurbineLiveExecClientFactory,
        )
        print(f"   TurbineLiveDataClientFactory: OK")
        print(f"   TurbineLiveExecClientFactory: OK")

        print("\n4. Importing utilities...")
        from nautilus_trader.adapters.turbine import (
            get_turbine_instrument_id,
            get_turbine_market_id,
            get_turbine_outcome,
        )
        print(f"   Symbol utilities: OK")

        # Test symbol utilities
        print("\n5. Testing symbol utilities...")
        test_market_id = "0x1234567890abcdef"
        inst_id = get_turbine_instrument_id(test_market_id, "YES")
        print(f"   Instrument ID: {inst_id}")

        extracted_market = get_turbine_market_id(inst_id)
        extracted_outcome = get_turbine_outcome(inst_id)
        print(f"   Extracted market: {extracted_market}")
        print(f"   Extracted outcome: {extracted_outcome}")

        assert extracted_market == test_market_id
        assert extracted_outcome == "YES"
        print("   Round-trip: OK")

        print("\n" + "=" * 60)
        print("Adapter Imports: OK")
        print("=" * 60)

    except Exception as e:
        print(f"\n   Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("\n")
    print("*" * 60)
    print("  TURBINE ADAPTER TEST SUITE")
    print("*" * 60)

    # Test imports first
    test_adapter_imports()

    # Test Turbine client
    await test_turbine_client()

    # Test WebSocket (optional, may timeout if no data)
    # await test_turbine_websocket()

    print("\n")
    print("*" * 60)
    print("  ALL TESTS COMPLETED")
    print("*" * 60)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
