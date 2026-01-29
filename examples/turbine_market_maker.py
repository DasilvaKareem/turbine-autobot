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
    python turbine_market_maker.py
"""

import asyncio
import os
from decimal import Decimal

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# NautilusTrader imports
from nautilus_trader.adapters.turbine import (
    TURBINE_VENUE,
    TurbineDataClientConfig,
    TurbineExecClientConfig,
    TurbineLiveDataClientFactory,
    TurbineLiveExecClientFactory,
    get_turbine_instrument_id,
)
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.common.enums import LogLevel
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LiveDataEngineConfig
from nautilus_trader.config import LiveExecEngineConfig
from nautilus_trader.config import LiveRiskEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
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

    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument to market make.
    spread_bps : int
        The spread in basis points (e.g., 100 = 1%).
    order_size : Decimal
        The size of each order in USDC.
    max_position : Decimal
        Maximum position size allowed.

    """

    instrument_id: InstrumentId
    spread_bps: int = 200  # 2% spread
    order_size: Decimal = Decimal("10.0")  # 10 USDC per order
    max_position: Decimal = Decimal("100.0")  # Max 100 USDC position


class TurbineMarketMaker(Strategy):
    """
    A simple market making strategy for Turbine prediction markets.

    This strategy:
    1. Subscribes to quote updates for the target instrument
    2. Places bid and ask orders around the mid price
    3. Manages inventory to stay within position limits
    """

    def __init__(self, config: TurbineMarketMakerConfig) -> None:
        super().__init__(config)
        self.instrument_id = config.instrument_id
        self.spread_bps = config.spread_bps
        self.order_size = config.order_size
        self.max_position = config.max_position

        # Track our orders
        self._bid_order_id = None
        self._ask_order_id = None

    def on_start(self) -> None:
        """Called when the strategy starts."""
        self.log.info("Starting Turbine Market Maker...")

        # Subscribe to quote updates
        self.subscribe_quote_ticks(self.instrument_id)

        self.log.info(f"Subscribed to {self.instrument_id}")

    def on_stop(self) -> None:
        """Called when the strategy stops."""
        self.log.info("Stopping Turbine Market Maker...")

        # Cancel all open orders
        self.cancel_all_orders(self.instrument_id)

    def on_quote_tick(self, tick: QuoteTick) -> None:
        """Called when a new quote tick is received."""
        if tick.instrument_id != self.instrument_id:
            return

        # Calculate mid price
        bid_price = tick.bid_price.as_decimal()
        ask_price = tick.ask_price.as_decimal()
        mid_price = (bid_price + ask_price) / 2

        self.log.info(
            f"Quote: bid={bid_price:.4f}, ask={ask_price:.4f}, mid={mid_price:.4f}"
        )

        # Calculate our spread
        half_spread = mid_price * Decimal(self.spread_bps) / Decimal(10000) / 2

        our_bid = mid_price - half_spread
        our_ask = mid_price + half_spread

        # Ensure prices are within valid range (0.001 to 0.999)
        our_bid = max(Decimal("0.001"), min(Decimal("0.998"), our_bid))
        our_ask = max(Decimal("0.002"), min(Decimal("0.999"), our_ask))

        # Update orders
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
        print("\nPlease set them in your .env file:")
        print("  TURBINE_PRIVATE_KEY=0x...")
        print("  TURBINE_API_KEY_ID=...")
        print("  TURBINE_API_PRIVATE_KEY=...")
        return

    # Example market ID - replace with an actual market from Turbine
    # You can get market IDs from the Turbine API: client.get_markets()
    example_market_id = "0x1234567890abcdef1234567890abcdef12345678"
    instrument_id = get_turbine_instrument_id(example_market_id, "YES")

    # Configure the trading node
    config = TradingNodeConfig(
        trader_id=TraderId("TURBINE-MM-001"),
        logging=LoggingConfig(log_level=LogLevel.INFO),
        data_engine=LiveDataEngineConfig(
            time_bars_build_with_no_updates=True,
            time_bars_timestamp_on_close=True,
        ),
        exec_engine=LiveExecEngineConfig(),
        risk_engine=LiveRiskEngineConfig(),
        data_clients={
            "TURBINE": TurbineDataClientConfig(
                chain_id=84532,  # Base Sepolia testnet
                instrument_provider=InstrumentProviderConfig(
                    load_all=True,
                ),
            ),
        },
        exec_clients={
            "TURBINE": TurbineExecClientConfig(
                chain_id=84532,  # Base Sepolia testnet
            ),
        },
    )

    # Create and configure the trading node
    node = TradingNode(config=config)

    # Add data client factory
    node.add_data_client_factory("TURBINE", TurbineLiveDataClientFactory)
    node.add_exec_client_factory("TURBINE", TurbineLiveExecClientFactory)

    # Configure strategy
    strategy_config = TurbineMarketMakerConfig(
        instrument_id=instrument_id,
        spread_bps=200,  # 2% spread
        order_size=Decimal("10.0"),  # 10 USDC
        max_position=Decimal("100.0"),  # Max 100 USDC position
    )

    # Add strategy
    strategy = TurbineMarketMaker(config=strategy_config)
    node.trader.add_strategy(strategy)

    # Build and run
    node.build()

    try:
        node.run()
    finally:
        node.dispose()


if __name__ == "__main__":
    main()
