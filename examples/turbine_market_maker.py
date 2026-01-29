#!/usr/bin/env python3
"""
Example Turbine Market Maker Bot using NautilusTrader.

This script demonstrates how to create a simple market making strategy
for Turbine's Bitcoin prediction markets using NautilusTrader.

Environment Variables Required:
    TURBINE_PRIVATE_KEY: Your Ethereum wallet private key
    TURBINE_API_KEY_ID: Your Turbine API key ID
    TURBINE_API_PRIVATE_KEY: Your Turbine API Ed25519 private key

Usage:
    source venv/bin/activate
    python examples/turbine_market_maker.py
"""

import os
import sys
from decimal import Decimal

from dotenv import load_dotenv
load_dotenv('/home/keneru/autobot/dashboard/.env.local')

# Import NautilusTrader and Turbine adapter
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.adapters.turbine import (
    TURBINE_VENUE,
    TurbineDataClientConfig,
    TurbineExecClientConfig,
    TurbineLiveDataClientFactory,
    TurbineLiveExecClientFactory,
    get_turbine_instrument_id,
)
print("✓ NautilusTrader and Turbine adapter imported successfully")

from nautilus_trader.cache.cache import Cache
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveDataEngineConfig
from nautilus_trader.config import LiveExecEngineConfig
from nautilus_trader.config import LiveRiskEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.trading.strategy import StrategyConfig


class TurbineMarketMakerConfig(StrategyConfig, frozen=True):
    """
    Configuration for the Turbine market maker strategy.
    """
    instrument_id: InstrumentId
    spread_bps: int = 200  # 2% spread
    order_size: Decimal = Decimal("0.50")  # $0.50 per order (small for testing)
    max_position: Decimal = Decimal("1.0")  # Max $1 position


class TurbineMarketMaker(Strategy):
    """
    A simple market making strategy for Turbine prediction markets.
    """

    def __init__(self, config: TurbineMarketMakerConfig) -> None:
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.spread_bps = config.spread_bps
        self.order_size = config.order_size
        self.max_position = config.max_position
        self._bid_order_id = None
        self._ask_order_id = None

    def on_start(self) -> None:
        """Called when the strategy starts."""
        self.log.info("Starting Turbine Market Maker...")
        self.subscribe_quote_ticks(self.instrument_id)
        self.log.info(f"Subscribed to {self.instrument_id}")

    def on_stop(self) -> None:
        """Called when the strategy stops."""
        self.log.info("Stopping Turbine Market Maker...")
        self.cancel_all_orders(self.instrument_id)

    def on_quote_tick(self, tick: QuoteTick) -> None:
        """Called when a new quote tick is received."""
        if tick.instrument_id != self.instrument_id:
            return

        bid_price = tick.bid_price.as_decimal()
        ask_price = tick.ask_price.as_decimal()
        mid_price = (bid_price + ask_price) / 2

        self.log.info(
            f"Quote: bid={bid_price:.4f}, ask={ask_price:.4f}, mid={mid_price:.4f}"
        )

        # Calculate our spread
        half_spread = mid_price * Decimal(self.spread_bps) / Decimal(10000) / 2
        our_bid = max(Decimal("0.001"), min(Decimal("0.998"), mid_price - half_spread))
        our_ask = max(Decimal("0.002"), min(Decimal("0.999"), mid_price + half_spread))

        self._update_orders(our_bid, our_ask)

    def _update_orders(self, bid_price: Decimal, ask_price: Decimal) -> None:
        """Update bid and ask orders."""
        # Cancel existing orders
        if self._bid_order_id:
            self.cancel_order(self._bid_order_id)
            self._bid_order_id = None

        if self._ask_order_id:
            self.cancel_order(self._ask_order_id)
            self._ask_order_id = None

        # Get current position
        position = self.cache.position(self.instrument_id)
        current_qty = position.quantity.as_decimal() if position else Decimal(0)

        # Place new bid if we're not at max long position
        if current_qty < self.max_position:
            bid_order = self.order_factory.limit(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=Quantity.from_str(str(self.order_size)),
                price=Price.from_str(f"{bid_price:.6f}"),
                time_in_force=TimeInForce.GTC,
            )
            self.submit_order(bid_order)
            self._bid_order_id = bid_order.client_order_id
            self.log.info(f"Placed BID: {bid_price:.6f} x {self.order_size}")

        # Place new ask if we have position to sell
        if current_qty > Decimal(0):
            ask_order = self.order_factory.limit(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=Quantity.from_str(str(min(current_qty, self.order_size))),
                price=Price.from_str(f"{ask_price:.6f}"),
                time_in_force=TimeInForce.GTC,
            )
            self.submit_order(ask_order)
            self._ask_order_id = ask_order.client_order_id
            self.log.info(f"Placed ASK: {ask_price:.6f} x {self.order_size}")


