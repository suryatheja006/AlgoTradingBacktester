from stuff.trade import Order
from stuff.order_book import OrderBook
from stuff.trading_state import TradingState
from typing import List, Dict, Any
import string

class Trader:

    def run(self, state: TradingState):
        result = {}

        for product, order_book in state.order_depths.items():
            orders: List[Order] = []
            if product == "GOLD":
                orders.append(Order(product, 9998, 30))
                orders.append(Order(product, 10002, -30))
            elif product == "SILVER":
                orders.append(Order(product, 2020, 30))
                orders.append(Order(product, 2040, -30))
            elif product == "BRONZE":
                orders.append(Order(product, 1919, 30))
                orders.append(Order(product, 1940, -30))

            result[product] = orders
        
        traderData = {
            "Mid-prices-GOLD": [order.price for order in result.get("GOLD", [])],
            "Mid-prices-SILVER": [order.price for order in result.get("SILVER", [])],
            "Mid-prices-BRONZE": [order.price for order in result.get("BRONZE", [])]
        }

        return result, traderData