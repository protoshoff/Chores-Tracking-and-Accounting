from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QProgressBar, QGridLayout
from PySide6.QtCore import Qt, Signal, QByteArray, QSize
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QPainter, QIcon
from ..services.api import ApiService
from ..services.avatars import (get_avatar_choices, get_avatar_svg, get_initials_svg,
                                parse_avatar_path, encode_avatar_path, AVATAR_COLORS)
from ..components.holo_widgets import HoloFrame, HoloButton

AVATAR_SIZE = 130

def _render_avatar_pixmap(avatar_path, kid_name, size=AVATAR_SIZE):
    """Render an avatar_path (e.g. 'robot:3' or '') into a QPixmap."""
    avatar_name, color_index = parse_avatar_path(avatar_path)
    if avatar_name:
        svg_str = get_avatar_svg(avatar_name, color_index)
    else:
        svg_str = get_initials_svg(kid_name, color_index)
    renderer = QSvgRenderer(QByteArray(svg_str.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def _make_svg_icon(svg_str, size=38):
    """Render an SVG string into a QIcon."""
    renderer = QSvgRenderer(QByteArray(svg_str.encode()))
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    renderer.render(p)
    p.end()
    return QIcon(px)


class AvatarPickerWidget(QWidget):
    """Two-stage picker: icon grid → color swatches.

    Emits avatar_selected(encoded_path) where encoded_path is "name:color_index"
    or "" for initials.  Initials emit immediately (no color stage).
    """
    avatar_selected = Signal(str)

    _BTN = 54
    _SWATCH = 30

    _STYLE_BASE = (
        "QPushButton { border: 1px solid #334455; border-radius: 6px;"
        " background: rgba(0,0,0,0.4); }"
        " QPushButton:hover { border-color: #00E5FF; background: rgba(0,229,255,0.15); }"
    )
    _STYLE_ACTIVE = (
        "QPushButton { border: 2px solid #00E5FF; border-radius: 6px;"
        " background: rgba(0,229,255,0.2); }"
    )
    _STYLE_INITIALS_BASE = (
        "QPushButton { font-size: 11px; font-weight: bold; color: #00E5FF;"
        " border: 1px solid #334455; border-radius: 6px; background: rgba(0,229,255,0.08); }"
        " QPushButton:hover { border-color: #00E5FF; background: rgba(0,229,255,0.2); }"
    )
    _STYLE_INITIALS_ACTIVE = (
        "QPushButton { font-size: 11px; font-weight: bold; color: #00E5FF;"
        " border: 2px solid #00E5FF; border-radius: 6px; background: rgba(0,229,255,0.25); }"
    )

    def __init__(self, current_avatar_path, parent=None):
        super().__init__(parent)
        self._current_name, self._current_color = parse_avatar_path(current_avatar_path)
        self._pending_name = None  # name chosen, awaiting color pick
        self._icon_buttons = []
        self._swatch_buttons = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 6, 0, 6)
        outer.setSpacing(8)

        # --- Stage 1: icon grid ---
        self._icon_widget = QWidget()
        grid = QGridLayout(self._icon_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)

        # "ABC" initials option
        initials_btn = HoloButton("ABC")
        initials_btn.setFixedSize(self._BTN, self._BTN)
        initials_btn.clicked.connect(self._on_initials)
        self._icon_buttons.append(("", initials_btn))
        grid.addWidget(initials_btn, 0, 0)

        choices = get_avatar_choices()
        for i, name in enumerate(choices):
            btn = HoloButton("")
            btn.setFixedSize(self._BTN, self._BTN)
            # Preview each icon in its own distinct color so all look different
            icon = _make_svg_icon(get_avatar_svg(name, i), size=self._BTN - 8)
            btn.setIcon(icon)
            btn.setIconSize(QSize(self._BTN - 8, self._BTN - 8))
            btn.clicked.connect(lambda checked=False, n=name: self._on_icon_chosen(n))
            self._icon_buttons.append((name, btn))
            col = (i + 1) % 5
            row = (i + 1) // 5
            grid.addWidget(btn, row, col)

        outer.addWidget(self._icon_widget)

        # --- Stage 2: color swatch row (hidden until icon chosen) ---
        self._swatch_widget = QWidget()
        swatch_layout = QVBoxLayout(self._swatch_widget)
        swatch_layout.setContentsMargins(0, 0, 0, 0)
        swatch_layout.setSpacing(4)

        self._color_label = QLabel("PICK A COLOR:")
        self._color_label.setStyleSheet("color: #00E5FF; font-size: 11px; font-weight: bold;")
        swatch_layout.addWidget(self._color_label)

        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(5)
        for ci, hex_color in enumerate(AVATAR_COLORS):
            sw = HoloButton("")
            sw.setFixedSize(self._SWATCH, self._SWATCH)
            sw.setStyleSheet(
                f"QPushButton {{ background: {hex_color}; border: 2px solid transparent;"
                f" border-radius: {self._SWATCH // 2}px; }}"
                f" QPushButton:hover {{ border-color: white; }}"
            )
            sw.clicked.connect(lambda checked=False, c=ci: self._on_color_chosen(c))
            self._swatch_buttons.append(sw)
            swatch_row.addWidget(sw)
        swatch_row.addStretch()
        swatch_layout.addLayout(swatch_row)

        self._swatch_widget.hide()
        outer.addWidget(self._swatch_widget)

        self._highlight_icon(self._current_name)

    def _on_initials(self):
        """Initials need no color — emit immediately."""
        self.avatar_selected.emit("")

    def _on_icon_chosen(self, name):
        """User tapped an icon — show color swatches."""
        self._pending_name = name
        self._highlight_icon(name)
        # Pre-highlight the currently stored color
        self._highlight_swatch(self._current_color)
        self._swatch_widget.show()

    def _on_color_chosen(self, color_index):
        """User tapped a swatch — encode and emit."""
        self._current_color = color_index
        self._highlight_swatch(color_index)
        encoded = encode_avatar_path(self._pending_name, color_index)
        self.avatar_selected.emit(encoded)

    def _highlight_icon(self, selected_name):
        for av_name, btn in self._icon_buttons:
            if av_name == "":
                btn.setStyleSheet(
                    self._STYLE_INITIALS_ACTIVE if selected_name == "" else self._STYLE_INITIALS_BASE
                )
            else:
                btn.setStyleSheet(
                    self._STYLE_ACTIVE if av_name == selected_name else self._STYLE_BASE
                )

    def _highlight_swatch(self, selected_index):
        for ci, sw in enumerate(self._swatch_buttons):
            hex_color = AVATAR_COLORS[ci % len(AVATAR_COLORS)]
            border = "white" if ci == selected_index else "transparent"
            sw.setStyleSheet(
                f"QPushButton {{ background: {hex_color}; border: 2px solid {border};"
                f" border-radius: {self._SWATCH // 2}px; }}"
                f" QPushButton:hover {{ border-color: white; }}"
            )


class KidDashboardView(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.kid_id = None
        self._kid_name = ""
        self._kid_index = 0
        self._current_avatar = ""
        self._picker_visible = False

        main_layout = QVBoxLayout(self)

        # Header Row
        top = QHBoxLayout()
        self.btn_back = HoloButton("← BACK", is_primary=False)
        self.btn_back.setFixedSize(120, 50)
        self.btn_back.clicked.connect(self.back_clicked.emit)
        top.addWidget(self.btn_back)

        self.lbl_title = QLabel("DASHBOARD")
        self.lbl_title.setObjectName("HoloHeader")
        top.addWidget(self.lbl_title)
        top.addStretch()
        main_layout.addLayout(top)

        # Content Split
        content = QHBoxLayout()

        # --- LEFT: Status Panel ---
        self.status_panel = HoloFrame("STATUS")
        self.status_panel.setFixedWidth(350)
        sl = QVBoxLayout(self.status_panel)
        sl.setContentsMargins(30, 80, 30, 40)
        sl.setSpacing(12)
        sl.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Avatar container with pencil badge overlay
        BADGE = 24
        CONTAINER = AVATAR_SIZE + BADGE // 2  # badge hangs half-off bottom-right
        avatar_container = QWidget()
        avatar_container.setFixedSize(CONTAINER, CONTAINER)
        avatar_container.setCursor(Qt.CursorShape.PointingHandCursor)
        avatar_container.setToolTip("Tap to change avatar")
        avatar_container.mousePressEvent = self._toggle_picker

        self.avatar_lbl = QLabel(avatar_container)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        self.avatar_lbl.move(0, 0)

        # Pencil badge — bottom-right corner, fully inside the container
        self.pencil_lbl = QLabel("✏", avatar_container)
        self.pencil_lbl.setFixedSize(BADGE, BADGE)
        self.pencil_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pencil_lbl.setStyleSheet(
            "background: #00E5FF; color: #050510; border-radius: 12px;"
            " font-size: 13px; font-weight: bold;"
        )
        self.pencil_lbl.move(AVATAR_SIZE - BADGE // 2, AVATAR_SIZE - BADGE // 2)

        sl.addWidget(avatar_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Avatar picker (hidden until avatar tapped; inserted at index 1 by _build_picker)
        self.avatar_picker = None  # built on load_kid when we know kid_index

        self.name_lbl = QLabel("-")
        self.name_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        sl.addWidget(self.name_lbl)

        self.bal_lbl = QLabel("$0.00")
        self.bal_lbl.setStyleSheet("font-size: 48px; color: #00E5FF; font-weight: bold;")
        sl.addWidget(self.bal_lbl)

        # Progress Bars with Labels
        sl.addWidget(QLabel("OFFICIAL PROGRESS:"))
        self.prog_official = QProgressBar()
        self.prog_official.setTextVisible(True)
        self.prog_official.setFormat("%p%")
        sl.addWidget(self.prog_official)

        sl.addWidget(QLabel("YOUR PROGRESS:"))
        self.prog_kid = QProgressBar()
        self.prog_kid.setTextVisible(True)
        self.prog_kid.setFormat("%p%")
        sl.addWidget(self.prog_kid)

        sl.addStretch()
        content.addWidget(self.status_panel)

        # --- RIGHT: Quest Logs (Chores) ---
        self.quest_panel = HoloFrame("QUEST LIST")
        ql = QVBoxLayout(self.quest_panel)
        ql.setContentsMargins(30, 80, 30, 40)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.scroll_widget)

        ql.addWidget(scroll)
        content.addWidget(self.quest_panel)

        main_layout.addLayout(content)

    def _build_picker(self):
        """Build (or rebuild) the avatar picker for the current kid."""
        # Remove old picker if present
        sl = self.status_panel.layout()
        if self.avatar_picker is not None:
            sl.removeWidget(self.avatar_picker)
            self.avatar_picker.deleteLater()
            self.avatar_picker = None

        self.avatar_picker = AvatarPickerWidget(self._current_avatar)
        self.avatar_picker.avatar_selected.connect(self._on_avatar_selected)
        # Insert right after avatar_lbl (index 1), then immediately hide
        sl.insertWidget(1, self.avatar_picker)
        self.avatar_picker.hide()

    def _toggle_picker(self, event=None):
        if self.avatar_picker is None:
            return
        self._picker_visible = not self._picker_visible
        self.avatar_picker.setVisible(self._picker_visible)

    def _on_avatar_selected(self, encoded_path):
        self._current_avatar = encoded_path
        ApiService.update_kid(self.kid_id, avatar_path=encoded_path)
        # Refresh avatar display
        px = _render_avatar_pixmap(encoded_path, self._kid_name)
        self.avatar_lbl.setPixmap(px)
        # Close picker
        self._picker_visible = False
        self.avatar_picker.setVisible(False)

    def load_kid(self, kid_id):
        self.kid_id = kid_id
        kid = ApiService.get_kid(kid_id)
        if kid:
            self._kid_name = kid['name']
            self._kid_index = kid['id'] - 1
            self._current_avatar = kid.get('avatar_path', '') or ''

            self.name_lbl.setText(kid['name'])
            self.bal_lbl.setText(f"${kid['balance']:.2f}")
            self.lbl_title.setText(f"{kid['name'].upper()} // DASHBOARD")

            # Avatar
            px = _render_avatar_pixmap(self._current_avatar, self._kid_name)
            self.avatar_lbl.setPixmap(px)

            # Build picker
            self._build_picker()
            self._picker_visible = False

            # Progress
            summary = kid.get("chores_summary", {})
            total = summary.get("total_weight", 1)
            if total == 0: total = 1

            off_pct = summary.get("week_pct", 0)
            self.prog_official.setValue(off_pct)

            done_weight = summary.get("completed_weight", 0)
            kid_pct = int((done_weight / total) * 100)
            if kid_pct > 100: kid_pct = 100
            self.prog_kid.setValue(kid_pct)

        self.load_chores()

    def load_chores(self):
        while self.scroll_layout.count():
            w = self.scroll_layout.takeAt(0).widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        chores = ApiService.get_kid_chores(self.kid_id)

        if not chores:
            self.scroll_layout.addWidget(QLabel("NO ACTIVE QUESTS DETECTED."))
            return

        dailies = [c for c in chores if c.get("frequency") == "DAILY"]
        weeklies = [c for c in chores if c.get("frequency") == "WEEKLY"]

        if dailies:
            self.scroll_layout.addWidget(self._make_section_header("DAILY QUESTS"))
            for c in dailies:
                self.scroll_layout.addWidget(self._create_quest_row(c))

        if weeklies:
            self.scroll_layout.addWidget(self._make_section_header("WEEKLY QUESTS"))
            for c in weeklies:
                self.scroll_layout.addWidget(self._create_quest_row(c))

        rotation_chores = ApiService.get_rotation_chores(self.kid_id)
        if rotation_chores:
            self.scroll_layout.addWidget(self._make_section_header("SHARED QUESTS"))
            for c in rotation_chores:
                self.scroll_layout.addWidget(self._create_quest_row(c, is_rotation=True))

    def _make_section_header(self, text):
        l = QLabel(text)
        l.setStyleSheet("color: #00E5FF; font-weight: bold; margin-top: 10px; border-bottom: 1px solid #007BFF;")
        return l

    def _create_quest_row(self, c, is_rotation=False):
        frame = QFrame()
        border_color = "#FF6B35" if is_rotation else "#007BFF"
        frame.setStyleSheet(f"background-color: rgba(0, 123, 255, 0.1); border: 1px solid {border_color}; border-radius: 4px;")
        layout = QHBoxLayout(frame)

        v = QVBoxLayout()
        name_text = c['name']
        name = QLabel(name_text)
        name.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        v.addWidget(name)

        desc_text = c.get('description', '') or ''
        if is_rotation and c.get('shared_with'):
            shared = ", ".join(c['shared_with'])
            desc_text = f"Alternates with {shared}"
        desc = QLabel(desc_text)
        desc.setStyleSheet("color: #B0BEC5; font-size: 14px;")
        v.addWidget(desc)
        layout.addLayout(v)

        layout.addStretch()

        status = c.get('status', 'INCOMPLETE')

        if status == 'INCOMPLETE':
            btn = HoloButton("COMPLETE", is_primary=True)
            btn.setFixedSize(155, 40)
            if is_rotation:
                btn.clicked.connect(lambda _, gid=c['id']: self.mark_rotation_done(gid))
            else:
                btn.clicked.connect(lambda _, cid=c['id']: self.mark_done(cid))
            layout.addWidget(btn)
        elif status == 'REJECTED':
            btn = HoloButton("RETRY", is_primary=False)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 85, 85, 0.2);
                    border: 1px solid #FF5555;
                    color: #FF5555;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(255, 85, 85, 0.4);
                }
            """)
            btn.setFixedSize(140, 40)
            if is_rotation:
                btn.clicked.connect(lambda _, gid=c['id']: self.mark_rotation_done(gid))
            else:
                btn.clicked.connect(lambda _, cid=c['id']: self.mark_done(cid))
            layout.addWidget(btn)
        else:
            lbl_text = status
            lbl_style = "font-weight: bold; color: white;"

            if status == "PENDING":
                lbl_text = "WAITING APPROVAL"
                lbl_style = "color: #FFD700; font-weight: bold;"
            elif status == "APPROVED":
                lbl_text = "COMPLETED"
                lbl_style = "color: #00E5FF; font-weight: bold;"

            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(lbl_style)
            layout.addWidget(lbl)

        return frame

    def mark_done(self, chore_id):
        from ..services.sound import SoundService
        ApiService.complete_chore(chore_id, self.kid_id)
        SoundService.play_chore_complete()
        self.load_chores()

    def mark_rotation_done(self, group_id):
        from ..services.sound import SoundService
        ApiService.complete_rotation_chore(group_id, self.kid_id)
        SoundService.play_chore_complete()
        self.load_chores()
