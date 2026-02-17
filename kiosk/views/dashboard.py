from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QProgressBar, QGridLayout
from PySide6.QtCore import Qt, Signal, QByteArray, QSize
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QPainter, QIcon
from ..services.api import ApiService
from ..services.avatars import get_avatar_choices, get_avatar_svg, get_initials_svg
from ..components.holo_widgets import HoloFrame, HoloButton

AVATAR_SIZE = 100

def _render_avatar_pixmap(avatar_path, kid_name, kid_index, size=AVATAR_SIZE):
    choices = get_avatar_choices()
    if avatar_path in choices:
        svg_str = get_avatar_svg(avatar_path, kid_index)
    else:
        svg_str = get_initials_svg(kid_name, kid_index)
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
    """2-row grid of avatar buttons, hidden until the avatar is tapped."""
    avatar_selected = Signal(str)

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

    def __init__(self, current_avatar, kid_index, parent=None):
        super().__init__(parent)
        self._buttons = []

        # 5 columns × 2 rows fits all 9 options (1 initials + 8 presets) neatly
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 6, 0, 6)
        grid.setSpacing(6)

        BTN = 54  # button size px

        # "ABC" initials / reset option
        initials_btn = HoloButton("ABC")
        initials_btn.setFixedSize(BTN, BTN)
        initials_btn.clicked.connect(lambda: self.avatar_selected.emit(""))
        self._buttons.append(("", initials_btn))
        grid.addWidget(initials_btn, 0, 0)

        choices = get_avatar_choices()
        for i, name in enumerate(choices):
            btn = HoloButton("")
            btn.setFixedSize(BTN, BTN)
            icon = _make_svg_icon(get_avatar_svg(name, i), size=BTN - 8)
            btn.setIcon(icon)
            btn.setIconSize(QSize(BTN - 8, BTN - 8))
            btn.clicked.connect(lambda checked=False, n=name: self.avatar_selected.emit(n))
            self._buttons.append((name, btn))
            col = (i + 1) % 5
            row = (i + 1) // 5
            grid.addWidget(btn, row, col)

        self._highlight(current_avatar)

    def _highlight(self, selected):
        for av_name, btn in self._buttons:
            if av_name == "":
                btn.setStyleSheet(
                    self._STYLE_INITIALS_ACTIVE if selected == "" else self._STYLE_INITIALS_BASE
                )
            else:
                btn.setStyleSheet(
                    self._STYLE_ACTIVE if av_name == selected else self._STYLE_BASE
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
            self.avatar_picker.setParent(None)
            self.avatar_picker = None

        self.avatar_picker = AvatarPickerWidget(self._current_avatar, self._kid_index)
        self.avatar_picker.avatar_selected.connect(self._on_avatar_selected)
        # Insert right after avatar_lbl (index 1), then immediately hide
        sl.insertWidget(1, self.avatar_picker)
        self.avatar_picker.hide()

    def _toggle_picker(self, event=None):
        if self.avatar_picker is None:
            return
        self._picker_visible = not self._picker_visible
        self.avatar_picker.setVisible(self._picker_visible)

    def _on_avatar_selected(self, avatar_name):
        self._current_avatar = avatar_name
        ApiService.update_kid(self.kid_id, avatar_path=avatar_name)
        # Refresh avatar display
        px = _render_avatar_pixmap(avatar_name, self._kid_name, self._kid_index)
        self.avatar_lbl.setPixmap(px)
        # Update picker highlight
        if self.avatar_picker:
            self.avatar_picker._highlight(avatar_name)
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
            px = _render_avatar_pixmap(self._current_avatar, self._kid_name, self._kid_index)
            self.avatar_lbl.setPixmap(px)

            # Build picker (knows kid_index for color preview)
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
            if w: w.setParent(None)

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
            self.scroll_layout.addWidget(self._make_section_header("🔄 SHARED QUESTS"))
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
