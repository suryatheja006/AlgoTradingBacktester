class Order:
    def __init__(self, symbol, price, quantity):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity

class Trader:
    def __init__(self):
        self.buy_price = 9998
        self.sell_price = 10002
        self.quantity = 10

    def run(self, state):
        orders = []
        if state.timestamp % 2 == 1:  # Odd timestamp: buy
            orders.append(Order("PRODUCT", self.buy_price, self.quantity))
        else:  # Even timestamp: sell
            orders.append(Order("PRODUCT", self.sell_price, -self.quantity))
        return {"PRODUCT": orders}, {}, "alternating_strategy"