def get_current_btc_market():
    """Fetch the current active BTC quick market from Turbine."""
    import requests

    resp = requests.get("https://api.turbinefi.com/api/v1/quick-markets/BTC?chain_id=137")
    data = resp.json()

    if not data.get('active'):
        return None

    qm = data['quickMarket']
    return {
        'market_id': qm['marketId'],
        'strike_price': qm['startPrice'] / 1e8,
        'end_time': qm['endTime'],
    }


def main():
    """Run the Turbine market maker bot."""
    # Check for required environment variables
    required_vars = [
        "TURBINE_PRIVATE_KEY",
        "TURBINE_API_KEY_ID",
        "TURBINE_API_PRIVATE_KEY",
    ]

    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(f"Error: Missing required environment variables: {missing}")
        return

    # Get current BTC market
    print("\nFetching current BTC quick market...")
    market_info = get_current_btc_market()

    if not market_info:
        print("No active BTC quick market found!")
        return

    print(f"Found market: {market_info['market_id'][:20]}...")
    print(f"Strike price: ${market_info['strike_price']:,.2f}")

    # Create instrument ID for YES outcome
    instrument_id = get_turbine_instrument_id(market_info['market_id'], "YES")
    print(f"Instrument ID: {instrument_id}")

    # Configure the trading node
    config = TradingNodeConfig(
        trader_id=TraderId("TURBINE-MM-001"),
        logging=LoggingConfig(log_level="INFO"),
        data_engine=LiveDataEngineConfig(
            time_bars_build_with_no_updates=True,
            time_bars_timestamp_on_close=True,
        ),
        exec_engine=LiveExecEngineConfig(),
        risk_engine=LiveRiskEngineConfig(),
        data_clients={
            "TURBINE": TurbineDataClientConfig(
                chain_id=137,  # Polygon mainnet
                instrument_provider=InstrumentProviderConfig(
                    load_all=False,  # We'll load specific instruments
                ),
            ),
        },
        exec_clients={
            "TURBINE": TurbineExecClientConfig(
                chain_id=137,  # Polygon mainnet
            ),
        },
    )

    # Create and configure the trading node
    node = TradingNode(config=config)

    # Add data client factory
    node.add_data_client_factory("TURBINE", TurbineLiveDataClientFactory)
    node.add_exec_client_factory("TURBINE", TurbineLiveExecClientFactory)

    # Configure strategy with small amounts for testing
    strategy_config = TurbineMarketMakerConfig(
        instrument_id=instrument_id,
        spread_bps=200,  # 2% spread
        order_size=Decimal("0.50"),  # $0.50 per order
        max_position=Decimal("1.0"),  # Max $1 position
    )

    # Add strategy
    strategy = TurbineMarketMaker(config=strategy_config)
    node.trader.add_strategy(strategy)

    # Build and run
    print("\nBuilding trading node...")
    node.build()

    print("\nStarting trading node...")
    try:
        node.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        node.dispose()


if __name__ == "__main__":
    main()
