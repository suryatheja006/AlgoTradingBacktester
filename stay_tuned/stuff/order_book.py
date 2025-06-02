from typing import Dict, Optional, Tuple, List

class OrderBook:
    """Represents the order book for a single product."""
    
    def __init__(self):
        # Dictionary to store buy orders {price: quantity}
        self.buy_orders: Dict[int, int] = {}
        # Dictionary to store sell orders {price: quantity}
        self.sell_orders: Dict[int, int] = {}
    
    def add_buy_order(self, price: int, quantity: int) -> None:
        """Add or update a buy order."""
        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive")
        self.buy_orders[price] = self.buy_orders.get(price, 0) + quantity
    
    def add_sell_order(self, price: int, quantity: int) -> None:
        """Add or update a sell order."""
        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive")
        self.sell_orders[price] = self.sell_orders.get(price, 0) + quantity
    
    def get_best_bid(self) -> Tuple[int, int]:
        """Get best (highest) bid price and quantity."""
        if not self.buy_orders:
            return 0, 0
        price = max(self.buy_orders.keys())
        return price, self.buy_orders[price]
    
    def get_best_ask(self) -> Tuple[int, int]:
        """Get best (lowest) ask price and quantity."""
        if not self.sell_orders:
            return 0, 0
        price = min(self.sell_orders.keys())
        return price, self.sell_orders[price]
    
    def get_mid_price(self) -> float:
        """Calculate the mid price from best bid and ask."""
        best_bid, _ = self.get_best_bid()
        best_ask, _ = self.get_best_ask()
        if best_bid == 0 or best_ask == 0:
            return 0.0
        return (best_bid + best_ask) / 2.0
    
    def remove_buy_order(self, price: int, quantity: int) -> None:
        """Remove or reduce a buy order."""
        if price not in self.buy_orders:
            return
        self.buy_orders[price] -= quantity
        if self.buy_orders[price] <= 0:
            del self.buy_orders[price]
    
    def remove_sell_order(self, price: int, quantity: int) -> None:
        """Remove or reduce a sell order."""
        if price not in self.sell_orders:
            return
        self.sell_orders[price] -= quantity
        if self.sell_orders[price] <= 0:
            del self.sell_orders[price]
    
    def is_empty(self) -> bool:
        """Check if the order book is empty."""
        return not (self.buy_orders or self.sell_orders)
    
    def __str__(self) -> str:
        """String representation of the order book."""
        bids = sorted(self.buy_orders.items(), reverse=True)
        asks = sorted(self.sell_orders.items())
        
        lines = ["OrderBook:", "  Bids:"]
        for price, qty in bids:
            lines.append(f"    {qty:4} @ {price:6}")
            
        lines.append("  Asks:")
        for price, qty in asks:
            lines.append(f"    {qty:4} @ {price:6}")
            
        return "\n".join(lines)
