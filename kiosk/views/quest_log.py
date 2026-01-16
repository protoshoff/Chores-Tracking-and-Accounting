from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, Signal
from ..components.holo_widgets import HoloFrame, HoloButton

class QuestLogView(QWidget):
    close_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main Layout (Centers the Holo Panel)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Holo Panel
        self.panel = HoloFrame(title="QUEST LOG")
        self.panel.setFixedSize(800, 600)
        
        # Panel Internal Layout
        # We need margins to avoid drawing over the glowing border/chamfers
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(60, 80, 60, 40) # Top margin clears the Title
        panel_layout.setSpacing(20)
        
        # --- A) Quest Heading ---
        lbl_head = QLabel("Current Objective: Sector 7")
        lbl_head.setObjectName("QuestHeading")
        lbl_head.setWordWrap(True)
        panel_layout.addWidget(lbl_head)
        
        # --- B) Quest Description ---
        desc_text = (
            "Retrieve the lost data core from Sector 7.\n\n"
            "Beware of rogue automated defenses and environmental hazards. "
            "Return to the command center for rewards.\n\n"
            "Status: PENDING AUTHORIZATION"
        )
        lbl_desc = QLabel(desc_text)
        lbl_desc.setObjectName("QuestDesc")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        panel_layout.addWidget(lbl_desc, 1) # Expand to fill space
        
        # --- C) Action Button Row (Mid-Panel) ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(40)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_track = HoloButton("TRACK")
        self.btn_abandon = HoloButton("ABANDON", is_primary=False)
        
        btn_layout.addWidget(self.btn_track)
        btn_layout.addWidget(self.btn_abandon)
        
        panel_layout.addLayout(btn_layout)
        
        panel_layout.addSpacing(20)
        
        # --- D) Footer Button Row ---
        foot_layout = QHBoxLayout()
        foot_layout.setSpacing(20)
        
        self.btn_active = HoloButton("ACTIVE", is_primary=False)
        self.btn_active.setMinimumWidth(100) # Smaller footer buttons
        
        self.btn_completed = HoloButton("COMPLETED", is_primary=False)
        self.btn_completed.setMinimumWidth(100)
        
        self.btn_close = HoloButton("CLOSE", is_primary=False)
        self.btn_close.setMinimumWidth(100)
        self.btn_close.clicked.connect(self.close_clicked.emit)
        
        foot_layout.addWidget(self.btn_active)
        foot_layout.addWidget(self.btn_completed)
        foot_layout.addStretch()
        foot_layout.addWidget(self.btn_close)
        
        panel_layout.addLayout(foot_layout)
        
        main_layout.addWidget(self.panel)
