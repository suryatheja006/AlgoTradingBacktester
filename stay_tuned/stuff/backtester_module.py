import csv
import json
from typing import Dict, List, Any, Optional, Tuple
from .trade import Trade, Order
from .order_book import OrderBook
from .trading_state import TradingState

class Backtester:
    """Main backtesting engine for the trading system."""
    
    # Position limits for each product
    POSITION_LIMITS = {
        "GOLD": 50,
        "SILVER": 50,
        "BRONZE": 50
    }
    
    def __init__(self, price_csv_path: str, trades_csv_path: str, trader: Any):
        """Initialize the backtester."""
        self.price_csv_path = price_csv_path
        self.trades_csv_path = trades_csv_path
        self.trader = trader
        
        # Data storage
        self.prices: Dict[int, Dict[str, Dict[str, str]]] = {}
        self.trades: Dict[int, Dict[str, List[Trade]]] = {}
        
        # State tracking
        self.positions: Dict[str, int] = {}
        self.pnls: Dict[str, float] = {}
        self.position = 0  # Total position across all products
        self.pnl = 0.0     # Total PnL across all products
        
        # History for analysis
        self.timestamps: List[int] = []
        
        # Per-product history
        self.position_history: Dict[str, List[int]] = {}
        self.pnl_history: Dict[str, List[float]] = {}
        self.volume_history: Dict[str, List[int]] = {}
        self.bid_price_history: Dict[str, List[float]] = {}
        self.ask_price_history: Dict[str, List[float]] = {}
        self.mid_price_history: Dict[str, List[float]] = {}
        
        # Total history across all products
        self.total_position_history: List[int] = []
        self.total_pnl_history: List[float] = []
        self.total_volume_history: List[int] = []
        
        # Order books for each product
        self.order_books: Dict[str, OrderBook] = {}
        
        # Trader data that persists between iterations
        self.trader_data = ""
    
    def load_data(self) -> None:
        """Load price and trade data from CSV files."""
        # Load price data
        with open(self.price_csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                try:
                    ts = int(row['timestamp'])
                    product = row['product']
                    
                    # Initialize timestamp entry if it doesn't exist
                    if ts not in self.prices:
                        self.prices[ts] = {}
                    
                    # Store price data by product
                    self.prices[ts][product] = row
                    
                except (ValueError, KeyError) as e:
                    print(f"Skipping invalid price row: {row}")
                    continue

        # Load trades data
        with open(self.trades_csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                try:
                    ts = int(row['timestamp'])
                    symbol = row['symbol']
                    price = float(row['price'])
                    quantity = int(float(row['quantity']))  # Handle potential float quantities
                    
                    # Skip zero quantity trades
                    if quantity == 0:
                        continue
                    
                    # Create trade with default MARKET participants
                    trade = Trade(symbol, int(price), quantity, 'MARKET', 'MARKET', ts)
                    
                    # Initialize data structures if needed
                    if ts not in self.trades:
                        self.trades[ts] = {}
                    if symbol not in self.trades[ts]:
                        self.trades[ts][symbol] = []
                    
                    # Add trade to the list
                    self.trades[ts][symbol].append(trade)
                    
                except (ValueError, KeyError) as e:
                    print(f"Skipping invalid trade row: {row}")
                    continue
        
        # Initialize history tracking for each product
        products = set()
        for ts_data in self.prices.values():
            products.update(ts_data.keys())
        
        for product in products:
            self.position_history[product] = []
            self.pnl_history[product] = []
            self.volume_history[product] = []
            self.bid_price_history[product] = []
            self.ask_price_history[product] = []
            self.mid_price_history[product] = []
            self.positions[product] = 0
            self.pnls[product] = 0.0
            
            # Initialize order book for the product
            self.order_books[product] = OrderBook()
    
    def run(self) -> None:
        """Run the backtest simulation."""
        print("Starting backtest...")
        
        # Load the data
        self.load_data()
        
        # Get all timestamps and sort them
        all_timestamps = sorted(set(self.prices.keys()) | set(self.trades.keys()))
        
        print(f"Processing {len(all_timestamps)} timestamps...")
        
        for ts in all_timestamps:
            # Update order books with new market data
            self._update_order_books(ts)
            
            # Get the current state
            state = self._get_state(ts)
            if state is None:
                continue
            
            # Get orders from the trader
            try:
                orders_dict, self.trader_data = self.trader.run(state)
            except Exception as e:
                print(f"Error in trader's run method: {e}")
                orders_dict = {}
            
            # Process the orders
            executed_trades = {}
            for product, orders in (orders_dict or {}).items():
                if product in self.order_books:
                    product_trades = self._process_orders(orders, ts)
                    if product in product_trades and product_trades[product]:
                        executed_trades[product] = product_trades[product]
            
            # Update history and positions
            self._update_history(ts, executed_trades)
        
        # Print final results
        print("\n===== BACKTESTING RESULTS =====")
        print(f"Final Total PnL: {self.pnl:.2f}")
        for product in sorted(self.positions.keys()):
            print(f"{product} - Position: {self.positions[product]}, PnL: {self.pnls.get(product, 0):.2f}")
        print("==============================\n")
    
    def _update_order_books(self, timestamp: int) -> None:
        """Update order books with new market data."""
        if timestamp in self.prices:
            for product, data in self.prices[timestamp].items():
                if product not in self.order_books:
                    self.order_books[product] = OrderBook()
                
                order_book = self.order_books[product]
                
                # Clear existing orders
                order_book.buy_orders.clear()
                order_book.sell_orders.clear()
                
                # Add buy orders (bids)
                for i in range(1, 4):
                    price_key = f'bid_price_{i}'
                    volume_key = f'bid_volume_{i}'
                    if price_key in data and volume_key in data and data[price_key] and data[volume_key]:
                        try:
                            price = int(float(data[price_key]))
                            volume = int(float(data[volume_key]))
                            if price > 0 and volume > 0:
                                order_book.add_buy_order(price, volume)
                        except (ValueError, TypeError):
                            continue
                
                # Add sell orders (asks)
                for i in range(1, 4):
                    price_key = f'ask_price_{i}'
                    volume_key = f'ask_volume_{i}'
                    if price_key in data and volume_key in data and data[price_key] and data[volume_key]:
                        try:
                            price = int(float(data[price_key]))
                            volume = int(float(data[volume_key]))
                            if price > 0 and volume > 0:
                                order_book.add_sell_order(price, volume)
                        except (ValueError, TypeError):
                            continue
    
    def _get_state(self, timestamp: int) -> Optional[TradingState]:
        """Create a TradingState object for the current timestamp."""
        if timestamp not in self.prices:
            return None
        
        # Create listings for all products
        listings = {}
        positions = {}
        
        for product in self.prices[timestamp].keys():
            # Create listing
            listings[product] = {
                'symbol': product,
                'product': product,
                'denomination': 'DOLLARS'
            }
            
            # Get current position
            positions[product] = self.positions.get(product, 0)
        
        # Get trades for this timestamp
        own_trades = self.trades.get(timestamp, {})
        market_trades = {}
        
        # Create TradingState
        return TradingState(
            trader_data=self.trader_data,
            timestamp=timestamp,
            listings=listings,
            order_depths=self.order_books,
            own_trades=own_trades,
            market_trades=market_trades,
            position=positions
        )
    
    def _process_orders(self, orders: List[Order], timestamp: int) -> Dict[str, List[Trade]]:
        """Process a list of orders and return executed trades by symbol."""
        executed_trades: Dict[str, List[Trade]] = {}
        
        for order in orders:
            if not isinstance(order, Order):
                continue
                
            symbol = order.symbol
            if symbol not in self.order_books:
                continue
                
            if symbol not in executed_trades:
                executed_trades[symbol] = []
                
            order_book = self.order_books[symbol]
            current_position = self.positions.get(symbol, 0)
            
            # Check position limits before processing order
            position_limit = self.POSITION_LIMITS.get(symbol, 50)  # Default to 50 if not specified
            
            if order.is_buy:
                # For buy orders, check if we're below the position limit
                max_buy_qty = position_limit - current_position
                if max_buy_qty <= 0:
                    continue  # Already at or above position limit, skip buy order
                    
                best_ask, best_ask_qty = order_book.get_best_ask()
                if best_ask is not None and order.price >= best_ask:
                    # Calculate execution price and quantity
                    price = best_ask
                    quantity = min(order.abs_quantity, best_ask_qty, max_buy_qty)
                    
                    if quantity <= 0:
                        continue  # No quantity left to buy within position limits
                    
                    # Create trade
                    trade = Trade(
                        symbol=symbol,
                        price=price,
                        quantity=quantity,
                        buyer="TRADER",
                        seller="MARKET",
                        timestamp=timestamp
                    )
                    executed_trades[symbol].append(trade)
                    
                    # Update position and PnL immediately
                    self.positions[symbol] = current_position + quantity
                    self.pnls[symbol] = self.pnls.get(symbol, 0.0) - (price * quantity)
                    
                    # Update order book
                    order_book.remove_sell_order(price, quantity)
                    
            else:  # Sell order
                # For sell orders, check if we're above the negative position limit
                max_sell_qty = position_limit + current_position  # current_position can be negative
                if max_sell_qty <= 0:
                    continue  # Already at or below negative position limit, skip sell order
                    
                best_bid, best_bid_qty = order_book.get_best_bid()
                if best_bid is not None and order.price <= best_bid:
                    # Calculate execution price and quantity
                    price = best_bid
                    quantity = min(order.abs_quantity, best_bid_qty, max_sell_qty)
                    
                    if quantity <= 0:
                        continue  # No quantity left to sell within position limits
                    
                    # Create trade
                    trade = Trade(
                        symbol=symbol,
                        price=price,
                        quantity=quantity,  # Positive quantity for sell
                        buyer="MARKET",
                        seller="TRADER",
                        timestamp=timestamp
                    )
                    executed_trades[symbol].append(trade)
                    
                    # Update position and PnL immediately
                    self.positions[symbol] = current_position - quantity
                    self.pnls[symbol] = self.pnls.get(symbol, 0.0) + (price * quantity)
                    
                    # Update order book
                    order_book.remove_buy_order(price, quantity)
        
        self.pnl = sum(self.pnls.values())  # Update total PnL
        return executed_trades
    
    def _update_history(self, timestamp: int, executed_trades: Dict[str, List[Trade]]) -> None:
        """Update historical data with the current state."""
        # Update timestamp
        self.timestamps.append(timestamp)
        
        # Update history for each product
        for product in self.positions.keys():
            # Initialize history lists if needed
            if product not in self.position_history:
                self.position_history[product] = []
            if product not in self.pnl_history:
                self.pnl_history[product] = []
            if product not in self.volume_history:
                self.volume_history[product] = []
            if product not in self.bid_price_history:
                self.bid_price_history[product] = []
            if product not in self.ask_price_history:
                self.ask_price_history[product] = []
            if product not in self.mid_price_history:
                self.mid_price_history[product] = []
            
            # Update position history
            self.position_history[product].append(self.positions.get(product, 0))
            
            # Update PnL history
            self.pnl_history[product].append(self.pnls.get(product, 0.0))
            
            # Calculate and update volume for this timestamp
            volume = 0
            if product in executed_trades:
                for trade in executed_trades[product]:
                    volume += abs(trade.quantity)
            self.volume_history[product].append(volume)
            
            # Update price history from raw price data
            if timestamp in self.prices and product in self.prices[timestamp]:
                product_data = self.prices[timestamp][product]
                
                # Get best bid and ask prices from the raw data
                best_bid = None
                best_ask = None
                
                # Check for bid prices (we'll take the highest bid)
                for i in range(1, 4):
                    price_key = f'bid_price_{i}'
                    if price_key in product_data and product_data[price_key]:
                        try:
                            bid_price = float(product_data[price_key])
                            if best_bid is None or bid_price > best_bid:
                                best_bid = bid_price
                        except (ValueError, TypeError):
                            pass
                
                # Check for ask prices (we'll take the lowest ask)
                for i in range(1, 4):
                    price_key = f'ask_price_{i}'
                    if price_key in product_data and product_data[price_key]:
                        try:
                            ask_price = float(product_data[price_key])
                            if best_ask is None or ask_price < best_ask:
                                best_ask = ask_price
                        except (ValueError, TypeError):
                            pass
                
                # Update bid and ask histories
                if best_bid is not None:
                    self.bid_price_history[product].append(best_bid)
                elif self.bid_price_history[product]:  # If no new bid, use previous value
                    self.bid_price_history[product].append(self.bid_price_history[product][-1])
                else:  # If no history, use 0
                    self.bid_price_history[product].append(0)
                
                if best_ask is not None:
                    self.ask_price_history[product].append(best_ask)
                elif self.ask_price_history[product]:  # If no new ask, use previous value
                    self.ask_price_history[product].append(self.ask_price_history[product][-1])
                else:  # If no history, use 0
                    self.ask_price_history[product].append(0)
                
                # Calculate and update mid price
                if best_bid is not None and best_ask is not None:
                    mid_price = (best_bid + best_ask) / 2
                elif best_bid is not None:
                    mid_price = best_bid
                elif best_ask is not None:
                    mid_price = best_ask
                elif self.mid_price_history[product]:  # If no new prices, use previous mid price
                    mid_price = self.mid_price_history[product][-1]
                else:  # If no history, use 0
                    mid_price = 0
                    
                self.mid_price_history[product].append(mid_price)
        
        # Update total position and PnL
        total_position = sum(abs(pos) for pos in self.positions.values())
        self.total_position_history.append(total_position)
        
        total_pnl = sum(self.pnls.values())
        self.total_pnl_history.append(total_pnl)
        self.pnl = total_pnl
    
    def get_results(self) -> Dict[str, Any]:
        """Get the backtest results."""
        return {
            'timestamps': self.timestamps,
            'positions': self.positions,
            'pnls': self.pnls,
            'total_pnl': self.pnl,
            'position_history': self.position_history,
            'pnl_history': self.pnl_history,
            'volume_history': self.volume_history,
            'bid_price_history': self.bid_price_history,
            'ask_price_history': self.ask_price_history,
            'mid_price_history': self.mid_price_history,
            'total_position_history': self.total_position_history,
            'total_pnl_history': self.total_pnl_history
        }
