from typing import Dict, List, Any, Optional
from .order_book import OrderBook
from .trade import Trade, Order

# Type aliases
Product = str
Position = int
Symbol = str
UserId = str

class TradingState:
    """Represents the current state of the trading environment."""
    
    def __init__(self,
                 trader_data: str,
                 timestamp: int,
                 listings: Dict[Symbol, Any],
                 order_depths: Dict[Symbol, OrderBook],
                 own_trades: Dict[Symbol, List[Trade]],
                 market_trades: Dict[Symbol, List[Trade]],
                 position: Dict[Product, Position],
                 observations: Dict[Symbol, Any] = None):
        """Initialize a new TradingState.
        
        Args:
            trader_data: Custom data that persists between rounds
            timestamp: Current timestamp in milliseconds
            listings: Available products and their details
            order_depths: Current state of the order book for each product
            own_trades: Trades executed by this trader in the last iteration
            market_trades: All trades that occurred in the market in the last iteration
            position: Current position for each product
            observations: Market observations (e.g., for derivatives)
        """
        self.trader_data = trader_data
        self.timestamp = timestamp
        self.listings = listings or {}
        self.order_depths = order_depths or {}
        self.own_trades = own_trades or {}
        self.market_trades = market_trades or {}
        self.position = position or {}
        self.observations = observations or {}
    
    def get_position(self, product: Product) -> Position:
        """Get the current position for a product."""
        return self.position.get(product, 0)
    
    def get_order_book(self, product: Symbol) -> OrderBook:
        """Get the order book for a product."""
        return self.order_depths.get(product, OrderBook())
    
    def toJSON(self):
        """Convert the trading state to a JSON-serializable dictionary."""
        return {
            'timestamp': self.timestamp,
            'listings': self.listings,
            'order_depths': {k: str(v) for k, v in self.order_depths.items()},
            'own_trades': {k: [str(t) for t in v] for k, v in self.own_trades.items()},
            'market_trades': {k: [str(t) for t in v] for k, v in self.market_trades.items()},
            'position': self.position,
            'observations': self.observations,
            'trader_data': self.trader_data
        }
