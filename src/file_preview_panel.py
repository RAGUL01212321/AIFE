"""
AIFE - File Preview Panel

Right-side panel widget for displaying RAG-retrieved files,
file details/properties, folder analytics, and content previews.
Designed to match AIFE's Catppuccin Mocha dark theme.
"""

import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QStackedWidget, QTextEdit, QSizePolicy,
    QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QLinearGradient,
    QPainterPath,
)
from typing import List, Dict, Any, Optional


# ─── Colour palette (Catppuccin Mocha) ─────────────────────
_SURFACE0  = "#313244"
_SURFACE1  = "#45475a"
_BASE      = "#1e1e2e"
_MANTLE    = "#181825"
_CRUST     = "#11111b"
_TEXT      = "#cdd6f4"
_SUBTEXT   = "#a6adc8"
_LAVENDER  = "#b4befe"
_MAUVE     = "#cba6f7"
_BLUE      = "#89b4fa"
_GREEN     = "#a6e3a1"
_PEACH     = "#fab387"
_RED       = "#f38ba8"
_YELLOW    = "#f9e2af"
_TEAL      = "#94e2d5"
_PINK      = "#f5c2e7"
_SKY       = "#89dceb"

_PIE_COLORS = [
    _MAUVE, _BLUE, _GREEN, _PEACH, _YELLOW,
    _TEAL, _PINK, _SKY, _RED, _LAVENDER,
]


class _Card(QFrame):
    """A styled card container"""
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("ragCard")
        self.setStyleSheet(f"""
            QFrame#ragCard {{
                background-color: {_SURFACE0};
                border: 1px solid {_SURFACE1};
                border-radius: 12px;
                padding: 0px;
            }}
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 12)
        self._layout.setSpacing(8)

        if title:
            lbl = QLabel(title)
            lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            lbl.setStyleSheet(f"color: {_TEXT}; background: transparent;")
            self._layout.addWidget(lbl)

    def add_widget(self, w):
        self._layout.addWidget(w)

    def add_layout(self, l):
        self._layout.addLayout(l)


class _FileRow(QFrame):
    """Single retrieved-file row"""
    clicked = pyqtSignal(str)  # emits file path

    def __init__(self, data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.file_path = data.get("path", "")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(52)
        self.setStyleSheet(f"""
            QFrame {{
                background: {_BASE};
                border: 1px solid {_SURFACE1};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: #7c3aed;
                background: rgba(124, 58, 237, 0.08);
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        # Icon
        is_dir = data.get("is_dir", False)
        is_link = data.get("is_symlink", False)
        icon = "📁" if is_dir else ("🔗" if is_link else "📄")
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedWidth(24)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 14))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_lbl)

        # Name + size column
        info = QVBoxLayout()
        info.setSpacing(1)
        name_lbl = QLabel(data.get("name", ""))
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        name_lbl.setStyleSheet(f"color: {_TEXT}; background: transparent; border: none;")
        info.addWidget(name_lbl)

        meta = data.get("readable_size", data.get("modified", ""))
        ext = data.get("extension", "")
        sub_text = f"{ext}  •  {meta}" if ext else str(meta)
        sub_lbl = QLabel(sub_text)
        sub_lbl.setFont(QFont("Segoe UI", 9))
        sub_lbl.setStyleSheet(f"color: {_SUBTEXT}; background: transparent; border: none;")
        info.addWidget(sub_lbl)
        layout.addLayout(info, 1)

        # Relevance dot
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {_GREEN}; font-size: 10px; background: transparent; border: none;")
        layout.addWidget(dot)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.file_path)
        super().mousePressEvent(event)


class _PieChart(QWidget):
    """Minimal pie chart drawn with QPainter"""
    def __init__(self, data: Dict[str, int], parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedSize(140, 140)

    def paintEvent(self, event):
        if not self.data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        total = sum(self.data.values())
        if total == 0:
            return

        rect = QRectF(10, 10, 120, 120)
        start_angle = 0

        for idx, (label, count) in enumerate(self.data.items()):
            span = int(count / total * 360 * 16)
            color = QColor(_PIE_COLORS[idx % len(_PIE_COLORS)])
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(_BASE), 2))
            painter.drawPie(rect, start_angle, span)
            start_angle += span

        painter.end()


