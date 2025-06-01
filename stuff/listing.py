from typing import Optional

# Type aliases
Symbol = str
Product = str

class Listing:
    """Represents a product listing in the market."""
    
    def __init__(self, symbol: Symbol, product: Product, denomination: str):
        """Initialize a new listing.
        
        Args:
            symbol: The trading symbol (e.g., "GOLD")
            product: The product name (e.g., "GOLD")
            denomination: The currency or unit of account (e.g., "DOLLARS")
        """
        self.symbol = symbol
        self.product = product
        self.denomination = denomination
    
    def __str__(self) -> str:
        return f"{self.symbol}: {self.product} ({self.denomination})"
    
    def __repr__(self) -> str:
        return f"Listing(symbol={self.symbol!r}, product={self.product!r}, denomination={self.denomination!r})"
