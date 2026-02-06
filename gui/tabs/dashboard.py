from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QGridLayout, QPushButton, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QDate, QTime, QSize, Signal, QThread, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QLinearGradient, QGradient

from qfluentwidgets import (
    CardWidget, TitleLabel, BodyLabel, StrongBodyLabel, 
    FluentIcon as FIF, IconWidget, TransparentToolButton,
    SimpleCardWidget, ImageLabel, PillToolButton
)

from core.tasks import task_manager
from core.calendar_manager import calendar_manager
from core.kasa_control import kasa_manager
from core.weather import weather_manager
from datetime import datetime, timedelta
import asyncio

# --- Wolf Knight Theme Constants ---
# Colors
THEME_BG = "#05080d"  # Deepest background
THEME_GLASS = "rgba(16, 24, 40, 0.70)" # Main glass card background
THEME_BORDER = "rgba(76, 201, 240, 0.3)" # Neon Cyan/Silver border
THEME_ACCENT = "#4cc9f0" # Neon Cyan
THEME_TEXT_MAIN = "#e8f1ff" # Ghost White
THEME_TEXT_SUB = "#94a3b8" # Silver Grey
THEME_GLOW = "rgba(76, 201, 240, 0.15)" # Glow color

class GlowEffect(QGraphicsDropShadowEffect):
    """Custom glow effect for UI elements."""
    def __init__(self, color=THEME_ACCENT, blur=15, parent=None):
        super().__init__(parent)
        self.setBlurRadius(blur)
        self.setColor(QColor(color))
        self.setOffset(0, 0)

class GreetingsHeader(QWidget):
    """
    Holographic HUD Header.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 20)
        self.layout.setSpacing(20)
        
        # --- Left: Holographic Date/Greeting ---
        text_container = QFrame()
        text_container.setStyleSheet("background: transparent;")
        tc_layout = QVBoxLayout(text_container)
        tc_layout.setContentsMargins(0,0,0,0)
        tc_layout.setSpacing(0)
        
        self.greeting_lbl = QLabel("SYSTEM ONLINE")
        self.greeting_lbl.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 14px; letter-spacing: 2px; color: {THEME_ACCENT}; font-weight: bold;")
        
        self.main_title = QLabel("COMMANDER")
        self.main_title.setStyleSheet(f"font-family: 'Segoe UI'; font-size: 48px; font-weight: 800; color: {THEME_TEXT_MAIN};")
        # Add glow to title
        shadow = GlowEffect(THEME_ACCENT, 20)
        self.main_title.setGraphicsEffect(shadow)
        
        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 16px; font-family: 'Consolas', monospace;")
        
        tc_layout.addWidget(self.greeting_lbl)
        tc_layout.addWidget(self.main_title)
        tc_layout.addWidget(self.date_lbl)
        
        self.layout.addWidget(text_container)
        self.layout.addStretch()
        
        # --- Right: HUD Rings (Time | Weather) ---
        hud_layout = QHBoxLayout()
        hud_layout.setSpacing(20)
        
        # Time HUD
        self.time_hud = self._create_hud_circle()
        self.clock_lbl = QLabel("--:--")
        self.clock_lbl.setAlignment(Qt.AlignCenter)
        self.clock_lbl.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {THEME_TEXT_MAIN}; background: transparent;")
        
        # Sub-label for AM/PM
        self.ampm_lbl = QLabel("--")
        self.ampm_lbl.setAlignment(Qt.AlignCenter)
        self.ampm_lbl.setStyleSheet(f"font-size: 10px; color: {THEME_ACCENT}; font-weight: bold; background: transparent;")
        
        t_layout = QVBoxLayout(self.time_hud)
        t_layout.setAlignment(Qt.AlignCenter)
        t_layout.setSpacing(0)
        t_layout.addWidget(self.clock_lbl)
        t_layout.addWidget(self.ampm_lbl)
        
        hud_layout.addWidget(self.time_hud)
        
        # Weather HUD
        self.weather_hud = self._create_hud_circle()
        
        self.w_icon = QLabel("...")
        self.w_icon.setAlignment(Qt.AlignCenter)
        self.w_icon.setStyleSheet("font-size: 22px; background: transparent;")
        
        self.w_temp = QLabel("--°")
        self.w_temp.setAlignment(Qt.AlignCenter)
        self.w_temp.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {THEME_TEXT_MAIN}; background: transparent;")
        
        w_layout = QVBoxLayout(self.weather_hud)
        w_layout.setAlignment(Qt.AlignCenter)
        w_layout.setSpacing(2)
        w_layout.addWidget(self.w_icon)
        w_layout.addWidget(self.w_temp)
        
        hud_layout.addWidget(self.weather_hud)
        
        self.layout.addLayout(hud_layout)
        
        # Timers
        self._update_time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
        
        self._fetch_weather()
        self.w_timer = QTimer(self)
        self.w_timer.timeout.connect(self._fetch_weather)
        self.w_timer.start(900000)

    def _create_hud_circle(self):
        frame = QFrame()
        frame.setFixedSize(110, 110)
        # Circular silver/cyan border with glass background
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(10, 15, 30, 0.6);
                border: 2px solid {THEME_BORDER};
                border-radius: 55px;
            }}
        """)
        # Add glow
        glow = GlowEffect(THEME_ACCENT, 30)
        frame.setGraphicsEffect(glow)
        return frame

    def _update_time(self):
        now = datetime.now()
        hour = now.hour
        
        # Greeting update
        if 5 <= hour < 12: greeting = "GOOD MORNING"
        elif 12 <= hour < 18: greeting = "GOOD AFTERNOON"
        else: greeting = "GOOD EVENING"
        self.greeting_lbl.setText(f"// {greeting}")
        
        # Date & Time
        self.date_lbl.setText(QDate.currentDate().toString("yyyy.MM.dd  |  dddd").upper())
        self.clock_lbl.setText(QTime.currentTime().toString("h:mm"))
        self.ampm_lbl.setText(QTime.currentTime().toString("AP"))

    def _fetch_weather(self):
        self._thread = QThread()
        self._worker = WeatherWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_weather_loaded)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_weather_loaded(self, data):
        if not data: return
        temp = data['temp']
        code = data['code']
        self.w_temp.setText(f"{int(temp)}°")
        
        # Weather Codes
        if code == 0: icon = "☀️"
        elif code in [1, 2, 3]: icon = "⛅"
        elif code in [45, 48]: icon = "🌫️"
        elif code in [51, 53, 55, 61]: icon = "🌧️"
        elif code in [71, 73, 85]: icon = "❄️"
        elif code >= 95: icon = "⚡"
        else: icon = "🌡️"
        self.w_icon.setText(icon)

