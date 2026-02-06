from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
import psutil
import pyqtgraph as pg
import numpy as np

from qfluentwidgets import (
    CardWidget, CaptionLabel, StrongBodyLabel, InfoBar, 
    InfoBarPosition, ProgressBar
)

# --- jarvis Knight Theme Constants ---
THEME_GLASS = "rgba(16, 24, 40, 0.75)" 
THEME_BORDER = "rgba(76, 201, 240, 0.3)" 
THEME_ACCENT = "#4cc9f0"
THEME_TEXT_MAIN = "#e8f1ff"
THEME_TEXT_SUB = "#94a3b8"

# Try to import pynvml for GPU monitoring
try:
    import pynvml
    pynvml.nvmlInit()
    GPU_AVAILABLE = True
except Exception:
    GPU_AVAILABLE = False

class SentinalGraph(QFrame):
    """A styled graph card using pyqtgraph."""
    def __init__(self, title, color=THEME_ACCENT, parent=None):
        super().__init__(parent)
        self.setObjectName("SentinelCard")
        self.setStyleSheet(f"""
            QFrame#SentinelCard {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        header = QHBoxLayout()
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 10px; font-weight: bold; letter-spacing: 1.5px;")
        self.value_label = QLabel("0%")
        self.value_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 900;")
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.value_label)
        layout.addLayout(header)

        # Plot Widget
        self.pw = pg.PlotWidget()
        self.pw.setBackground(None)
        self.pw.setMouseEnabled(x=False, y=False)
        self.pw.hideAxis('bottom')
        self.pw.hideAxis('left')
        
        # Transparent background for plot
        self.pw.getViewBox().setMenuEnabled(False)
        
        self.curve = self.pw.plot(pen=pg.mkPen(color, width=2))
        # Fill under curve
        self.curve.setBrush(pg.mkBrush(color + "40")) # Transparent fill
        self.curve.setFillLevel(0)
        
        self.data = np.zeros(100)
        layout.addWidget(self.pw)

    def update_data(self, value, val_text=None):
        self.data[:-1] = self.data[1:]
        self.data[-1] = value
        self.curve.setData(self.data)
        if val_text:
            self.value_label.setText(val_text)
        else:
            self.value_label.setText(f"{value:.1f}%")

class ProcessList(QFrame):
    """Top consuming processes list."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
                padding: 10px;
            }}
            QLabel#procHeader {{
                color: {THEME_ACCENT};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QLabel#procItem {{
                color: {THEME_TEXT_MAIN};
                font-size: 12px;
                font-family: 'Consolas';
            }}
        """)
        layout = QVBoxLayout(self)
        header = QLabel("HOLOGRAPHIC PROCESS OVERWATCH")
        header.setObjectName("procHeader")
        layout.addWidget(header)
        
        self.items = []
        for _ in range(5):
            lbl = QLabel("--")
            lbl.setObjectName("procItem")
            self.items.append(lbl)
            layout.addWidget(lbl)
            
    def update_processes(self):
        try:
            procs = sorted(psutil.process_iter(['name', 'cpu_percent', 'memory_percent']), 
                           key=lambda x: x.info['cpu_percent'], reverse=True)[:5]
            for i, p in enumerate(procs):
                if i < len(self.items):
                    name = p.info['name'][:18]
                    cpu = p.info['cpu_percent']
                    mem = p.info['memory_percent']
                    self.items[i].setText(f"{name:<20} CPU: {cpu:>4.1f}% | MEM: {mem:>4.1f}%")
        except: pass

class SentinelTab(QWidget):
    """
    Sentinel: Advanced System Telemetry Dashboard.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SentinelTab")
        self._setup_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_stats)
        self.timer.start(2000) # Slightly slower refresh for efficiency
        
        # Track network history
        self.last_net = psutil.net_io_counters()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # Header
        header_layout = QHBoxLayout()
        titles_layout = QVBoxLayout()
        title = QLabel("SENTINEL OVERWATCH")
        title.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {THEME_TEXT_MAIN}; letter-spacing: 3px;")
        subtitle = QLabel("HARDWARE TELEMETRY CORE")
        subtitle.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 10px; font-weight: bold; letter-spacing: 1.5px;")
        titles_layout.addWidget(title)
        titles_layout.addWidget(subtitle)
        header_layout.addLayout(titles_layout)
        header_layout.addStretch()
        
        # Status Badge
        status_badge = QLabel("• SYSTEM STABLE")
        status_badge.setStyleSheet(f"""
            color: #81c784; 
            border: 1px solid rgba(129, 199, 132, 0.4);
            border-radius: 10px;
            padding: 4px 12px;
            font-size: 10px;
            font-weight: bold;
        """)
        header_layout.addWidget(status_badge, 0, Qt.AlignTop)
        
        layout.addLayout(header_layout)

        # Scroll Area for Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(container)
        self.grid.setSpacing(15)

        # Main Performance Graphs (Top Row)
        self.cpu_graph = SentinalGraph("CPU Cluster Usage")
        self.ram_graph = SentinalGraph("Physical Memory", color="#ffb74d")
        self.gpu_graph = SentinalGraph("GPU Neural Load", color=THEME_ACCENT)
        self.vram_graph = SentinalGraph("VRAM Allocation", color="#90caf9")
        
        self.grid.addWidget(self.cpu_graph, 0, 0)
        self.grid.addWidget(self.ram_graph, 0, 1)
        self.grid.addWidget(self.gpu_graph, 1, 0)
        self.grid.addWidget(self.vram_graph, 1, 1)

        # Bottom Section
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(15)
        
        # Network velocity group
        net_card = QFrame()
        net_card.setStyleSheet(f"background-color: {THEME_GLASS}; border: 1px solid {THEME_BORDER}; border-radius: 12px;")
        net_layout = QVBoxLayout(net_card)
        net_layout.addWidget(QLabel("NETWORK FLUX"))
        self.net_down_graph = SentinalGraph("Downlink", color="#81c784")
        self.net_up_graph = SentinalGraph("Uplink", color="#ef5350")
        net_layout.addWidget(self.net_down_graph)
        net_layout.addWidget(self.net_up_graph)
        bottom_row.addWidget(net_card, 1)
        
        # Processes list
        self.proc_list = ProcessList()
        bottom_row.addWidget(self.proc_list, 1)
        
        self.grid.addLayout(bottom_row, 2, 0, 1, 2)

        # Storage Panel
        storage_panel = QFrame()
        storage_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        sp_layout = QVBoxLayout(storage_panel)
        header = QLabel("STORAGE NODES")
        header.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 11px; font-weight: bold;")
        sp_layout.addWidget(header)
        
        disks = psutil.disk_partitions(all=False)
        for disk in disks[:3]:
            try:
                usage = psutil.disk_usage(disk.mountpoint)
                bar_container = QVBoxLayout()
                label_layout = QHBoxLayout()
                label_layout.addWidget(CaptionLabel(f"{disk.mountpoint} ({disk.device})"))
                label_layout.addStretch()
                label_layout.addWidget(CaptionLabel(f"{usage.percent}%"))
                bar_container.addLayout(label_layout)
                
                bar = ProgressBar()
                bar.setValue(int(usage.percent))
                bar_container.addWidget(bar)
                sp_layout.addLayout(bar_container)
            except: pass
                
        self.grid.addWidget(storage_panel, 3, 0, 1, 2)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _update_stats(self):
        # CPU
        self.cpu_graph.update_data(psutil.cpu_percent())
        
        # RAM
        ram = psutil.virtual_memory()
        self.ram_graph.update_data(ram.percent, f"{ram.used / (1024**3):.1f} / {ram.total / (1024**3):.1f} GB")
        
        # GPU
        if GPU_AVAILABLE:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                self.gpu_graph.update_data(util.gpu)
                self.vram_graph.update_data((mem.used / mem.total) * 100, f"{mem.used / (1024**3):.1f} / {mem.total / (1024**3):.1f} GB")
            except: pass
        
        # Network
        net = psutil.net_io_counters()
        up = (net.bytes_sent - self.last_net.bytes_sent) / (1024 * 1024) / 2 # /2 for 2s interval
        down = (net.bytes_recv - self.last_net.bytes_recv) / (1024 * 1024) / 2
        self.last_net = net
        
        self.net_up_graph.update_data(min(up * 10, 100), f"{up:.2f} MB/s")
        self.net_down_graph.update_data(min(down * 10, 100), f"{down:.2f} MB/s")
        
        # Processes
        self.proc_list.update_processes()
