# doc_id: DOC-LEGACY-0071
# DOC_ID: DOC-LEGACY-0007
# tkinter_dashboard_gui.py - Integration with your existing tkinter GUI
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

from dashboard_backend import (
    DashboardEngine, DashboardFactory, IndicatorRegistry, 
    SignalStrength, IndicatorCategory, BaseIndicator
)

class SignalCell(ttk.Frame):
    """Individual signal cell widget with color coding"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.signal_var = tk.StringVar()
        self.confidence_var = tk.StringVar()
        
        # Create label for signal
        self.signal_label = ttk.Label(
            self, 
            textvariable=self.signal_var,
            width=8,
            anchor='center',
            font=('Arial', 8, 'bold')
        )
        self.signal_label.pack(fill='both', expand=True)
        
        # Store current signal for color updates
        self.current_signal = SignalStrength.NO_SIGNAL
        self.update_display()
    
    def set_signal(self, signal: SignalStrength, confidence: float = 0):
        """Update signal display"""
        self.current_signal = signal
        
        # Abbreviated signal names for compact display
        signal_map = {
            SignalStrength.STRONG_BUY: "S.BUY",
            SignalStrength.WEAK_BUY: "W.BUY",
            SignalStrength.NO_SIGNAL: "---",
            SignalStrength.WEAK_SELL: "W.SELL",
            SignalStrength.STRONG_SELL: "S.SELL"
        }
        
        self.signal_var.set(signal_map.get(signal, "---"))
        self.confidence_var.set(f"{confidence:.0f}%")
        self.update_display()
    
    def update_display(self):
        """Update colors based on signal"""
        color_map = {
            SignalStrength.STRONG_BUY: {'bg': '#006400', 'fg': 'white'},  # Dark green
            SignalStrength.WEAK_BUY: {'bg': '#32CD32', 'fg': 'black'},   # Light green
            SignalStrength.NO_SIGNAL: {'bg': '#D3D3D3', 'fg': 'black'},   # Gray
            SignalStrength.WEAK_SELL: {'bg': '#FF6347', 'fg': 'black'},   # Light red
            SignalStrength.STRONG_SELL: {'bg': '#8B0000', 'fg': 'white'}  # Dark red
        }
        
        colors = color_map.get(self.current_signal, {'bg': '#D3D3D3', 'fg': 'black'})
        self.signal_label.configure(background=colors['bg'], foreground=colors['fg'])

class ProgressBarCell(ttk.Frame):
    """Progress bar for confidence display"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.progress = ttk.Progressbar(
            self, 
            mode='determinate',
            length=100,
            style='Custom.Horizontal.TProgressbar'
        )
        self.progress.pack(fill='both', expand=True, padx=2, pady=2)
        
        self.confidence_label = ttk.Label(self, text="0%", font=('Arial', 8))
        self.confidence_label.pack()
        
        self.setup_styles()
    
    def setup_styles(self):
        """Setup custom progress bar styles"""
        style = ttk.Style()
        
        # Green for bullish
        style.configure(
            'Bullish.Horizontal.TProgressbar',
            background='#32CD32'
        )
        
        # Red for bearish  
        style.configure(
            'Bearish.Horizontal.TProgressbar',
            background='#FF6347'
        )
        
        # Gray for neutral
        style.configure(
            'Neutral.Horizontal.TProgressbar',
            background='#D3D3D3'
        )
    
    def set_confidence(self, confidence: float, signal_type: str = 'neutral'):
        """Update confidence display"""
        self.progress['value'] = confidence
        self.confidence_label.config(text=f"{confidence:.0f}%")
        
        # Change style based on signal type
        style_map = {
            'bullish': 'Bullish.Horizontal.TProgressbar',
            'bearish': 'Bearish.Horizontal.TProgressbar',
            'neutral': 'Neutral.Horizontal.TProgressbar'
        }
        
        self.progress.configure(style=style_map.get(signal_type, 'Neutral.Horizontal.TProgressbar'))

