from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QFrame, QFileDialog,
    QStackedWidget, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QUrl, QPropertyAnimation, QEasingCurve, Property, QSize, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtGui import QIcon, QColor, QPainter, QLinearGradient
import hashlib
import random
import threading

from qfluentwidgets import (
    CardWidget, PrimaryPushButton, Slider, CaptionLabel,
    StrongBodyLabel, TransparentToolButton, FluentIcon as FIF,
    SearchLineEdit, ScrollArea
)
from utilities.youtube_handler import YouTubeHandler
from utilities.spotify_handler import SpotifyHandler
from config import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET

# --- Wolf Knight Theme Constants ---
THEME_GLASS = "rgba(16, 24, 40, 0.75)" 
THEME_BORDER = "rgba(76, 201, 240, 0.3)" 
THEME_ACCENT = "#4cc9f0"
THEME_TEXT_MAIN = "#e8f1ff"
THEME_TEXT_SUB = "#94a3b8"

class VisualizerBar(QFrame):
    """A single animating bar for the sonic visualizer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(6, 40)
        self._val_height = 20
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 {THEME_ACCENT}, stop:1 rgba(76, 201, 240, 0.1));
                border-radius: 3px;
            }}
        """)
        
        self.animation = QPropertyAnimation(self, b"animatedHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutSine)

    @Property(int)
    def animatedHeight(self):
        return self.height()

    @animatedHeight.setter
    def animatedHeight(self, h):
        self.setFixedHeight(h)

    def set_target_height(self, h):
        self.animation.stop()
        self.animation.setEndValue(h)
        self.animation.start()

class NeuralCore(QFrame):
    """Pulsing core visualizer for Sonic Interface."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("neuralCore")
        self.setFixedSize(140, 140)
        self._is_pulsing = False
        self._scale = 1.0
        self._dir = 1
        self._pulse_speed = 0.02
        self._interval = 50
        
        # Add glow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(76, 201, 240, 100))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw radial glow
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(76, 201, 240, 150))
        grad.setColorAt(1, QColor(76, 201, 240, 20))
        
        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        
        # Pulse scale
        offset = (self.width() * (1.0 - self._scale)) / 2
        painter.drawEllipse(self.rect().adjusted(int(offset), int(offset), int(-offset), int(-offset)))
        
        # Inner Ring
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QColor(255, 255, 255, 100))
        painter.drawEllipse(self.rect().adjusted(25, 25, -25, -25))

    def set_pulse(self, active):
        self._is_pulsing = active
        if active:
            if not hasattr(self, 'pulse_timer'):
                self.pulse_timer = QTimer(self)
                self.pulse_timer.timeout.connect(self._animate)
                self.pulse_timer.start(self._interval)
        else:
            if hasattr(self, 'pulse_timer'):
                self.pulse_timer.stop()
                del self.pulse_timer
            self._scale = 1.0 # Reset scale when not pulsing
            self.update()

    def set_pulse_speed(self, speed_factor):
        """Adjust pulse speed based on BPM energy (0.5 to 2.0)."""
        self._pulse_speed = 0.01 + (speed_factor * 0.04)
        self._interval = max(20, int(50 / (speed_factor + 0.1)))
        if hasattr(self, 'pulse_timer'):
            self.pulse_timer.setInterval(self._interval)

    def _animate(self):
        self._scale += self._pulse_speed * self._dir
        if self._scale > 1.25: self._dir = -1
        elif self._scale < 0.90: self._dir = 1
        self.update()

class SearchResultCard(CardWidget):
    """A beautiful card representing a YouTube search result."""
    clicked = Slot(dict)

    def __init__(self, track_data, parent=None):
        super().__init__(parent)
        self.track_data = track_data
        self.setFixedHeight(80)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Icon/Thumbnail placeholder
        self.icon_label = QLabel(FIF.VIDEO.icon().pixmap(40, 40), self)
        layout.addWidget(self.icon_label)
        
        # Info
        info_layout = QVBoxLayout()
        self.title_label = StrongBodyLabel(track_data['title'], self)
        self.title_label.setStyleSheet("font-size: 14px;")
        self.uploader_label = CaptionLabel(track_data['uploader'], self)
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.uploader_label)
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # Play Button
        self.play_btn = TransparentToolButton(FIF.PLAY, self)
        self.play_btn.clicked.connect(lambda: self.clicked.emit(self.track_data))
        layout.addWidget(self.play_btn)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.clicked.emit(self.track_data)

class SonicInterface(QWidget):
    """
    Sonic Interface: Unified Media Player with Wolf Knight aesthetic.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MediaTab")
        
        # Audio Engine
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # YouTube Handler
        self.yt_handler = YouTubeHandler()
        
        # Spotify Handler
        self.spotify_handler = SpotifyHandler(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
        self.spotify_synced = False
        
        # BPM / Energy Sync State
        self.current_energy = 1.0 
        self.target_energy = 1.0
        self.bpm_seed = 0.5 
        
        self._setup_ui()
        self._connect_signals()
        
        # Timer for visualizer and progress
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_loop)
        self.update_timer.start(100)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Header
        header_layout = QHBoxLayout()
        titles_layout = QVBoxLayout()
        title = QLabel("SONIC INTERFACE")
        title.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {THEME_TEXT_MAIN}; letter-spacing: 4px;")
        subtitle = QLabel("NEURAL AUDIO FREQUENCY SYNC")
        subtitle.setStyleSheet(f"color: {THEME_ACCENT}; font-size: 11px; font-weight: bold; letter-spacing: 2px;")
        titles_layout.addWidget(title)
        titles_layout.addWidget(subtitle)
        header_layout.addLayout(titles_layout)
        
        header_layout.addStretch()
        
        # YouTube Search
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("Search YouTube Mission Data...")
        self.search_input.setFixedWidth(300)
        self.search_input.searchButton.clicked.connect(self._search_youtube)
        self.search_input.returnPressed.connect(self._search_youtube)
        header_layout.addWidget(self.search_input)
        
        layout.addLayout(header_layout)

        # Main Player Card
        self.player_card = QFrame()
        self.player_card.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_GLASS};
                border: 1px solid {THEME_BORDER};
                border-radius: 24px;
            }}
        """)
        card_layout = QVBoxLayout(self.player_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(30)

        # Player View Container
        self.player_view = QWidget()
        player_view_layout = QVBoxLayout(self.player_view)
        player_view_layout.setContentsMargins(0, 0, 0, 0)
        player_view_layout.setSpacing(30)

        # Visualizer Section
        self.viz_layout = QHBoxLayout()
        self.viz_layout.setAlignment(Qt.AlignCenter)
        self.viz_layout.setSpacing(20)
        
        # Left Bars
        self.left_bars = QHBoxLayout()
        self.left_bars.setSpacing(6)
        self.bars = []
        for _ in range(12):
            bar = VisualizerBar()
            self.bars.append(bar)
            self.left_bars.addWidget(bar)
        
        # Central Core
        self.core = NeuralCore()
        
        # Right Bars
        self.right_bars = QHBoxLayout()
        self.right_bars.setSpacing(6)
        for _ in range(12):
            bar = VisualizerBar()
            self.bars.append(bar)
            self.right_bars.addWidget(bar)
            
        self.viz_layout.addLayout(self.left_bars)
        self.viz_layout.addWidget(self.core)
        self.viz_layout.addLayout(self.right_bars)
        
        player_view_layout.addLayout(self.viz_layout)

        # Track Info
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)
        self.track_title = QLabel("No Track Selected")
        self.track_title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {THEME_TEXT_MAIN};")
        self.track_artist = QLabel("Select a local file or sync with Spotify")
        self.track_artist.setStyleSheet(f"font-size: 14px; color: {THEME_TEXT_SUB};")
        info_layout.addWidget(self.track_title, 0, Qt.AlignCenter)
        info_layout.addWidget(self.track_artist, 0, Qt.AlignCenter)
        player_view_layout.addLayout(info_layout)

        # Search Results View
        self.results_view = QWidget()
        results_layout = QVBoxLayout(self.results_view)
        results_layout.setContentsMargins(0, 0, 0, 0)
        
        results_header = QHBoxLayout()
        self.results_label = StrongBodyLabel("Search Results")
        self.btn_back_to_player = TransparentToolButton(FIF.CLOSE)
        self.btn_back_to_player.clicked.connect(lambda: self.view_stack.setCurrentIndex(0))
        results_header.addWidget(self.results_label)
        results_header.addStretch()
        results_header.addWidget(self.btn_back_to_player)
        results_layout.addLayout(results_header)

        self.results_scroll = ScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.results_container = QWidget()
        self.results_list_layout = QVBoxLayout(self.results_container)
        self.results_list_layout.setSpacing(10)
        self.results_list_layout.addStretch()
        self.results_scroll.setWidget(self.results_container)
        results_layout.addWidget(self.results_scroll)

        # View Stack
        self.view_stack = QStackedWidget()
        self.view_stack.addWidget(self.player_view)
        self.view_stack.addWidget(self.results_view)
        card_layout.addWidget(self.view_stack)

        # Progress Bar
        self.progress_slider = Slider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        card_layout.addWidget(self.progress_slider)

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignCenter)
        controls_layout.setSpacing(30)

        self.btn_prev = TransparentToolButton(FIF.LEFT_ARROW)
        self.btn_play = TransparentToolButton(FIF.PLAY)
        self.btn_next = TransparentToolButton(FIF.RIGHT_ARROW)
        
        for btn in [self.btn_prev, self.btn_next]:
            btn.setIconSize(QSize(32, 32))
            btn.setFixedSize(64, 64)
            
        self.btn_play.setIconSize(QSize(48, 48))
        self.btn_play.setFixedSize(80, 80)
        self.btn_play.setStyleSheet(f"""
            ToolButton {{
                background-color: rgba(76, 201, 240, 0.1);
                border: 1px solid {THEME_ACCENT};
                border-radius: 40px;
            }}
            ToolButton:hover {{
                background-color: {THEME_ACCENT};
                color: #05080d;
            }}
        """)

        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_next)
        card_layout.addLayout(controls_layout)

        # Volume
        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(100, 0, 100, 0)
        vol_icon = QLabel("🔊")
        self.volume_slider = Slider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.audio_output.setVolume(0.7)
        volume_layout.addWidget(vol_icon)
        volume_layout.addWidget(self.volume_slider)
        card_layout.addLayout(volume_layout)

        layout.addWidget(self.player_card)

        # Bottom Actions
        actions_layout = QHBoxLayout()
        
        self.btn_spotify = PrimaryPushButton("SYNC SPOTIFY")
        self.btn_spotify.setFixedWidth(180)
        self.btn_spotify.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(30, 215, 96, 0.1);
                border: 1px solid #1ed760;
                border-radius: 6px;
                color: #1ed760;
            }}
            QPushButton:hover {{
                background-color: #1ed760;
                color: #05080d;
            }}
        """)
        
        self.btn_browse = PrimaryPushButton("OPEN LOCAL FILE")
        self.btn_browse.setFixedWidth(200)
        self.btn_browse.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(76, 201, 240, 0.1);
                border: 1px solid {THEME_ACCENT};
                border-radius: 6px;
                color: {THEME_TEXT_MAIN};
            }}
            QPushButton:hover {{
                background-color: {THEME_ACCENT};
                color: #05080d;
            }}
        """)
        actions_layout.addWidget(self.btn_spotify)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_browse)
        layout.addLayout(actions_layout)

    def _connect_signals(self):
        self.btn_browse.clicked.connect(self._browse_file)
        self.btn_spotify.clicked.connect(self._sync_spotify)
        self.btn_play.clicked.connect(self._toggle_playback)
        self.volume_slider.valueChanged.connect(self._set_volume)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)

    def _search_youtube(self):
        query = self.search_input.text()
        if not query:
            return
            
        self.track_title.setText("Searching YouTube...")
        self.track_artist.setText(f"Query: {query}")
        
        # Show results view and clear old results
        self.view_stack.setCurrentIndex(1)
        self._clear_results()
        self.results_label.setText(f"Searching: {query}...")
        
        # Run search in a thread to keep UI responsive
        threading.Thread(target=self._run_youtube_search, args=(query,), daemon=True).start()

    def _clear_results(self):
        while self.results_list_layout.count() > 1:
            item = self.results_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _run_youtube_search(self, query):
        results = self.yt_handler.search(query, limit=5)
        if results:
            from PySide6.QtCore import QMetaObject, Q_ARG, Slot
            QMetaObject.invokeMethod(self, "_display_results", 
                                   Qt.QueuedConnection, 
                                   Q_ARG(list, results))
        else:
            QMetaObject.invokeMethod(self, "_on_search_failed", Qt.QueuedConnection)

    @Slot(list)
    def _display_results(self, results):
        self.results_label.setText(f"YouTube Results: {len(results)}")
        self._clear_results()
        for track in results:
            card = SearchResultCard(track)
            card.clicked.connect(self._on_result_clicked)
            self.results_list_layout.insertWidget(self.results_list_layout.count() - 1, card)

    def _on_result_clicked(self, track_data):
        self.results_label.setText("Extracting Neural Stream...")
        # Get stream URL in background
        threading.Thread(target=self._extract_and_play, args=(track_data,), daemon=True).start()

    def _extract_and_play(self, track_data):
        stream_url = self.yt_handler.get_stream_url(track_data['url'])
        if stream_url:
            from PySide6.QtCore import QMetaObject, Q_ARG
            QMetaObject.invokeMethod(self, "_play_youtube_stream", 
                                   Qt.QueuedConnection, 
                                   Q_ARG(str, track_data['title']), 
                                   Q_ARG(str, track_data['uploader']),
                                   Q_ARG(str, stream_url))
            QMetaObject.invokeMethod(self.view_stack, "setCurrentIndex", Qt.QueuedConnection, Q_ARG(int, 0))
        else:
            QMetaObject.invokeMethod(self, "_on_search_failed", Qt.QueuedConnection)

    @Slot(str, str, str)
    def _play_youtube_stream(self, title, uploader, url):
        self.player.setSource(QUrl(url))
        self.track_title.setText(title)
        self.track_artist.setText(f"YouTube: {uploader}")
        
        # Pseudo-BPM from title
        h = hashlib.md5(title.encode()).hexdigest()
        self.bpm_seed = (int(h[:2], 16) / 255.0) 
        self.core.set_pulse_speed(0.5 + self.bpm_seed * 1.5)
        
        self.player.play()
        self.btn_play.setIcon(FIF.PAUSE)

    @Slot()
    def _on_search_failed(self):
        self.track_title.setText("No Mission Data Found")
        self.track_artist.setText("Search failed or no results.")

    def _sync_spotify(self):
        success, msg = self.spotify_handler.authenticate()
        if success:
            self.spotify_synced = True
            self.track_title.setText("Spotify Neural Link Active")
            self.track_artist.setText("Syncing live telemetry...")
            self.btn_spotify.setText("SPOTIFY LINKED")
            self.btn_spotify.setEnabled(False)
        else:
            self.track_title.setText("Sync Failed")
            self.track_artist.setText(msg)

    def _browse_file(self):
        # Disable spotify sync if browsing local
        self.spotify_synced = False
        self.btn_spotify.setEnabled(True)
        self.btn_spotify.setText("SYNC SPOTIFY")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio Pulse", "", "Audio Files (*.mp3 *.wav *.flac *.m4a)"
        )
        if file_path:
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.track_title.setText(file_path.split("/")[-1])
            self.track_artist.setText("Local Segment Indexed")
            
            # Calculate pseudo-BPM energy from filename
            h = hashlib.md5(file_path.encode()).hexdigest()
            self.bpm_seed = (int(h[:2], 16) / 255.0) 
            self.core.set_pulse_speed(0.5 + self.bpm_seed * 1.5)
            
            self.player.play()
            self.btn_play.setIcon(FIF.PAUSE)

    def _toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.btn_play.setIcon(FIF.PLAY)
        else:
            self.player.play()
            self.btn_play.setIcon(FIF.PAUSE)

    def _set_volume(self, val):
        self.audio_output.setVolume(val / 100.0)

    def _on_position_changed(self, pos):
        if not self.progress_slider.isSliderDown():
            duration = self.player.duration()
            if duration > 0:
                self.progress_slider.setValue(int(pos / duration * 1000))

    def _on_duration_changed(self, duration):
        pass

    def _on_slider_moved(self, pos):
        duration = self.player.duration()
        if duration > 0:
            self.player.setPosition(int(pos / 1000 * duration))

    def _update_loop(self):
        """Update simulated visualizer bars with BPM syncing."""
        is_playing = self.player.playbackState() == QMediaPlayer.PlayingState
        
        # Poll Spotify if synced
        if self.spotify_synced:
            track = self.spotify_handler.get_current_track()
            if track:
                is_playing = True # Force visualizer if spotify is playing
                self.track_title.setText(track['title'])
                self.track_artist.setText(f"Spotify: {track['artist']}")
                # Update progress slider
                self.progress_slider.setValue(int(track['progress_ms'] / track['duration_ms'] * 1000))
                
                # Update BPM seed from title occasionally
                h = hashlib.md5(track['title'].encode()).hexdigest()
                self.bpm_seed = (int(h[:2], 16) / 255.0)
                self.core.set_pulse_speed(0.5 + self.bpm_seed * 1.5)

        self.core.set_pulse(is_playing)
        
        # Smoothly transition energy for "breathing" effect
        self.current_energy = self.current_energy * 0.9 + self.target_energy * 0.1
        if random.random() > 0.8:
            # Occasional spikes in intensity
            self.target_energy = 0.5 + (random.random() * self.bpm_seed * 1.5)

        for bar in self.bars:
            if is_playing:
                # Height based on track energy and current pulse
                base_h = 20 + (self.bpm_seed * 40)
                var_h = random.randint(10, 40) * self.current_energy
                target = int(min(100, base_h + var_h))
                bar.set_target_height(target)
            else:
                # Settle down
                bar.set_target_height(10)

