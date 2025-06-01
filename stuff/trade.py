from typing import Optional, Union

# Type aliases
Symbol = str
UserId = str

class Trade:
    """Represents a trade that has been executed.
    
    Attributes:
        symbol: The product being traded
        price: The price at which the trade was executed
        quantity: The quantity traded (positive for buy, negative for sell)
        buyer: The buyer's user ID (or "MARKET" for market orders)
        seller: The seller's user ID (or "MARKET" for market orders)
        timestamp: When the trade occurred
    """
    def __init__(self, symbol: Symbol, price: int, quantity: int, 
                 buyer: Optional[UserId] = None, seller: Optional[UserId] = None, 
                 timestamp: int = 0) -> None:
        if not isinstance(price, int) or not isinstance(quantity, int):
            raise ValueError("Price and quantity must be integers")
        if quantity == 0:
            raise ValueError("Trade quantity cannot be zero")
            
        self.symbol = symbol
        self.price: int = price
        self.quantity: int = quantity  # Positive for buy, negative for sell
        self.buyer = buyer or "MARKET"
        self.seller = seller or "MARKET"
        self.timestamp = timestamp
    
    @property
    def is_buy(self) -> bool:
        """Return True if this is a buy trade (quantity > 0)."""
        return self.quantity > 0
    
    @property
    def is_sell(self) -> bool:
        """Return True if this is a sell trade (quantity < 0)."""
        return self.quantity < 0
    
    @property
    def abs_quantity(self) -> int:
        """Return the absolute quantity of the trade."""
        return abs(self.quantity)
    
    def __str__(self) -> str:
        return f"Trade({self.symbol} {self.quantity}@{self.price} {self.buyer}<-{self.seller} t={self.timestamp})"
    
    def __repr__(self) -> str:
        return (f"Trade(symbol={self.symbol!r}, price={self.price}, quantity={self.quantity}, "
                f"buyer='{self.buyer}', seller='{self.seller}', timestamp={self.timestamp})")


class Order:
    """Represents a limit order in the market.
    
    Attributes:
        symbol: The product being traded
        price: The limit price (must be > 0)
        quantity: Positive for buy orders, negative for sell orders
    """
    def __init__(self, symbol: Symbol, price: int, quantity: int) -> None:
        if not isinstance(price, int) or not isinstance(quantity, int):
            raise ValueError("Price and quantity must be integers")
        if price <= 0:
            raise ValueError("Price must be positive")
        if quantity == 0:
            raise ValueError("Quantity cannot be zero")
            
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
    
    @property
    def is_buy(self) -> bool:
        """Return True if this is a buy order."""
        return self.quantity > 0
    
    @property
    def is_sell(self) -> bool:
        """Return True if this is a sell order."""
        return self.quantity < 0
    
    @property
    def abs_quantity(self) -> int:
        """Return the absolute quantity of the order."""
        return abs(self.quantity)
    
    def __str__(self) -> str:
        side = "BUY" if self.is_buy else "SELL"
        return f"{side} {self.abs_quantity} {self.symbol} @ {self.price}"
    
    def __repr__(self) -> str:
        return f"Order(symbol={self.symbol!r}, price={self.price}, quantity={self.quantity})"