class WeatherWorker(QThread):
    finished = Signal(dict)
    def run(self):
        data = weather_manager.get_weather()
        self.finished.emit(data or {})

from core.gamification import game_manager
from qfluentwidgets import ProgressBar

class LevelingCard(QFrame):
    """
    HUD for XP and Level.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(260, 100)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Header: Level
        top = QHBoxLayout()
        self.lvl_lbl = QLabel("LEVEL 1")
        self.lvl_lbl.setStyleSheet(f"color: {THEME_TEXT_MAIN}; font-weight: 800; font-size: 14px; letter-spacing: 1px;")
        
        self.xp_text = QLabel("0 / 100 XP")
        self.xp_text.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 10px;")
        
        top.addWidget(self.lvl_lbl)
        top.addStretch()
        top.addWidget(self.xp_text)
        layout.addLayout(top)
        
        # XP Bar
        self.progress = ProgressBar()
        self.progress.setFixedHeight(4)
        layout.addWidget(self.progress)
        
        # Rank
        self.rank_lbl = QLabel("Wolf PUP PROTOCOL")
        self.rank_lbl.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 9px; font-weight: bold; letter-spacing: 2px;")
        layout.addWidget(self.rank_lbl)

    def update_stats(self, data):
        lvl = data.get('level', 1)
        xp = data.get('xp', 0)
        next_xp = data.get('xp_to_next', 100)
        prog = data.get('progress', 0)
        
        self.lvl_lbl.setText(f"LEVEL {lvl}")
        self.xp_text.setText(f"{xp} / {next_xp} XP")
        self.progress.setValue(int(prog))
        
        ranks = ["PUP", "SCOUT", "HUNTER", "WARRIOR", "ALPHA", "FENRIR"]
        idx = min(lvl // 5, len(ranks)-1)
        self.rank_lbl.setText(f"{ranks[idx]} PROTOCOL")

class StatCard(QFrame):
    """
    Glass card with neon silver borders.
    """
    navigate_requested = Signal(str)
    
    def __init__(self, icon: FIF, title: str, count: str, route_key: str = None, parent=None):
        super().__init__(parent)
        self.setFixedSize(260, 100)
        self.route_key = route_key
        if route_key:
            self.setCursor(Qt.PointingHandCursor)
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: rgba(20, 30, 50, 0.9);
                border: 1px solid {THEME_ACCENT};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Left: Icon & Label
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignVCenter)
        left_layout.setSpacing(5)
        
        # Icon Container (No background, just colored icon)
        iw = IconWidget(icon)
        iw.setFixedSize(24, 24)
        left_layout.addWidget(iw)
        
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 10px; font-weight: bold; letter-spacing: 1px; background: transparent; border: none;")
        left_layout.addWidget(lbl)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # Right: Count
        self.num_label = QLabel(str(count))
        self.num_label.setStyleSheet(f"font-size: 32px; font-weight: 300; color: {THEME_TEXT_MAIN}; background: transparent; border: none;")
        layout.addWidget(self.num_label)

    def set_count(self, count):
        self.num_label.setText(str(count))
        
    def mousePressEvent(self, event):
        if self.route_key:
            self.navigate_requested.emit(self.route_key)

class HomeScenesCard(QFrame):
    """
    Rune-like buttons for scene control.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(260, 140)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 12px;
            }}
        """)
        self._devices = []
        self._action_thread = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        title = QLabel("PROTOCOL OVERRIDE")
        title.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 10px; font-weight: bold; letter-spacing: 1px; border: none; background: transparent;")
        layout.addWidget(title)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.focus_btn = self._create_rune_btn("FOCUS")
        self.focus_btn.clicked.connect(self._on_focus_mode)
        
        self.relax_btn = self._create_rune_btn("RELAX")
        self.relax_btn.clicked.connect(self._on_relax_mode)
        
        btn_layout.addWidget(self.focus_btn)
        btn_layout.addWidget(self.relax_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        status = QLabel("Awaiting Command...")
        status.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 10px; border: none; background: transparent; font-style: italic;")
        layout.addWidget(status)
        
    def _create_rune_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedHeight(40)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(76, 201, 240, 0.1);
                border: 1px solid {THEME_BORDER};
                color: {THEME_TEXT_MAIN};
                border-radius: 4px;
                font-weight: bold;
                font-family: 'Segoe UI';
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {THEME_ACCENT};
                color: #000;
                border: 1px solid {THEME_ACCENT};
            }}
        """)
        return btn

    def set_devices(self, devices: list):
        self._devices = devices
    
    def _on_focus_mode(self):
        if not self._devices: return
        self._run_scene_action(self._focus_action)
        
    def _on_relax_mode(self):
        if not self._devices: return
        self._run_scene_action(self._relax_action)
        
    def _run_scene_action(self, action_func):
        class SceneThread(QThread):
            def __init__(self, func):
                super().__init__()
                self.func = func
            def run(self):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.func())
                    loop.close()
                except Exception as e:
                    print(f"Scene error: {e}")
        
        if self._action_thread and self._action_thread.isRunning():
            self._action_thread.wait()
        self._action_thread = SceneThread(action_func)
        self._action_thread.start()

    async def _focus_action(self):
        for device in self._devices:
            dev_obj = device.get('obj')
            await kasa_manager.turn_off(device['ip'], dev=dev_obj)

    async def _relax_action(self):
        for device in self._devices:
            dev_obj = device.get('obj')
            if device.get('brightness') is not None:
                await kasa_manager.set_brightness(device['ip'], 40, dev=dev_obj)
                await kasa_manager.turn_on(device['ip'], dev=dev_obj)
            else:
                await kasa_manager.turn_on(device['ip'], dev=dev_obj)

