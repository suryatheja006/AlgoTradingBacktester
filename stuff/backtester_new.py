import csv
from typing import List, Dict, Any, Optional, Tuple, Union
import json
from json import JSONEncoder

# Import from our new modules
from .trade import Trade, Order, Symbol, UserId, Product, Position, Observation
from .order_book import OrderBook
from .listing import Listing
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
        """Initialize the backtester with data paths and trader instance."""
        self.price_csv_path = price_csv_path
        self.trades_csv_path = trades_csv_path
        self.trader = trader
        
        # Data storage
        self.prices: Dict[int, Dict[str, Dict[str, str]]] = {}
        self.trades: Dict[int, Dict[str, List[Trade]]] = {}
        
        # State tracking
        self.positions: Dict[str, int] = {}
        self.pnls: Dict[str, float] = {}
        self.position = 0
        self.pnl = 0.0
        
        # History for analysis
        self.timestamps: List[int] = []
        self.position_history: Dict[str, List[int]] = {}
        self.pnl_history: Dict[str, List[float]] = {}
        self.total_position_history: List[int] = []
        self.total_pnl_history: List[float] = []
        self.volume_history: Dict[str, List[int]] = {}
        self.bid_price_history: Dict[str, List[float]] = {}
        self.ask_price_history: Dict[str, List[float]] = {}
        self.mid_price_history: Dict[str, List[float]] = {}
        
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
                    trades = self._process_orders(orders, ts)
                    if trades:
                        executed_trades[product] = trades
            
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
            listings[product] = Listing(
                symbol=product,
                product=product,
                denomination='DOLLARS'
            )
            
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
    
    def _process_orders(self, orders: List[Order], timestamp: int) -> List[Trade]:
        """Process a list of orders and return executed trades."""
        executed_trades = []
        
        for order in orders:
            if not isinstance(order, Order):
                continue
                
            if order.symbol not in self.order_books:
                continue
                
            order_book = self.order_books[order.symbol]
            
            if order.is_buy:
                # Process buy order
                best_ask, best_ask_qty = order_book.get_best_ask()
                if best_ask is not None and order.price >= best_ask:
                    # Calculate execution price and quantity
                    price = best_ask
                    quantity = min(order.abs_quantity, best_ask_qty)
                    
                    # Create trade
                    trade = Trade(
                        symbol=order.symbol,
                        price=price,
                        quantity=quantity,
                        buyer="TRADER",
                        seller="MARKET",
                        timestamp=timestamp
                    )
                    executed_trades.append(trade)
                    
                    # Update order book
                    order_book.remove_sell_order(price, quantity)
                    
            else:  # Sell order
                best_bid, best_bid_qty = order_book.get_best_bid()
                if best_bid is not None and order.price <= best_bid:
                    # Calculate execution price and quantity
                    price = best_bid
                    quantity = min(order.abs_quantity, best_bid_qty)
                    
                    # Create trade
                    trade = Trade(
                        symbol=order.symbol,
                        price=price,
                        quantity=-quantity,  # Negative for sell
                        buyer="MARKET",
                        seller="TRADER",
                        timestamp=timestamp
                    )
                    executed_trades.append(trade)
                    
                    # Update order book
                    order_book.remove_buy_order(price, quantity)
        
        return executed_trades
    
    def _update_history(self, timestamp: int, executed_trades: Dict[str, List[Trade]]) -> None:
        """Update historical data with the current state."""
        # Update positions and PnL based on executed trades
        for product, trades in executed_trades.items():
            for trade in trades:
                # Update position
                position_delta = trade.quantity
                self.positions[product] = self.positions.get(product, 0) + position_delta
        
        # Update timestamp
        self.timestamps.append(timestamp)
        
        # Update history for each product
        for product in self.positions.keys():
            # Update position history
            if product not in self.position_history:
                self.position_history[product] = []
            self.position_history[product].append(self.positions[product])
            
            # Update PnL history (simplified)
            if product not in self.pnl_history:
                self.pnl_history[product] = []
            
            # For simplicity, just track the current position value as PnL
            if product in self.order_books:
                order_book = self.order_books[product]
                mid_price = order_book.get_mid_price()
                if mid_price is not None:
                    self.pnls[product] = self.positions[product] * mid_price
                    self.pnl_history[product].append(self.pnls[product])
            
            # Update volume history
            if product not in self.volume_history:
                self.volume_history[product] = []
            
            # Calculate total volume for this timestamp
            volume = 0
            if timestamp in self.trades and product in self.trades[timestamp]:
                for trade in self.trades[timestamp][product]:
                    volume += abs(trade.quantity)
            self.volume_history[product].append(volume)
            
            # Update price history
            if product in self.order_books:
                order_book = self.order_books[product]
                best_bid, _ = order_book.get_best_bid()
                best_ask, _ = order_book.get_best_ask()
                
                if best_bid is not None:
                    if product not in self.bid_price_history:
                        self.bid_price_history[product] = []
                    self.bid_price_history[product].append(best_bid)
                
                if best_ask is not None:
                    if product not in self.ask_price_history:
                        self.ask_price_history[product] = []
                    self.ask_price_history[product].append(best_ask)
                
                # Calculate mid price
                if best_bid is not None and best_ask is not None:
                    mid_price = (best_bid + best_ask) / 2
                    if product not in self.mid_price_history:
                        self.mid_price_history[product] = []
                    self.mid_price_history[product].append(mid_price)
        
        # Update total position and PnL
        self.total_position_history.append(sum(self.positions.values()))
        self.total_pnl_history.append(sum(self.pnls.values()))
        self.pnl = sum(self.pnls.values())
    
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
