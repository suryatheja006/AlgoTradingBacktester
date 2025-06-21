from src.backtester import Order, OrderBook
from typing import List
import pandas as pd
import numpy as np
import statistics

# Base Class
class BaseClass:
    def __init__(self, product_name, max_position):
        self.product_name = product_name
        self.max_position = max_position
    
    def get_orders(self, state, orderbook, position):
        """Override this method in product-specific strategies"""
        return []

class SudowoodoStrategy(BaseClass):
    def __init__(self):
        super().__init__("SUDOWOODO", 50)
        self.fair_value = 10000
    
    def get_orders(self, state, orderbook, position):
        orders = []
        
        if not orderbook.buy_orders and not orderbook.sell_orders:
            return orders
        
        orders.append(Order(self.product_name, self.fair_value + 2, -10))
        orders.append(Order(self.product_name, self.fair_value - 2, 10))

        return orders

class DrowzeeStrategy(BaseClass):
    def __init__(self):
        super().__init__("DROWZEE", 50)
    
    def get_orders(self, state, orderbook, position):
        orders = []
        
        # LOGIC FOR DROWZEE
        
        return orders

class AbraStrategy(BaseClass):
    def __init__(self):
        super().__init__("ABRA", 50)
        self.reversion_window = 200
        
    def get_orders(self, state, orderbook, position):
        orders = []

        # LOGIC FOR ABRA
        
        return orders

class Trader:
    def __init__(self):
        self.strategies = {
            "SUDOWOODO": SudowoodoStrategy(),
            "DROWZEE": DrowzeeStrategy(), 
            "ABRA": AbraStrategy()
        }
    
    def run(self, state):
        result = {}
        positions = getattr(state, 'positions', {})
        
        for product, orderbook in state.order_depth.items():
            current_position = positions.get(product, 0)
            product_orders = self.strategies[product].get_orders(state, orderbook, current_position)
            result[product] = product_orders
        
        return result