class IntelligenceItem(QFrame):
    """Row in Intelligence Feed - Holographic list item."""
    def __init__(self, icon: FIF, title: str, description: str, time_str: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(15)
        
        # Hexagonal Icon mock (using styled label)
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"background-color: rgba(76, 201, 240, 0.1); border-radius: 16px; color: {THEME_ACCENT};")
        # Can't put icon in label easy, use IconWidget next to it or overlay
        # Simpler: just use IconWidget directly
        
        iw = IconWidget(icon)
        iw.setFixedSize(18, 18)
        
        # Container for icon to center it
        ic_cont = QFrame()
        ic_cont.setFixedSize(32, 32)
        ic_cont.setStyleSheet(f"background-color: rgba(20, 30, 50, 0.8); border: 1px solid {THEME_BORDER}; border-radius: 16px;")
        ic_layout = QVBoxLayout(ic_cont)
        ic_layout.setAlignment(Qt.AlignCenter)
        ic_layout.setContentsMargins(0,0,0,0)
        ic_layout.addWidget(iw)
        
        layout.addWidget(ic_cont)
        
        # Content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        
        top = QHBoxLayout()
        t = QLabel(title.upper())
        t.setStyleSheet(f"color: {THEME_TEXT_MAIN}; font-weight: bold; font-size: 12px; letter-spacing: 0.5px;")
        
        tm = QLabel(time_str)
        tm.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 10px; font-family: 'Consolas', monospace;")
        
        top.addWidget(t)
        top.addStretch()
        top.addWidget(tm)
        
        d = QLabel(description)
        d.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 12px;")
        d.setWordWrap(True)
        
        text_layout.addLayout(top)
        text_layout.addWidget(d)
        
        layout.addLayout(text_layout)

    def update_content(self, title: str, description: str, time_str: str):
        # We need to access labels, but I didn't save them as attributes in this quick implementation.
        # Let's fix that.
        self.findChild(QLabel, "").setText(title.upper()) # This is risky.
        # Re-implementation for proper updates:
        pass

