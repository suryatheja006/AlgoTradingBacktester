# Do not remove this line
from src.backtester import Order

# Strategy.py must include the Trader class with a run() method
class Trader:
    '''
    INPUT:
        - state: holds information about market trades, timestamps, position etc.,
                 Some attributes may not be available right now. 
    OUTPUT:
        - results: Dict{"PRODUCT_NAME": List[Order]} 
                   holds your orders for each product in a dictionary
    '''

    def run(self, state):
        
        results = {}
        orders = []

        # Hardcoded for now, you will decide this. This is not the optimal strategy
        buy_price = 9998
        sell_price = 10002

        if state.timestamp % 2 == 1:
            # Order("PRODUCT_NAME": str, price: int, quantity: int)
            orders.append(Order("PRODUCT", buy_price, 10)) # Positive quantity -> Buy order
        else:
            orders.append(Order("PRODUCT", sell_price, -10)) # Negative quantity -> Sell order

        results["PRODUCT"] = orders

        return results
