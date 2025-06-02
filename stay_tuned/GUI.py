import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import importlib.util
import traceback
import threading
import webbrowser
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
import numpy as np

from stuff.backtester_module import Backtester
from stuff.trade import Trade, Order
from stuff.order_book import OrderBook
from stuff.trading_state import TradingState

class ModernBacktesterGUI:
    def __init__(self, root):
        self.root = root
        root.title("Advanced Backtester Pro")
        root.geometry("1200x800")
        
        # Configure dark theme
        self.setup_dark_theme()
        
        self.price_file = ""
        self.trades_file = ""
        self.algo_file = ""
        self.backtester = None
        
        # Create main layout
        self.create_widgets()
        
    def setup_dark_theme(self):
        """Configure dark theme colors and styles"""
        self.colors = {
            'bg_primary': '#1e1e1e',
            'bg_secondary': '#2d2d2d',
            'bg_tertiary': '#3d3d3d',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0b0',
            'accent': '#007acc',
            'success': '#4caf50',
            'warning': '#ff9800',
            'error': '#f44336'
        }
        
        # Configure root
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button style
        style.configure('Dark.TButton',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       focuscolor='none',
                       relief='flat')
        style.map('Dark.TButton',
                 background=[('active', self.colors['accent']),
                           ('pressed', self.colors['bg_secondary'])])
        
        # Configure frame style
        style.configure('Dark.TFrame',
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        # Configure label style
        style.configure('Dark.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Header.TLabel',
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=('Arial', 12, 'bold'))
        
        # Configure progressbar
        style.configure('Dark.Horizontal.TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['bg_secondary'])
    
    def create_widgets(self):
        """Create and layout all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="🚀 Advanced Backtester Pro", 
                               style='Header.TLabel')
        title_label.pack()
        
        # File loading section
        files_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        files_frame.pack(fill='x', pady=(0, 20))
        
        files_label = ttk.Label(files_frame, text="📁 Data Files", style='Header.TLabel')
        files_label.pack(anchor='w')
        
        # File buttons frame
        buttons_frame = ttk.Frame(files_frame, style='Dark.TFrame')
        buttons_frame.pack(fill='x', pady=(10, 0))
        
        # File loading buttons
        self.price_btn = ttk.Button(buttons_frame, text="📊 Load Price Data", 
                                   command=self.load_price, style='Dark.TButton')
        self.price_btn.pack(side='left', padx=(0, 10))
        
        self.trades_btn = ttk.Button(buttons_frame, text="💱 Load Trades Data", 
                                    command=self.load_trades, style='Dark.TButton')
        self.trades_btn.pack(side='left', padx=(0, 10))
        
        self.algo_btn = ttk.Button(buttons_frame, text="🧠 Load Strategy", 
                                  command=self.load_algo, style='Dark.TButton')
        self.algo_btn.pack(side='left', padx=(0, 10))
        
        # Run button
        self.run_btn = ttk.Button(buttons_frame, text="🚀 Run Backtest", 
                                 command=self.run_backtest_threaded, style='Dark.TButton')
        self.run_btn.pack(side='left', padx=(20, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(buttons_frame, style='Dark.Horizontal.TProgressbar', 
                                       mode='indeterminate')
        self.progress.pack(side='right', padx=(10, 0))
        
        # Status section
        status_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        status_frame.pack(fill='x', pady=(0, 20))
        
        status_label = ttk.Label(status_frame, text="📋 Status & Logs", style='Header.TLabel')
        status_label.pack(anchor='w')
        
        # Output text with scrollbar
        text_frame = tk.Frame(status_frame, bg=self.colors['bg_primary'])
        text_frame.pack(fill='x', pady=(10, 0))
        
        self.output_text = tk.Text(text_frame, height=8, width=80,
                                  bg=self.colors['bg_secondary'],
                                  fg=self.colors['text_primary'],
                                  insertbackground=self.colors['text_primary'],
                                  selectbackground=self.colors['accent'],
                                  font=('Consolas', 9),
                                  relief='flat',
                                  borderwidth=1)
        
        scrollbar = tk.Scrollbar(text_frame, bg=self.colors['bg_tertiary'])
        scrollbar.pack(side='right', fill='y')
        self.output_text.pack(side='left', fill='both', expand=True)
        self.output_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output_text.yview)
        
        # Results section
        results_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        results_frame.pack(fill='both', expand=True)
        
        results_label = ttk.Label(results_frame, text="📈 Interactive Results", style='Header.TLabel')
        results_label.pack(anchor='w')
        
        # Results buttons
        viz_buttons_frame = ttk.Frame(results_frame, style='Dark.TFrame')
        viz_buttons_frame.pack(fill='x', pady=(10, 0))
        
        self.interactive_btn = ttk.Button(viz_buttons_frame, text="📊 Open Interactive Dashboard", 
                                         command=self.open_interactive_plot, style='Dark.TButton',
                                         state='disabled')
        self.interactive_btn.pack(side='left', padx=(0, 10))
        
        self.summary_btn = ttk.Button(viz_buttons_frame, text="📋 Performance Summary", 
                                     command=self.show_summary, style='Dark.TButton',
                                     state='disabled')
        self.summary_btn.pack(side='left', padx=(0, 10))
        
        self.export_btn = ttk.Button(viz_buttons_frame, text="💾 Export Results", 
                                    command=self.export_results, style='Dark.TButton',
                                    state='disabled')
        self.export_btn.pack(side='left')
        
        # Quick stats frame
        self.stats_frame = ttk.Frame(results_frame, style='Dark.TFrame')
        self.stats_frame.pack(fill='x', pady=(10, 0))
        
        self.quick_stats_label = ttk.Label(self.stats_frame, text="📊 Run a backtest to see results", 
                                          style='Dark.TLabel')
        self.quick_stats_label.pack(anchor='w')
        
        # File status labels
        self.create_status_labels(files_frame)
        
        # Keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Initial log message
        self.log_message("🌟 Welcome to Advanced Backtester Pro!")
        self.log_message("💡 Load your data files and strategy to get started.")
        
    def update_quick_stats(self):
        """Update the quick stats label with multi-product information"""
        if not self.backtester:
            return
        
        # Get products from backtester
        products = list(self.backtester.pnls.keys())
        
        # Format overall PnL and position information
        total_pnl = self.backtester.pnl
        
        # Create the stats text
        stats_text = f"💰 TOTAL PnL: ${total_pnl:,.2f}   |   "
        
        # Add per-product information
        for product in products:
            product_pnl = self.backtester.pnls[product]
            product_position = self.backtester.positions[product]
            stats_text += f"{product}: ${product_pnl:,.2f} (Pos: {product_position})   |   "
        
        # Remove the last separator
        stats_text = stats_text.rstrip("   |   ")
        
        # Update the label
        self.quick_stats_label.config(text=stats_text)
        self.log_message("⌨️  Keyboard shortcuts: Ctrl+O (Open files), Ctrl+R (Run), Ctrl+S (Summary)")
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        self.root.bind('<Control-r>', lambda e: self.run_backtest_threaded())
        self.root.bind('<Control-s>', lambda e: self.show_summary() if self.backtester else None)
        self.root.bind('<Control-d>', lambda e: self.open_interactive_plot() if self.backtester else None)
        self.root.bind('<F5>', lambda e: self.run_backtest_threaded())
        self.root.bind('<Escape>', lambda e: self.root.quit())
    
    def create_status_labels(self, parent):
        """Create file status indicators"""
        status_frame = ttk.Frame(parent, style='Dark.TFrame')
        status_frame.pack(fill='x', pady=(10, 0))
        
        self.price_status = ttk.Label(status_frame, text="❌ Price data: Not loaded", 
                                     style='Dark.TLabel')
        self.price_status.pack(anchor='w')
        
        self.trades_status = ttk.Label(status_frame, text="❌ Trades data: Not loaded", 
                                      style='Dark.TLabel')
        self.trades_status.pack(anchor='w')
        
        self.algo_status = ttk.Label(status_frame, text="❌ Strategy: Not loaded", 
                                    style='Dark.TLabel')
        self.algo_status.pack(anchor='w')
    
    def log_message(self, message, level='info'):
        """Add timestamped message to output text"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == 'error':
            icon = "❌"
        elif level == 'success':
            icon = "✅"
        elif level == 'warning':
            icon = "⚠️"
        else:
            icon = "ℹ️"
        
        formatted_message = f"[{timestamp}] {icon} {message}\n"
        
        self.output_text.insert(tk.END, formatted_message)
        self.output_text.see(tk.END)
        self.root.update()
    
    def load_price(self):
        self.price_file = filedialog.askopenfilename(
            title="Select Price Data CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if self.price_file:
            self.log_message(f"Price data loaded: {self.price_file.split('/')[-1]}", 'success')
            self.price_status.config(text=f"✅ Price data: {self.price_file.split('/')[-1]}")
        
    def load_trades(self):
        self.trades_file = filedialog.askopenfilename(
            title="Select Trades Data CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if self.trades_file:
            self.log_message(f"Trades data loaded: {self.trades_file.split('/')[-1]}", 'success')
            self.trades_status.config(text=f"✅ Trades data: {self.trades_file.split('/')[-1]}")
    
    def load_algo(self):
        self.algo_file = filedialog.askopenfilename(
            title="Select Strategy Python File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if self.algo_file:
            self.log_message(f"Strategy loaded: {self.algo_file.split('/')[-1]}", 'success')
            self.algo_status.config(text=f"✅ Strategy: {self.algo_file.split('/')[-1]}")
    
    def run_backtest_threaded(self):
        """Run backtest in separate thread to prevent GUI freezing"""
        if not self.price_file or not self.trades_file or not self.algo_file:
            messagebox.showerror("Missing Files", "Please load all required files first")
            return
        
        # Start progress animation
        self.progress.start(10)
        self.run_btn.config(state='disabled')
        
        # Run in separate thread
        thread = threading.Thread(target=self.run_backtest)
        thread.daemon = True
        thread.start()
    
    def run_backtest(self):
        """Execute the backtest"""
        try:
            self.log_message("🚀 Starting backtest execution...")
            
            # Load strategy module
            spec = importlib.util.spec_from_file_location("strategy", self.algo_file)
            strategy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(strategy)
            trader = strategy.Trader()
            
            self.log_message("✅ Strategy module loaded successfully")
            
            # Initialize backtester
            self.backtester = Backtester(self.price_file, self.trades_file, trader)
            self.log_message("📊 Running backtest simulation...")
            
            # Run backtest
            self.backtester.run()
            
            # Log results
            self.log_message("🎉 Backtest completed successfully!", 'success')
            
            # Log total results
            self.log_message(f"💰 Final Total PnL: ${self.backtester.pnl:.2f}")
            
            # Log per-product results
            products = list(self.backtester.pnls.keys())
            for product in products:
                product_position = self.backtester.positions.get(product, 0)
                product_pnl = self.backtester.pnls.get(product, 0)
                self.log_message(f"📊 {product} Position: {product_position} | PnL: ${product_pnl:.2f}")
            
            # Enable visualization buttons
            self.interactive_btn.config(state='normal')
            self.summary_btn.config(state='normal')
            self.export_btn.config(state='normal')
            
            # Update quick stats
            self.update_quick_stats()
            
        except Exception as e:
            self.log_message("❌ Error during backtest execution:", 'error')
            self.log_message(str(e), 'error')
            self.log_message(traceback.format_exc())
        
        # Stop progress animation
        self.progress.stop()
        self.run_btn.config(state='normal')
    
    def log_message(self, message, level='info'):
        """Log a message to the output text widget"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Set icon based on message level
        if level == 'error':
            icon = "❌"
        elif level == 'warning':
            icon = "⚠️"
        elif level == 'success':
            icon = "✅"
        else:
            icon = "ℹ️"
        
        formatted_message = f"[{timestamp}] {icon} {message}\n"
        
        self.output_text.insert(tk.END, formatted_message)
        self.output_text.see(tk.END)
        self.root.update()
    
    def export_results(self):
        """Export backtest results to CSV with multi-product support"""
        if not self.backtester:
            messagebox.showerror("No Data", "Please run a backtest first")
            return False
        
        try:
            # Ask user for save location
            file_path = filedialog.asksaveasfilename(
                title="Save Results As",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not file_path:
                return False
            
            # Get products from backtester
            products = list(self.backtester.pnls.keys())
            
            # Create DataFrame with results
            data = {'Timestamp': self.backtester.timestamps, 'Total_PnL': self.backtester.total_pnl_history}
            
            # Add product-specific data
            for product in products:
                data[f'{product}_Position'] = self.backtester.position_history[product]
                data[f'{product}_PnL'] = self.backtester.pnl_history[product]
                data[f'{product}_Volume'] = self.backtester.volume_history[product]
                data[f'{product}_MidPrice'] = self.backtester.mid_price_history[product]
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            self.log_message(f"✅ Multi-product results exported to: {file_path.split('/')[-1]}", 'success')
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error exporting results: {str(e)}", 'error')
            return False
    
    def open_interactive_plot(self):
        """Create and open interactive plotly dashboard with separate charts for PnL, volume, and price data"""
        if not self.backtester:
            messagebox.showerror("No Data", "Please run a backtest first")
            return
        
        try:
            self.log_message("🎨 Creating interactive charts...")
                
            # Get products from backtester
            products = list(self.backtester.pnls.keys())
            timestamps = self.backtester.timestamps
                
            # Define colors for each product
            colors = {
                'GOLD': '#FFD700',
                'SILVER': '#C0C0C0',
                'BRONZE': '#CD7F32'
            }
            
            # Create PnL figure (all products + total in one chart)
            pnl_fig = go.Figure()
                
            # Add PnL traces for each product and total
            for product in products:
                color = colors.get(product, '#1f77b4')
                pnl_fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=self.backtester.pnl_history[product],
                    mode='lines',
                    name=f'{product} PnL',
                    line=dict(color=color, width=2),
                    hovertemplate='<b>Timestamp:</b> %{x}<br>' +
                                 f'<b>{product} PnL:</b> %{{y:,.2f}}<br>' +
                                 '<extra></extra>'
                ))
                
            # Add total PnL trace
            pnl_fig.add_trace(go.Scatter(
                x=timestamps,
                y=self.backtester.total_pnl_history,
                mode='lines',
                name='Total PnL',
                line=dict(color='#00FF00', width=3, dash='dash'),
                hovertemplate='<b>Timestamp:</b> %{x}<br>' +
                             '<b>Total PnL:</b> %{y:,.2f}<br>' +
                             '<extra></extra>'
            ))
                
            # Update PnL chart layout
            pnl_fig.update_layout(
                title='Profit & Loss (PnL)',
                xaxis_title='Timestamp',
                yaxis_title='PnL ($)',
                showlegend=True,
                template='plotly_dark',
                height=400
            )
                
            # Create volume figures (one per product)
            volume_figs = {}
            for product in products:
                color = colors.get(product, '#1f77b4')
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=timestamps,
                    y=self.backtester.volume_history[product],
                    name=f'{product} Volume',
                    marker_color=color,
                    opacity=0.8,
                    hovertemplate='<b>Timestamp:</b> %{x}<br>' +
                                 f'<b>Volume:</b> %{{y:,.0f}}<br>' +
                                 '<extra></extra>'
                ))
                fig.update_layout(
                    title=f'{product} Volume Traded',
                    xaxis_title='Timestamp',
                    yaxis_title='Volume',
                    showlegend=False,
                    template='plotly_dark',
                    height=300
                )
                volume_figs[product] = fig
                
            # Create price figures (one per product with bid/ask/mid)
            price_figs = {}
            for product in products:
                color = colors.get(product, '#1f77b4')
                fig = go.Figure()
                    
                # Add bid price
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=self.backtester.bid_price_history[product],
                    mode='lines',
                    name='Bid',
                    line=dict(color='#FF0000', width=1.5),
                    hovertemplate='<b>Bid:</b> %{y:,.2f}<extra></extra>'
                ))
                    
                # Add ask price
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=self.backtester.ask_price_history[product],
                    mode='lines',
                    name='Ask',
                    line=dict(color='#00FF00', width=1.5),
                    hovertemplate='<b>Ask:</b> %{y:,.2f}<extra></extra>'
                ))
                    
                # Add mid price
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=self.backtester.mid_price_history[product],
                    mode='lines',
                    name='Mid',
                    line=dict(color=color, width=2, dash='dash'),
                    hovertemplate='<b>Mid:</b> %{y:,.2f}<extra></extra>'
                ))
                    
                fig.update_layout(
                    title=f'{product} Price Action',
                    xaxis_title='Timestamp',
                    yaxis_title='Price',
                    showlegend=True,
                    template='plotly_dark',
                    height=400,
                    hovermode='x unified'
                )
                price_figs[product] = fig
                
            # Create a single HTML file with all charts
            import os
            import tempfile
            
            # Create a temporary directory for the HTML file
            temp_dir = os.path.join(tempfile.gettempdir(), 'trading_plots')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create the HTML content with all charts
            template = """<!DOCTYPE html>
<html>
<head>
    <title>Trading Dashboard</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #1a1a1a; 
            color: #fff;
        }}
        .chart-container {{ 
            background-color: #2d2d2d; 
            border-radius: 8px; 
            padding: 20px; 
            margin-bottom: 20px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1, h2 {{ 
            color: #4CAF50; 
            text-align: center; 
        }}
        .section {{ 
            margin-bottom: 40px; 
            border-bottom: 1px solid #444; 
            padding-bottom: 20px;
        }}
    </style>
</head>
<body>
    <h1>Trading Dashboard</h1>
    
    <div class="section">
        <h2>Profit & Loss</h2>
        <div class="chart-container">
            {pnl_chart}
        </div>
    </div>
    
    <div class="section">
        <h2>Volume Analysis</h2>
        {volume_charts}
    </div>
    
    <div class="section">
        <h2>Price Action</h2>
        {price_charts}
    </div>
    
    <script>
        // Make all charts responsive
        window.addEventListener('resize', function() {{
            const iframes = document.getElementsByTagName('iframe');
            for (let iframe of iframes) {{
                iframe.style.width = '100%';
            }}
        }});
    </script>
</body>
</html>"""
            
            # Generate PnL chart HTML
            pnl_html = pnl_fig.to_html(full_html=False, include_plotlyjs='cdn')
            
            # Generate volume charts HTML
            volume_charts_html = ''
            for product, fig in volume_figs.items():
                chart_content = fig.to_html(full_html=False, include_plotlyjs=False)
                chart_html = f'''
                <div class="chart-container">
                    <h3>{product} Volume</h3>
                    {chart_content}
                </div>
                '''
                volume_charts_html += chart_html
            
            # Generate price charts HTML
            price_charts_html = ''
            for product, fig in price_figs.items():
                chart_content = fig.to_html(full_html=False, include_plotlyjs=False)
                chart_html = f'''
                <div class="chart-container">
                    <h3>{product} Price Action</h3>
                    {chart_content}
                </div>
                '''
                price_charts_html += chart_html
            
            # Generate the final HTML by formatting the template
            final_html = template.format(
                pnl_chart=pnl_html,
                volume_charts=volume_charts_html,
                price_charts=price_charts_html
            )
            
            # Save the combined HTML file
            dashboard_file = os.path.join(temp_dir, 'trading_dashboard.html')
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                f.write(final_html)
            
            # Open the dashboard in the default web browser
            webbrowser.open(f'file://{os.path.abspath(dashboard_file)}')
            
            self.log_message(f"✅ Interactive dashboard saved to: {os.path.abspath(dashboard_file)}")
            self.log_message("✅ Dashboard opened in your default web browser")
                
        except Exception as e:
            self.log_message(f"❌ Error creating charts: {str(e)}", 'error')
            self.log_message(traceback.format_exc())
    
    def show_summary(self):
        """Show performance summary in a new window with multi-product support"""
        if not self.backtester:
            messagebox.showerror("No Data", "Please run a backtest first")
            return
            
        # Create summary window
        summary_window = tk.Toplevel(self.root)
        summary_window.title("📊 Multi-Product Performance Summary")
        summary_window.geometry("800x700")
        summary_window.configure(bg=self.colors['bg_primary'])
        summary_window.resizable(True, True)
        
        # Make window modal
        summary_window.transient(self.root)
        summary_window.grab_set()
        
        # Get products from backtester
        products = list(self.backtester.pnls.keys())
        
        # Calculate overall metrics
        total_pnls = np.array(self.backtester.total_pnl_history)
        final_total_pnl = self.backtester.pnl
        max_total_pnl = np.max(total_pnls) if len(total_pnls) > 0 else 0
        min_total_pnl = np.min(total_pnls) if len(total_pnls) > 0 else 0
        pnl_volatility = np.std(total_pnls) if len(total_pnls) > 1 else 0
        max_drawdown = max_total_pnl - min_total_pnl if max_total_pnl > min_total_pnl else 0
        
        # Calculate product-specific metrics
        product_metrics = {}
        total_position_changes = 0
        
        for product in products:
            product_positions = np.array(self.backtester.position_history[product])
            product_pnls = np.array(self.backtester.pnl_history[product])
            product_volumes = np.array(self.backtester.volume_history[product])
            
            # Calculate metrics for this product
            max_position = np.max(np.abs(product_positions)) if len(product_positions) > 0 else 0
            final_position = product_positions[-1] if len(product_positions) > 0 else 0
            final_pnl = product_pnls[-1] if len(product_pnls) > 0 else 0
            max_pnl = np.max(product_pnls) if len(product_pnls) > 0 else 0
            min_pnl = np.min(product_pnls) if len(product_pnls) > 0 else 0
            total_volume = np.sum(product_volumes) if len(product_volumes) > 0 else 0
            avg_volume = np.mean(product_volumes) if len(product_volumes) > 0 else 0
            
            # Count position changes for this product
            position_changes = 0
            if len(product_positions) > 1:
                for i in range(1, len(product_positions)):
                    if product_positions[i] != product_positions[i-1]:
                        position_changes += 1
            
            total_position_changes += position_changes
            
            # Store metrics for this product
            product_metrics[product] = {
                'max_position': max_position,
                'final_position': final_position,
                'final_pnl': final_pnl,
                'max_pnl': max_pnl,
                'min_pnl': min_pnl,
                'position_changes': position_changes,
                'total_volume': total_volume,
                'avg_volume': avg_volume
            }
        
        # Create main frame with padding
        main_frame = tk.Frame(summary_window, bg=self.colors['bg_primary'])
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Create a canvas with scrollbar for potentially long content
        canvas = tk.Canvas(main_frame, bg=self.colors['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title frame
        title_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_primary'])
        title_frame.pack(fill='x', pady=(0, 20))
        
        title_label = tk.Label(title_frame, 
                              text="📊 MULTI-PRODUCT BACKTESTING SUMMARY",
                              bg=self.colors['bg_primary'],
                              fg=self.colors['text_primary'],
                              font=('Arial', 14, 'bold'))
        title_label.pack()
        
        # Create overall summary section
        overall_summary = f"""{'='*60}

💰 OVERALL PERFORMANCE:
   • Total Final PnL: ${final_total_pnl:,.2f}
   • Maximum PnL: ${max_total_pnl:,.2f}
   • Minimum PnL: ${min_total_pnl:,.2f}
   • Maximum Drawdown: ${max_drawdown:,.2f}
   • PnL Volatility: ${pnl_volatility:,.2f}
   • Sharpe Ratio: {final_total_pnl / pnl_volatility if pnl_volatility > 0 else 'N/A'}
   • Total Position Changes: {total_position_changes}
   • Position Limit Per Product: ±{self.backtester.POSITION_LIMITS.get('GOLD', 50)}

{'='*60}
"""
        
        # Create product-specific summary sections
        product_summaries = ""
        for product in products:
            metrics = product_metrics[product]
            product_summaries += f"""
📊 {product} METRICS:
   • Final Position: {metrics['final_position']}
   • Maximum Position: {metrics['max_position']}
   • Position Changes: {metrics['position_changes']}
   • Final PnL: ${metrics['final_pnl']:,.2f}
   • Maximum PnL: ${metrics['max_pnl']:,.2f}
   • Minimum PnL: ${metrics['min_pnl']:,.2f}
   • Total Volume: {metrics['total_volume']:,}
   • Average Volume: {metrics['avg_volume']:,.2f}

{'='*60}
"""
        
        # Combine all summary sections
        summary_text = overall_summary + product_summaries + f"""
🎯 SUMMARY:
   {'✅ Profitable Strategy' if final_total_pnl > 0 else '❌ Loss-Making Strategy'}
   {'🎯 Low Risk' if pnl_volatility < abs(final_total_pnl) else '⚠️ High Volatility'}
   • Profit Factor: {(max_total_pnl / abs(min_total_pnl)):,.2f} (if min_total_pnl < 0)

{'='*60}"""
        
        # Create scrollable text frame
        text_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        text_frame.pack(fill='both', expand=True)
        
        # Create text widget with scrollbar
        text_widget = tk.Text(text_frame,
                             bg=self.colors['bg_secondary'],
                             fg=self.colors['text_primary'],
                             font=('Consolas', 9),
                             padx=20, pady=20,
                             wrap=tk.WORD,
                             relief='flat',
                             borderwidth=0,
                             insertbackground=self.colors['text_primary'],
                             selectbackground=self.colors['accent'])
        
        scrollbar = tk.Scrollbar(text_frame, bg=self.colors['bg_tertiary'], 
                                troughcolor=self.colors['bg_secondary'])
        scrollbar.pack(side='right', fill='y')
        text_widget.pack(side='left', fill='both', expand=True)
        
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert('1.0', summary_text)
        text_widget.config(state='disabled')
        
        # Close button frame
        button_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        button_frame.pack(fill='x', pady=(15, 0))
        
        close_btn = tk.Button(button_frame,
                             text="✅ Close",
                             command=summary_window.destroy,
                             bg=self.colors['bg_tertiary'],
                             fg=self.colors['text_primary'],
                             font=('Arial', 10, 'bold'),
                             relief='flat',
                             padx=20, pady=8,
                             cursor='hand2')
        close_btn.pack(side='right')
        
        # Center the window
        summary_window.update_idletasks()
        x = (summary_window.winfo_screenwidth() // 2) - (summary_window.winfo_width() // 2)
        y = (summary_window.winfo_screenheight() // 2) - (summary_window.winfo_height() // 2)
        summary_window.geometry(f"+{x}+{y}")


def main():
    root = tk.Tk()
    app = ModernBacktesterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()