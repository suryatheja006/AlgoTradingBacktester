from src.backtester import Order, OrderBook
from typing import List

class Trader:
    
    def run(self, state):
        result = {}
        
        orders: List[Order] = []
        order_depth: OrderBook = state.order_depth
        if len(order_depth.sell_orders) != 0:
            best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
            if int(best_ask) < 10000:
                orders.append(Order("PRODUCT", best_ask, -best_ask_amount))

        if len(order_depth.buy_orders) != 0:
            best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
            if int(best_bid) > 10000:
                orders.append(Order("PRODUCT", best_bid, -best_bid_amount))
        
        result["PRODUCT"] = orders
        return result