class DashboardTab(ttk.Frame):
    """Main dashboard tab for your trading interface"""
    
    def __init__(self, parent, dde_client=None, price_manager=None):
        super().__init__(parent)
        
        # Initialize dashboard engine
        self.dashboard_engine = DashboardFactory.create_forex_dashboard()
        self.dde_client = dde_client
        self.price_manager = price_manager
        
        # GUI state
        self.signal_cells = {}  # symbol_timeframe_indicator -> SignalCell
        self.summary_cells = {}  # symbol_timeframe -> SignalCell
        self.confidence_bars = {}  # symbol_timeframe -> ProgressBarCell
        self.selected_timeframe = tk.StringVar(value='M15')
        
        # Update queue for thread-safe GUI updates
        self.update_queue = queue.Queue()
        
        self.setup_ui()
        self.start_background_updates()
    
    def setup_ui(self):
        """Setup the main dashboard UI"""
        # Create main container with paned window
        main_paned = ttk.PanedWindow(self, orient='vertical')
        main_paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Top section: Controls and summary
        self.create_controls_section(main_paned)
        
        # Middle section: Signal matrix
        self.create_signal_matrix(main_paned)
        
        # Bottom section: Overall market summary
        self.create_market_summary(main_paned)
        
        # Start processing updates
        self.process_updates()
    
    def create_controls_section(self, parent):
        """Create control panel section"""
        controls_frame = ttk.LabelFrame(parent, text="Dashboard Controls")
        parent.add(controls_frame, minsize=80)
        
        # Timeframe selection
        tf_frame = ttk.Frame(controls_frame)
        tf_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(tf_frame, text="Timeframe:").pack(side='left')
        
        timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
        for tf in timeframes:
            btn = ttk.Radiobutton(
                tf_frame, 
                text=tf, 
                variable=self.selected_timeframe,
                value=tf,
                command=self.on_timeframe_changed
            )
            btn.pack(side='left', padx=2)
        
        # Control buttons
        btn_frame = ttk.Frame(controls_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Add Indicator", command=self.show_add_indicator_dialog).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Remove Indicator", command=self.show_remove_indicator_dialog).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Settings", command=self.show_settings_dialog).pack(side='left', padx=2)
        
        # Status indicator
        self.status_var = tk.StringVar(value="Initializing...")
        ttk.Label(btn_frame, textvariable=self.status_var).pack(side='right')
    
    def create_signal_matrix(self, parent):
        """Create the main signal matrix display"""
        matrix_frame = ttk.LabelFrame(parent, text="Signal Matrix")
        parent.add(matrix_frame, minsize=400)
        
        # Create scrollable frame
        canvas = tk.Canvas(matrix_frame)
        scrollbar = ttk.Scrollbar(matrix_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Build matrix table
        self.build_matrix_table()
    
    def build_matrix_table(self):
        """Build the signal matrix table"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.signal_cells.clear()
        self.summary_cells.clear()
        self.confidence_bars.clear()
        
        symbols = self.dashboard_engine.symbols
        indicators = list(self.dashboard_engine.registry._indicators.keys())
        
        # Create headers
        headers = ['Symbol'] + indicators + ['Summary', 'Confidence']
        for col, header in enumerate(headers):
            label = ttk.Label(
                self.scrollable_frame, 
                text=header, 
                font=('Arial', 9, 'bold'),
                anchor='center'
            )
            label.grid(row=0, column=col, padx=1, pady=1, sticky='ew')
        
        # Create matrix cells
        for row, symbol in enumerate(symbols, 1):
            # Symbol label
            symbol_label = ttk.Label(
                self.scrollable_frame, 
                text=symbol,
                font=('Arial', 9, 'bold'),
                anchor='center'
            )
            symbol_label.grid(row=row, column=0, padx=1, pady=1, sticky='ew')
            
            # Indicator signal cells
            for col, indicator in enumerate(indicators, 1):
                cell = SignalCell(self.scrollable_frame)
                cell.grid(row=row, column=col, padx=1, pady=1, sticky='ew')
                
                key = f"{symbol}_{self.selected_timeframe.get()}_{indicator}"
                self.signal_cells[key] = cell
            
            # Summary cell
            summary_cell = SignalCell(self.scrollable_frame)
            summary_cell.grid(row=row, column=len(indicators)+1, padx=1, pady=1, sticky='ew')
            
            summary_key = f"{symbol}_{self.selected_timeframe.get()}"
            self.summary_cells[summary_key] = summary_cell
            
            # Confidence bar
            confidence_bar = ProgressBarCell(self.scrollable_frame)
            confidence_bar.grid(row=row, column=len(indicators)+2, padx=1, pady=1, sticky='ew')
            self.confidence_bars[summary_key] = confidence_bar
        
        # Configure column weights
        for col in range(len(headers)):
            self.scrollable_frame.columnconfigure(col, weight=1)
    
    def create_market_summary(self, parent):
        """Create overall market summary section"""
        summary_frame = ttk.LabelFrame(parent, text="Market Summary")
        parent.add(summary_frame, minsize=100)
        
        # Create summary widgets
        summary_container = ttk.Frame(summary_frame)
        summary_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Overall bias indicators
        ttk.Label(summary_container, text="Short-term Bias:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w')
        self.short_term_var = tk.StringVar(value="Neutral")
        ttk.Label(summary_container, textvariable=self.short_term_var, font=('Arial', 10)).grid(row=0, column=1, sticky='w')
        
        ttk.Label(summary_container, text="Long-term Bias:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w')
        self.long_term_var = tk.StringVar(value="Neutral")
        ttk.Label(summary_container, textvariable=self.long_term_var, font=('Arial', 10)).grid(row=1, column=1, sticky='w')
        
        # Signal counts
        ttk.Label(summary_container, text="Total Buy Signals:", font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky='w', padx=(20,0))
        self.buy_count_var = tk.StringVar(value="0")
        ttk.Label(summary_container, textvariable=self.buy_count_var, font=('Arial', 10), foreground='green').grid(row=0, column=3, sticky='w')
        
        ttk.Label(summary_container, text="Total Sell Signals:", font=('Arial', 10, 'bold')).grid(row=1, column=2, sticky='w', padx=(20,0))
        self.sell_count_var = tk.StringVar(value="0")
        ttk.Label(summary_container, textvariable=self.sell_count_var, font=('Arial', 10), foreground='red').grid(row=1, column=3, sticky='w')
        
        # Last update time
        ttk.Label(summary_container, text="Last Update:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky='w')
        self.last_update_var = tk.StringVar(value="Never")
        ttk.Label(summary_container, textvariable=self.last_update_var, font=('Arial', 10)).grid(row=2, column=1, sticky='w')
    
    def on_timeframe_changed(self):
        """Handle timeframe selection change"""
        self.build_matrix_table()
        self.status_var.set(f"Switched to {self.selected_timeframe.get()}")
    
    def show_add_indicator_dialog(self):
        """Show dialog to add new indicator"""
        dialog = IndicatorDialog(self, self.dashboard_engine.registry, mode='add')
        self.wait_window(dialog)
        
        if dialog.result:
            symbol, timeframe, indicator, config = dialog.result
            try:
                self.dashboard_engine.add_indicator(symbol, timeframe, indicator, **config)
                self.build_matrix_table()
                self.status_var.set(f"Added {indicator} for {symbol} {timeframe}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add indicator: {e}")
    
    def show_remove_indicator_dialog(self):
        """Show dialog to remove indicator"""
        dialog = IndicatorDialog(self, self.dashboard_engine.registry, mode='remove')
        self.wait_window(dialog)
        
        if dialog.result:
            symbol, timeframe, indicator, _ = dialog.result
            try:
                self.dashboard_engine.remove_indicator(symbol, timeframe, indicator)
                self.build_matrix_table()
                self.status_var.set(f"Removed {indicator} for {symbol} {timeframe}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove indicator: {e}")
    
    def show_settings_dialog(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self, self.dashboard_engine)
        self.wait_window(dialog)
    
    def start_background_updates(self):
        """Start background thread for dashboard updates"""
        def update_worker():
            while True:
                try:
                    # Get latest dashboard data
                    data = self.dashboard_engine.get_dashboard_data()
                    
                    # Queue update for main thread
                    self.update_queue.put(('dashboard_update', data))
                    
                    time.sleep(self.dashboard_engine.update_interval)
                except Exception as e:
                    self.update_queue.put(('error', str(e)))
                    time.sleep(1)
        
        # Start dashboard engine updates
        self.dashboard_engine.start_real_time_updates()
        
        # Start GUI update worker
        update_thread = threading.Thread(target=update_worker, daemon=True)
        update_thread.start()
    
    def process_updates(self):
        """Process updates from background thread"""
        try:
            while True:
                try:
                    update_type, data = self.update_queue.get_nowait()
                    
                    if update_type == 'dashboard_update':
                        self.update_dashboard_display(data)
                    elif update_type == 'error':
                        self.status_var.set(f"Error: {data}")
                        
                except queue.Empty:
                    break
        
        except Exception as e:
            print(f"Error processing updates: {e}")
        
        # Schedule next update check
        self.after(1000, self.process_updates)  # Check every second
    
    def update_dashboard_display(self, data):
        """Update the dashboard display with new data"""
        signal_matrix = data.get('signal_matrix', {})
        summary_data = data.get('summary_data', {})
        last_update = data.get('last_update', '')
        
        current_tf = self.selected_timeframe.get()
        total_buy = 0
        total_sell = 0
        
        # Update signal cells
        for symbol in self.dashboard_engine.symbols:
            if symbol in signal_matrix and current_tf in signal_matrix[symbol]:
                symbol_signals = signal_matrix[symbol][current_tf]
                
                # Update individual indicator cells
                for indicator, signal_str in symbol_signals.items():
                    cell_key = f"{symbol}_{current_tf}_{indicator}"
                    if cell_key in self.signal_cells:
                        try:
                            signal = SignalStrength(signal_str)
                            self.signal_cells[cell_key].set_signal(signal)
                        except (ValueError, KeyError):
                            pass  # Handle invalid signal values
                
                # Update summary cell
                summary_key = f"{symbol}_{current_tf}"
                if summary_key in summary_data[symbol]:
                    summary_info = summary_data[symbol][summary_key]
                    
                    if summary_key in self.summary_cells:
                        try:
                            summary_signal = SignalStrength(summary_info['summary'])
                            confidence = summary_info['confidence']
                            
                            self.summary_cells[summary_key].set_signal(summary_signal, confidence)
                            
                            # Update confidence bar
                            if summary_key in self.confidence_bars:
                                signal_type = 'bullish' if 'Buy' in summary_info['summary'] else 'bearish' if 'Sell' in summary_info['summary'] else 'neutral'
                                self.confidence_bars[summary_key].set_confidence(confidence, signal_type)
                            
                            # Count signals for overall summary
                            total_buy += summary_info.get('buy_signals', 0)
                            total_sell += summary_info.get('sell_signals', 0)
                            
                        except (ValueError, KeyError):
                            pass
        
        # Update overall market summary
        self.buy_count_var.set(str(total_buy))
        self.sell_count_var.set(str(total_sell))
        self.last_update_var.set(datetime.now().strftime("%H:%M:%S"))
        
        # Determine overall bias
        if total_buy > total_sell * 1.5:
            self.short_term_var.set("Bullish")
        elif total_sell > total_buy * 1.5:
            self.short_term_var.set("Bearish")
        else:
            self.short_term_var.set("Neutral")
        
        self.status_var.set(f"Updated at {datetime.now().strftime('%H:%M:%S')}")


class IndicatorDialog(tk.Toplevel):
    """Dialog for adding/removing indicators"""
    
    def __init__(self, parent, indicator_registry: IndicatorRegistry, mode='add'):
        super().__init__(parent)
        self.registry = indicator_registry
        self.mode = mode
        self.result = None
        
        self.title(f"{mode.title()} Indicator")
        self.geometry("400x300")
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        # Center on parent
        self.center_on_parent(parent)
    
    def setup_ui(self):
        """Setup dialog UI"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Symbol selection
        ttk.Label(main_frame, text="Symbol:").grid(row=0, column=0, sticky='w', pady=2)
        self.symbol_var = tk.StringVar()
        symbol_combo = ttk.Combobox(main_frame, textvariable=self.symbol_var, state='readonly')
        symbol_combo['values'] = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
        symbol_combo.grid(row=0, column=1, sticky='ew', pady=2)
        symbol_combo.current(0)
        
        # Timeframe selection
        ttk.Label(main_frame, text="Timeframe:").grid(row=1, column=0, sticky='w', pady=2)
        self.timeframe_var = tk.StringVar()
        tf_combo = ttk.Combobox(main_frame, textvariable=self.timeframe_var, state='readonly')
        tf_combo['values'] = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
        tf_combo.grid(row=1, column=1, sticky='ew', pady=2)
        tf_combo.current(2)  # Default to M15
        
        # Indicator selection
        ttk.Label(main_frame, text="Indicator:").grid(row=2, column=0, sticky='w', pady=2)
        self.indicator_var = tk.StringVar()
        indicator_combo = ttk.Combobox(main_frame, textvariable=self.indicator_var, state='readonly')
        indicator_combo['values'] = list(self.registry._indicators.keys())
        indicator_combo.grid(row=2, column=1, sticky='ew', pady=2)
        indicator_combo.bind('<<ComboboxSelected>>', self.on_indicator_selected)
        
        # Configuration frame (for indicator parameters)
        self.config_frame = ttk.LabelFrame(main_frame, text="Configuration")
        self.config_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)
        
        self.config_vars = {}
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side='left', padx=5)
        
        # Configure column weights
        main_frame.columnconfigure(1, weight=1)
    
    def on_indicator_selected(self, event=None):
        """Handle indicator selection to show configuration options"""
        # Clear existing config widgets
        for widget in self.config_frame.winfo_children():
            widget.destroy()
        
        self.config_vars.clear()
        
        indicator_name = self.indicator_var.get()
        if not indicator_name:
            return
        
        # Get indicator class to inspect parameters
        indicator_class = self.registry._indicators.get(indicator_name)
        if not indicator_class:
            return
        
        # Create temporary instance to get default config
        try:
            temp_instance = indicator_class("TEMP", "M15")
            config = temp_instance.config
            
            row = 0
            for param, default_value in config.items():
                ttk.Label(self.config_frame, text=f"{param}:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
                
                var = tk.StringVar(value=str(default_value))
                entry = ttk.Entry(self.config_frame, textvariable=var)
                entry.grid(row=row, column=1, sticky='ew', padx=5, pady=2)
                
                self.config_vars[param] = var
                row += 1
            
            self.config_frame.columnconfigure(1, weight=1)
            
        except Exception as e:
            ttk.Label(self.config_frame, text=f"Error loading config: {e}").pack()
    
    def on_ok(self):
        """Handle OK button"""
        if not all([self.symbol_var.get(), self.timeframe_var.get(), self.indicator_var.get()]):
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        # Collect configuration
        config = {}
        for param, var in self.config_vars.items():
            try:
                value = var.get()
                # Try to convert to appropriate type
                if value.isdigit():
                    config[param] = int(value)
                elif '.' in value and value.replace('.', '').isdigit():
                    config[param] = float(value)
                else:
                    config[param] = value
            except ValueError:
                config[param] = value
        
        self.result = (
            self.symbol_var.get(),
            self.timeframe_var.get(),
            self.indicator_var.get(),
            config
        )
        self.destroy()
    
    def on_cancel(self):
        """Handle Cancel button"""
        self.destroy()
    
    def center_on_parent(self, parent):
        """Center dialog on parent window"""
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")


class SettingsDialog(tk.Toplevel):
    """Settings dialog for dashboard configuration"""
    
    def __init__(self, parent, dashboard_engine: DashboardEngine):
        super().__init__(parent)
        self.engine = dashboard_engine
        
        self.title("Dashboard Settings")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        self.center_on_parent(parent)
    
    def setup_ui(self):
        """Setup settings UI"""
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # General settings tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        
        self.setup_general_settings(general_frame)
        
        # Indicators tab
        indicators_frame = ttk.Frame(notebook)
        notebook.add(indicators_frame, text="Indicators")
        
        self.setup_indicators_settings(indicators_frame)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Apply", command=self.on_apply).pack(side='left', padx=5)
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side='left', padx=5)
    
    def setup_general_settings(self, parent):
        """Setup general settings tab"""
        # Update interval
        ttk.Label(parent, text="Update Interval (seconds):").grid(row=0, column=0, sticky='w', pady=5)
        self.update_interval_var = tk.StringVar(value=str(self.engine.update_interval))
        ttk.Entry(parent, textvariable=self.update_interval_var).grid(row=0, column=1, sticky='ew', pady=5)
        
        # ADX weight
        ttk.Label(parent, text="ADX Weight Multiplier:").grid(row=1, column=0, sticky='w', pady=5)
        self.adx_weight_var = tk.StringVar(value=str(self.engine.aggregator.adx_weight))
        ttk.Entry(parent, textvariable=self.adx_weight_var).grid(row=1, column=1, sticky='ew', pady=5)
        
        # Configure column weights
        parent.columnconfigure(1, weight=1)
    
    def setup_indicators_settings(self, parent):
        """Setup indicators settings tab"""
        # Available indicators list
        ttk.Label(parent, text="Available Indicators:").pack(anchor='w')
        
        # Create treeview for indicators
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, pady=5)
        
        self.indicators_tree = ttk.Treeview(tree_frame, columns=('category', 'status'), show='tree headings')
        self.indicators_tree.heading('#0', text='Indicator')
        self.indicators_tree.heading('category', text='Category')
        self.indicators_tree.heading('status', text='Status')
        
        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.indicators_tree.yview)
        self.indicators_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.indicators_tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')
        
        # Populate indicators tree
        self.populate_indicators_tree()
        
        # Indicator control buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text="Enable All", command=self.enable_all_indicators).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Disable All", command=self.disable_all_indicators).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Load Plugin", command=self.load_plugin).pack(side='left', padx=2)
    
    def populate_indicators_tree(self):
        """Populate the indicators tree with current indicators"""
        # Clear existing items
        for item in self.indicators_tree.get_children():
            self.indicators_tree.delete(item)
        
        # Group indicators by category
        available_indicators = self.engine.registry.get_available_indicators()
        
        for category, indicators in available_indicators.items():
            category_node = self.indicators_tree.insert('', 'end', text=category.value.title())
            
            for indicator in indicators:
                # Check if indicator is active
                active_count = sum(1 for key in self.engine.active_indicators.keys() if indicator in key)
                status = f"Active ({active_count})" if active_count > 0 else "Inactive"
                
                self.indicators_tree.insert(
                    category_node, 'end',
                    text=indicator,
                    values=(category.value, status)
                )
    
    def enable_all_indicators(self):
        """Enable all indicators for all symbols/timeframes"""
        for symbol in self.engine.symbols:
            for timeframe in self.engine.timeframes:
                for indicator_name in self.engine.registry._indicators.keys():
                    if f"{symbol}_{timeframe}_{indicator_name}" not in self.engine.active_indicators:
                        try:
                            self.engine.add_indicator(symbol, timeframe, indicator_name)
                        except Exception as e:
                            print(f"Error adding {indicator_name}: {e}")
        
        self.populate_indicators_tree()
    
    def disable_all_indicators(self):
        """Disable all indicators"""
        indicators_to_remove = list(self.engine.active_indicators.keys())
        for key in indicators_to_remove:
            parts = key.split('_')
            if len(parts) >= 3:
                symbol = parts[0]
                timeframe = parts[1]
                indicator = '_'.join(parts[2:])
                try:
                    self.engine.remove_indicator(symbol, timeframe, indicator)
                except Exception as e:
                    print(f"Error removing {indicator}: {e}")
        
        self.populate_indicators_tree()
    
    def load_plugin(self):
        """Load indicator plugin from file"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Select Indicator Plugin",
            filetypes=[("Python files", "*.py")]
        )
        
        if file_path:
            try:
                # This would implement plugin loading logic
                messagebox.showinfo("Success", f"Plugin loaded from {file_path}")
                self.populate_indicators_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load plugin: {e}")
    
    def on_apply(self):
        """Apply settings without closing dialog"""
        try:
            # Apply update interval
            new_interval = int(self.update_interval_var.get())
            self.engine.update_interval = new_interval
            
            # Apply ADX weight
            new_weight = float(self.adx_weight_var.get())
            self.engine.aggregator.adx_weight = new_weight
            
            messagebox.showinfo("Success", "Settings applied successfully")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid setting value: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
    
    def on_ok(self):
        """Apply settings and close dialog"""
        self.on_apply()
        self.destroy()
    
    def on_cancel(self):
        """Close dialog without applying settings"""
        self.destroy()
    
    def center_on_parent(self, parent):
        """Center dialog on parent window"""
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")


# Integration with your existing main application
class MainApplicationIntegration:
    """Integration helper for adding dashboard to existing application"""
    
    @staticmethod
    def add_dashboard_tab(notebook_widget, dde_client=None, price_manager=None):
        """Add dashboard tab to existing notebook widget"""
        dashboard_tab = DashboardTab(notebook_widget, dde_client, price_manager)
        notebook_widget.add(dashboard_tab, text="Trading Dashboard")
        return dashboard_tab
    
    @staticmethod
    def create_standalone_dashboard():
        """Create standalone dashboard window"""
        root = tk.Tk()
        root.title("Trading Signals Dashboard")
        root.geometry("1400x800")
        
        # Create dashboard
        dashboard = DashboardTab(root)
        dashboard.pack(fill='both', expand=True)
        
        return root, dashboard


# Example usage
def main():
    """Example of how to use the dashboard GUI"""
    
    # Option 1: Standalone dashboard
    root, dashboard = MainApplicationIntegration.create_standalone_dashboard()
    
    # Option 2: Add to existing notebook (commented out)
    # existing_notebook = ttk.Notebook(root)
    # dashboard_tab = MainApplicationIntegration.add_dashboard_tab(existing_notebook)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        dashboard.dashboard_engine.stop_real_time_updates()
        root.quit()


if __name__ == "__main__":
    main()