class IntelligenceFeed(QFrame):
    """
    Vertical 'Holographic Projection' Feed.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(5, 8, 13, 0.4);
                border-left: 1px solid {THEME_BORDER};
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 20, 30, 30)
        self.layout.setSpacing(20)
        
        # Header
        h_layout = QHBoxLayout()
        h_lbl = QLabel("INTELLIGENCE FEED")
        h_lbl.setStyleSheet(f"color: {THEME_TEXT_MAIN}; font-weight: bold; font-size: 14px; letter-spacing: 2px;")
        
        live = QLabel("● LIVE")
        live.setStyleSheet("color: #ff3b30; font-weight: bold; font-size: 10px; font-family: 'Consolas', monospace;")
        # Blink effect could go here
        
        h_layout.addWidget(h_lbl)
        h_layout.addStretch()
        h_layout.addWidget(live)
        self.layout.addLayout(h_layout)
        

        # 2. Daily Focus
        self.focus_item = self._create_item(FIF.TILES, "MISSION OBJECTIVES", "Analyzing daily schedule protocols...", "SYNCING")
        self.layout.addWidget(self.focus_item)
        
        # 3. IOT
        self.dev_item = self._create_item(FIF.IOT, "CONNECTED ASSETS", "Ping network for active nodes...", "SCANNING")
        self.layout.addWidget(self.dev_item)
        
        self.layout.addStretch()
        
        # Priority Card
        self.priority = PriorityCard()
        self.layout.addWidget(self.priority)

    def _create_item(self, icon, title, desc, time):
        item = IntelligenceItem(icon, title, desc, time)
        return item
        
    # Helpers to update content safely
    def _update_item_widgets(self, item, title, desc, time):
        # IntelligenceItem internal structure extraction logic
        # Since I defined it dynamically above, I'll access layout items.
        # [0] is Icon, [1] is Text Layout. Text Layout [0] is Top Row (Title, Time), [1] is Desc.
        
        text_layout = item.layout().itemAt(1).layout()
        
        title_lbl = text_layout.itemAt(0).layout().itemAt(0).widget()
        time_lbl = text_layout.itemAt(0).layout().itemAt(2).widget()
        desc_lbl = text_layout.itemAt(1).widget()
        
        title_lbl.setText(title.upper())
        time_lbl.setText(time)
        desc_lbl.setText(desc)

    def update_devices(self, devices):
        c = len(devices)
        active = sum(1 for d in devices if d.get('is_on'))
        msg = f"{c} Nodes detected. {active} Active." if c > 0 else "No nodes detected."
        self._update_item_widgets(self.dev_item, "NETWORK STATUS", msg, "ONLINE")
        
    def update_focus(self, tasks):
        active = [t for t in tasks if not t.get('completed')]
        msg = f"{len(active)} pending objectives." if active else "All objectives complete."
        self._update_item_widgets(self.focus_item, "CURRENT OBJECTIVES", msg, "ACTIVE")


class PriorityCard(QFrame):
    """
    Glowing bottom card for next event.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(110)
        # Deep blue gradient with glow
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(5, 20, 50, 0.9), stop:1 rgba(10, 10, 20, 0.9));
                border: 1px solid {THEME_ACCENT};
                border-radius: 16px;
            }}
        """)
        # Strong glow effect
        glow = GlowEffect(THEME_ACCENT, 25)
        self.setGraphicsEffect(glow)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        
        content = QVBoxLayout()
        content.setSpacing(4)
        
        lbl = QLabel("NEXT PRIORITY")
        lbl.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 10px; font-weight: bold; letter-spacing: 2px; background: transparent; border: none;")
        
        self.title_lbl = QLabel("NO PENDING EVENTS")
        self.title_lbl.setStyleSheet(f"color: {THEME_TEXT_MAIN}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        
        self.time_lbl = QLabel("Standby mode engaged")
        self.time_lbl.setStyleSheet(f"color: {THEME_TEXT_SUB}; font-size: 12px; background: transparent; border: none;")
        
        content.addWidget(lbl)
        content.addWidget(self.title_lbl)
        content.addWidget(self.time_lbl)
        
        layout.addLayout(content)
        layout.addStretch()
        
        # Action Button
        btn = QPushButton("DETAILS")
        btn.setFixedSize(90, 36)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(76, 201, 240, 0.2);
                border: 1px solid {THEME_ACCENT};
                color: {THEME_TEXT_MAIN};
                border-radius: 8px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {THEME_ACCENT};
                color: #05080d;
            }}
        """)
        layout.addWidget(btn)

    def update_event(self, events: list):
        now = datetime.now()
        next_event = None
        for event in events:
            try:
                st = datetime.strptime(event['start_time'], "%Y-%m-%d %H:%M:%S")
                if st > now:
                    if next_event is None or st < datetime.strptime(next_event['start_time'], "%Y-%m-%d %H:%M:%S"):
                        next_event = event
            except: continue
            
        if next_event:
            self.title_lbl.setText(next_event['title'])
            st = datetime.strptime(next_event['start_time'], "%Y-%m-%d %H:%M:%S")
            delta = st - now
            mins = int(delta.total_seconds() / 60)
            formatted_time = f"T-MINUS {mins} MINUTES" if mins < 60 else f"T-MINUS {mins//60} HOURS"
            self.time_lbl.setText(formatted_time)
        else:
            self.title_lbl.setText("NO PENDING EVENTS")
            self.time_lbl.setText("Schedule clear.")