class _PieLegend(QWidget):
    """Legend for the pie chart"""
    def __init__(self, data: Dict[str, int], parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        total = sum(data.values()) or 1
        for idx, (ext, count) in enumerate(list(data.items())[:8]):
            pct = count / total * 100
            color = _PIE_COLORS[idx % len(_PIE_COLORS)]
            row = QHBoxLayout()
            row.setSpacing(6)

            dot = QLabel("●")
            dot.setFixedWidth(14)
            dot.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent;")
            row.addWidget(dot)

            lbl = QLabel(f"{ext}  {count} ({pct:.0f}%)")
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setStyleSheet(f"color: {_SUBTEXT}; background: transparent;")
            row.addWidget(lbl, 1)

            layout.addLayout(row)

        layout.addStretch()


class FilePreviewPanel(QWidget):
    """
    Right-side panel displaying:
    - Retrieved files from RAG
    - Detailed file properties
    - Folder statistics with pie chart
    - Text file content preview
    """

    file_clicked = pyqtSignal(str)  # absolute path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self._setup_ui()

    # ──────────────── UI Setup ──────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(8)

        # Header
        header = QHBoxLayout()
        header.setSpacing(6)
        title = QLabel("🔍 Insights")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self._clear_btn = QPushButton("✕")
        self._clear_btn.setFixedSize(28, 28)
        self._clear_btn.setToolTip("Clear panel")
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_SURFACE0}; color: {_SUBTEXT};
                border: 1px solid {_SURFACE1}; border-radius: 6px;
                font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {_RED}; color: #fff; border-color: {_RED}; }}
        """)
        self._clear_btn.clicked.connect(self.clear)
        header.addWidget(self._clear_btn)
        root.addLayout(header)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
        """)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(10)
        self._content_layout.addStretch()

        scroll.setWidget(self._content)
        root.addWidget(scroll)

        # Placeholder
        self._show_placeholder()

    # ──────────────── Public API ──────────────────

    def show_retrieved_files(self, files: List[Dict[str, Any]]):
        """Display a list of RAG-retrieved files."""
        self._clear_content()

        card = _Card(f"📂 Retrieved Files ({len(files)})")

        if not files:
            lbl = QLabel("No matching files found.")
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet(f"color: {_SUBTEXT}; background: transparent;")
            card.add_widget(lbl)
        else:
            for f in files:
                row = _FileRow(f)
                row.clicked.connect(self._on_file_clicked)
                card.add_widget(row)

        self._content_layout.insertWidget(0, card)

    def show_file_details(self, props: Dict[str, Any]):
        """Display detailed file properties + optional content preview."""
        self._clear_content()

        if "error" in props:
            card = _Card("⚠️ Error")
            lbl = QLabel(props["error"])
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {_RED}; background: transparent;")
            card.add_widget(lbl)
            self._content_layout.insertWidget(0, card)
            return

        name = props.get("name", "Unknown")
        card = _Card(f"📋 {name}")

        # Properties grid
        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setColumnStretch(1, 1)

        fields = [
            ("Type", props.get("type", "")),
            ("Size", props.get("readable_size", "")),
            ("Path", props.get("path", "")),
            ("Permissions", f"{props.get('permissions_octal', '')} ({props.get('permissions_string', '')})"),
            ("Inode", str(props.get("inode", ""))),
            ("Hard Links", str(props.get("hard_links", ""))),
            ("Owner UID", str(props.get("owner_uid", ""))),
            ("Owner GID", str(props.get("owner_gid", ""))),
            ("Modified", props.get("modified", "")),
            ("Accessed", props.get("accessed", "")),
        ]

        for row_idx, (label, value) in enumerate(fields):
            key_lbl = QLabel(label)
            key_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
            key_lbl.setStyleSheet(f"color: {_LAVENDER}; background: transparent;")
            grid.addWidget(key_lbl, row_idx, 0, Qt.AlignTop)

            val_lbl = QLabel(str(value))
            val_lbl.setFont(QFont("JetBrains Mono", 9))
            val_lbl.setWordWrap(True)
            val_lbl.setStyleSheet(f"color: {_TEXT}; background: transparent;")
            grid.addWidget(val_lbl, row_idx, 1)

        card.add_layout(grid)
        self._content_layout.insertWidget(0, card)

        # Content preview
        preview = props.get("content_preview", "")
        if preview:
            preview_card = _Card("📝 Content Preview")
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(preview)
            text_edit.setFont(QFont("JetBrains Mono", 9))
            text_edit.setMaximumHeight(300)
            text_edit.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {_BASE};
                    color: {_TEXT};
                    border: 1px solid {_SURFACE1};
                    border-radius: 8px;
                    padding: 8px;
                }}
            """)
            preview_card.add_widget(text_edit)
            self._content_layout.insertWidget(1, preview_card)

    def show_folder_stats(self, stats: Dict[str, Any]):
        """Display folder statistics with pie chart."""
        self._clear_content()

        card = _Card("📊 Folder Statistics")

        # Summary stats
        summary = QGridLayout()
        summary.setSpacing(8)

        stat_items = [
            ("📄 Files", str(stats.get("total_files", 0)), _BLUE),
            ("📁 Folders", str(stats.get("total_folders", 0)), _PEACH),
            ("🔗 Symlinks", str(stats.get("total_symlinks", 0)), _TEAL),
            ("💾 Total Size", stats.get("readable_size", "0 B"), _GREEN),
            ("👁 Hidden", str(stats.get("hidden_count", 0)), _SUBTEXT),
        ]

        for idx, (label, value, color) in enumerate(stat_items):
            col = idx % 2
            row = idx // 2

            stat_frame = QFrame()
            stat_frame.setStyleSheet(f"""
                QFrame {{
                    background: {_BASE};
                    border: 1px solid {_SURFACE1};
                    border-radius: 8px;
                    padding: 8px;
                }}
            """)
            sl = QVBoxLayout(stat_frame)
            sl.setContentsMargins(8, 6, 8, 6)
            sl.setSpacing(2)

            v_lbl = QLabel(value)
            v_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
            v_lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
            v_lbl.setAlignment(Qt.AlignCenter)
            sl.addWidget(v_lbl)

            l_lbl = QLabel(label)
            l_lbl.setFont(QFont("Segoe UI", 9))
            l_lbl.setStyleSheet(f"color: {_SUBTEXT}; background: transparent; border: none;")
            l_lbl.setAlignment(Qt.AlignCenter)
            sl.addWidget(l_lbl)

            summary.addWidget(stat_frame, row, col)

        card.add_layout(summary)

        # Type distribution pie chart
        type_dist = stats.get("type_distribution", {})
        if type_dist:
            sep = QLabel("File Types")
            sep.setFont(QFont("Segoe UI", 10, QFont.Bold))
            sep.setStyleSheet(f"color: {_LAVENDER}; background: transparent; margin-top: 8px;")
            card.add_widget(sep)

            chart_row = QHBoxLayout()
            chart_row.setSpacing(12)
            chart_row.addWidget(_PieChart(type_dist))
            chart_row.addWidget(_PieLegend(type_dist), 1)
            card.add_layout(chart_row)

        # Extremes
        extremes_data = []
        if stats.get("largest_file"):
            f = stats["largest_file"]
            extremes_data.append(("📐 Largest", f"{f['name']} ({f['size']})"))
        if stats.get("smallest_file"):
            f = stats["smallest_file"]
            extremes_data.append(("🔬 Smallest", f"{f['name']} ({f['size']})"))
        if stats.get("newest_file"):
            f = stats["newest_file"]
            extremes_data.append(("🆕 Newest", f"{f['name']} ({f['modified']})"))
        if stats.get("oldest_file"):
            f = stats["oldest_file"]
            extremes_data.append(("📜 Oldest", f"{f['name']} ({f['modified']})"))

        if extremes_data:
            sep2 = QLabel("Notable Files")
            sep2.setFont(QFont("Segoe UI", 10, QFont.Bold))
            sep2.setStyleSheet(f"color: {_LAVENDER}; background: transparent; margin-top: 8px;")
            card.add_widget(sep2)

            for label, value in extremes_data:
                row_layout = QHBoxLayout()
                row_layout.setSpacing(6)
                k = QLabel(label)
                k.setFont(QFont("Segoe UI", 9, QFont.Bold))
                k.setStyleSheet(f"color: {_SUBTEXT}; background: transparent;")
                k.setFixedWidth(80)
                row_layout.addWidget(k)

                v = QLabel(value)
                v.setFont(QFont("Segoe UI", 9))
                v.setStyleSheet(f"color: {_TEXT}; background: transparent;")
                v.setWordWrap(True)
                row_layout.addWidget(v, 1)
                card.add_layout(row_layout)

        self._content_layout.insertWidget(0, card)

    def clear(self):
        """Clear all content and show placeholder."""
        self._clear_content()
        self._show_placeholder()

    # ──────────────── Private helpers ──────────────────

    def _clear_content(self):
        """Remove all widgets from the content area."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_placeholder(self):
        placeholder = QWidget()
        pl = QVBoxLayout(placeholder)
        pl.setAlignment(Qt.AlignCenter)
        pl.setSpacing(8)

        icon = QLabel("🔍")
        icon.setFont(QFont("Segoe UI Emoji", 32))
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("background: transparent;")
        pl.addWidget(icon)

        msg = QLabel("Ask the assistant about\nyour files to see insights here")
        msg.setFont(QFont("Segoe UI", 10))
        msg.setAlignment(Qt.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {_SUBTEXT}; background: transparent;")
        pl.addWidget(msg)

        hints = QLabel(
            "Try asking:\n"
            "• \"How many files are here?\"\n"
            "• \"Find python files\"\n"
            "• \"Show properties of README.md\"\n"
            "• \"What's the largest file?\""
        )
        hints.setFont(QFont("Segoe UI", 9))
        hints.setAlignment(Qt.AlignCenter)
        hints.setWordWrap(True)
        hints.setStyleSheet(f"color: {_SURFACE1}; background: transparent;")
        pl.addWidget(hints)

        self._content_layout.insertWidget(0, placeholder)

    def _on_file_clicked(self, path: str):
        self.file_clicked.emit(path)