class DashboardLoader(QThread):
    finished = Signal(dict)
    def run(self):
        try:
            tasks = task_manager.get_tasks()
            
            devices = []
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                d = loop.run_until_complete(kasa_manager.discover_devices())
                loop.close()
                devices = list(d.values()) if isinstance(d, dict) else d
            except: pass
            
            today = datetime.now().strftime("%Y-%m-%d")
            events = calendar_manager.get_events(today)
            
            self.finished.emit({"tasks": tasks, "devices": devices, "events": events})
        except:
            self.finished.emit({})

class DashboardView(QWidget):
    navigate_to = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardView")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Background gradient setup done in main window stylesheet or here
        # For the 'spectral Wolf' feel, we might want a background image or specific gradient
        # But global styles handle the window bg. We'll handle layout here.
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 0, 0) # Right margin 0 for full flush feed
        main_layout.setSpacing(30)
        
        # 1. Header
        self.header = GreetingsHeader()
        main_layout.addWidget(self.header)
        
        # 2. Content Area
        content = QHBoxLayout()
        content.setSpacing(40)
        
        # -- Left Col (Cards) --
        left = QVBoxLayout()
        left.setSpacing(25)
        
        self.planner_stat = StatCard(FIF.CALENDAR, "Agenda Status", "--", "plannerInterface")
        self.planner_stat.navigate_requested.connect(self._on_navigate)
        left.addWidget(self.planner_stat)
        
        self.device_stat = StatCard(FIF.IOT, "Network Nodes", "--", "homeInterface")
        self.device_stat.navigate_requested.connect(self._on_navigate)
        left.addWidget(self.device_stat)
        
        self.leveling_hud = LevelingCard()
        left.addWidget(self.leveling_hud)
        # Initial stats
        game_manager.stats_updated.connect(self.leveling_hud.update_stats)
        
        self.scenes = HomeScenesCard()
        left.addWidget(self.scenes)
        
        left.addStretch()
        content.addLayout(left)
        
        # -- Right Col (Feed) --
        self.feed = IntelligenceFeed()
        content.addWidget(self.feed, 1) # Expand to fill rest
        
        main_layout.addLayout(content)
        
        self.loader = None
        QTimer.singleShot(100, self._start_loading)
        

    def _start_loading(self):
        if self.loader and self.loader.isRunning(): return
        self.loader = DashboardLoader(self)
        self.loader.finished.connect(self._on_data)
        self.loader.finished.connect(self.loader.deleteLater)
        self.loader.start()
        # Trigger XP sync
        game_manager._save_stats()
        
    def _on_data(self, data):
        if not data: return
        tasks = data.get('tasks', [])
        devs = data.get('devices', [])
        evts = data.get('events', [])
        
        self.scenes.set_devices(devs)
        
        act_tasks = len([t for t in tasks if not t.get('completed')])
        self.planner_stat.set_count(act_tasks)
        self.device_stat.set_count(len(devs))
        
        self.feed.update_devices(devs)
        self.feed.update_focus(tasks)
        self.feed.priority.update_event(evts)
        
    def _on_navigate(self, key):
        self.navigate_to.emit(key)

