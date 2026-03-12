from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QFrame, QGridLayout,
                             QSizePolicy, QSpacerItem)
from PyQt6.QtCore import Qt, QPointF
try:
    from PyQt6.QtWidgets import QScroller, QScrollerProperties
    HAS_QSCROLLER = True
except ImportError:
    try:
        from PyQt6.QtCore import QScroller, QScrollerProperties
        HAS_QSCROLLER = True
    except ImportError:
        HAS_QSCROLLER = False
import logging
import database


class VScrollArea(QScrollArea):
    """A scroll area that forces its content to match the viewport width,
    preventing horizontal scrolling and ensuring word-wrap works."""
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.widget():
            self.widget().setFixedWidth(self.viewport().width())


def _enable_touch_scroll(scroll_area):
    """Enable kinetic finger-flick scrolling on a QScrollArea.
    
    Uses QScroller if available (Qt 6.x). Falls back to a manual
    touch-drag implementation for compatibility.
    """
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    if HAS_QSCROLLER:
        QScroller.grabGesture(scroll_area.viewport(),
                              QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        scroller = QScroller.scroller(scroll_area.viewport())
        props = scroller.scrollerProperties()
        props.setScrollMetric(QScrollerProperties.ScrollMetric.DragVelocitySmoothingFactor, 0.6)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.MinimumVelocity, 0.0)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.MaximumVelocity, 0.5)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.AcceleratingFlickMaximumTime, 0.4)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.DecelerationFactor, 0.8)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.OvershootDragResistanceFactor, 0.35)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.OvershootScrollDistanceFactor, 0.1)
        scroller.setScrollerProperties(props)
        logging.debug("QScroller kinetic scroll enabled")
    else:
        # Fallback: manual touch-drag scrolling via event filter
        _install_touch_drag(scroll_area)
        logging.debug("Manual touch-drag scroll enabled (QScroller unavailable)")


def _install_touch_drag(scroll_area):
    """Fallback touch-drag scroll for systems without QScroller."""
    from PyQt6.QtCore import QObject, QEvent

    class TouchDragFilter(QObject):
        def __init__(self, scroll):
            super().__init__(scroll)
            self.scroll = scroll
            self._dragging = False
            self._last_y = 0
            self._last_x = 0

        def eventFilter(self, obj, event):
            if event.type() == QEvent.Type.MouseButtonPress:
                self._dragging = True
                pos = event.position()
                self._last_y = pos.y()
                self._last_x = pos.x()
                return False
            elif event.type() == QEvent.Type.MouseMove and self._dragging:
                pos = event.position()
                dy = self._last_y - pos.y()
                dx = self._last_x - pos.x()
                vbar = self.scroll.verticalScrollBar()
                hbar = self.scroll.horizontalScrollBar()
                if vbar:
                    vbar.setValue(vbar.value() + int(dy))
                if hbar:
                    hbar.setValue(hbar.value() + int(dx))
                self._last_y = pos.y()
                self._last_x = pos.x()
                return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._dragging = False
                return False
            return False

    filt = TouchDragFilter(scroll_area)
    scroll_area.viewport().installEventFilter(filt)


class LogHandler(logging.Handler):
    """Routes Python logging messages into the on-screen QTextEdit."""
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        msg = self.format(record)
        self.callback(msg)


# ─────────────────────── helpers ───────────────────────

def _icon(char):
    """Return a small coloured icon label using emoji / unicode."""
    lbl = QLabel(char)
    lbl.setFixedSize(20, 20)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet("font-size: 12px; background: transparent;")
    return lbl


def _truncate(text, maxlen=70):
    if len(text) > maxlen:
        return text[:maxlen] + "…"
    return text


def _format_date_short(iso_str):
    """Turn an ISO date string into a compact display like 'Mar 15'."""
    if not iso_str or iso_str == "Unknown Date":
        return "—"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d")
    except Exception:
        return iso_str[:10]


# ─────────────────────── DASHBOARD ───────────────────────

class DashboardScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #0a1628;")
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 8)
        root.setSpacing(10)

        # ── stat cards row ──
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)

        self.card_pending, self.lbl_pending = self._stat_card("PENDING REVIEWS", "📋", "0")
        self.card_invited, self.lbl_invited = self._stat_card("INVITATIONS", "✉️", "0")
        self.card_due, self.lbl_due = self._stat_card("DUE SOON", "📅", "0")

        cards_row.addWidget(self.card_pending)
        cards_row.addWidget(self.card_invited)
        cards_row.addWidget(self.card_due)
        root.addLayout(cards_row)

        # ── recent activity header ──
        hdr = QHBoxLayout()
        lbl_ra = QLabel("RECENT ACTIVITY")
        lbl_ra.setProperty("class", "section-header")
        lbl_view = QLabel("View all")
        lbl_view.setProperty("class", "section-link")
        hdr.addWidget(lbl_ra)
        hdr.addStretch()
        hdr.addWidget(lbl_view)
        root.addLayout(hdr)

        # ── activity list (scrollable) ──
        self.activity_scroll = VScrollArea()
        self.activity_scroll.setWidgetResizable(True)
        self.activity_container = QWidget()
        self.activity_container.setStyleSheet("background: transparent;")
        self.activity_layout = QVBoxLayout(self.activity_container)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(4)
        self.activity_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.activity_scroll.setWidget(self.activity_container)
        _enable_touch_scroll(self.activity_scroll)
        root.addWidget(self.activity_scroll)

    # helpers
    def _stat_card(self, title, icon_char, value):
        frame = QFrame()
        frame.setProperty("class", "stat-card")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)

        top = QHBoxLayout()
        lbl_t = QLabel(title)
        lbl_t.setProperty("class", "stat-header")
        top.addWidget(lbl_t)
        top.addStretch()
        top.addWidget(_icon(icon_char))
        lay.addLayout(top)

        lbl_v = QLabel(value)
        lbl_v.setProperty("class", "stat-value")
        lay.addWidget(lbl_v)

        return frame, lbl_v

    def _clear_activity(self):
        while self.activity_layout.count():
            child = self.activity_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def refresh_data(self):
        logging.info("Dashboard refresh")
        stats = database.get_dashboard_stats()
        self.lbl_pending.setText(str(stats.get("accepted", 0)))
        self.lbl_invited.setText(str(stats.get("invited", 0)))
        # "due soon" – count accepted items (placeholder logic)
        self.lbl_due.setText(str(stats.get("accepted", 0)))

        # Build a small recent-activity list (last 4 items from all statuses)
        self._clear_activity()
        all_items = []
        for status in ("completed", "accepted", "invited"):
            all_items.extend(database.get_reviews_by_status(status))

        for item in all_items[:4]:
            row = QFrame()
            row.setProperty("class", "activity-row")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(8, 4, 8, 4)
            rl.setSpacing(8)

            icon = "✅" if item["status"] == "completed" else ("📩" if item["status"] == "invited" else "📝")
            rl.addWidget(_icon(icon))

            col = QVBoxLayout()
            col.setSpacing(1)
            t = QLabel(_truncate(item["paper_title"], 55))
            t.setProperty("class", "activity-title")
            s = QLabel(item["journal_name"])
            s.setProperty("class", "activity-sub")
            col.addWidget(t)
            col.addWidget(s)
            rl.addLayout(col)
            rl.addStretch()

            ts = item.get("date_completed") or item.get("date_accepted") or item.get("date_invited") or ""
            tl = QLabel(_format_date_short(ts))
            tl.setProperty("class", "activity-time")
            rl.addWidget(tl)

            self.activity_layout.addWidget(row)


# ─────────────────────── INVITATIONS ───────────────────────

class InvitationsScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #0a1628;")
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 8)
        root.setSpacing(6)

        self.scroll = VScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.card_layout = QVBoxLayout(self.container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(8)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container)
        _enable_touch_scroll(self.scroll)
        root.addWidget(self.scroll)

    def _clear(self):
        while self.card_layout.count():
            c = self.card_layout.takeAt(0)
            if c.widget():
                c.widget().deleteLater()

    def refresh_data(self):
        logging.info("Invitations refresh")
        self._clear()
        items = database.get_reviews_by_status("invited")

        if not items:
            lbl = QLabel("No pending invitations.")
            lbl.setStyleSheet("color: #556b88; font-style: italic; font-size: 10px;")
            self.card_layout.addWidget(lbl)
            return

        for item in items:
            card = QFrame()
            card.setProperty("class", "review-card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(10, 8, 10, 8)
            cl.setSpacing(4)

            # Row 1: title + date badge
            r1 = QHBoxLayout()
            lbl_title = QLabel(item["paper_title"])
            lbl_title.setProperty("class", "card-title")
            lbl_title.setWordWrap(True)
            r1.addWidget(lbl_title)
            r1.addStretch()

            due = _format_date_short(item["review_due_date"])
            lbl_date = QLabel(f"📅 {due}")
            lbl_date.setProperty("class", "card-date")
            lbl_date.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            r1.addWidget(lbl_date)
            cl.addLayout(r1)

            # Row 2: journal
            lbl_j = QLabel(item["journal_name"].upper())
            lbl_j.setProperty("class", "card-journal")
            cl.addWidget(lbl_j)

            # Row 3: abstract snippet
            abstract = item.get("paper_abstract", "")
            if abstract and abstract != "No abstract available":
                lbl_abs = QLabel(item.get("paper_abstract", ""))
                lbl_abs.setProperty("class", "card-abstract")
                lbl_abs.setWordWrap(True)
                cl.addWidget(lbl_abs)

            # Row 4: buttons
            r4 = QHBoxLayout()
            r4.setSpacing(6)
            btn_acc = QPushButton("✔ Accept")
            btn_acc.setProperty("class", "btn-accept")
            btn_acc.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_acc.clicked.connect(lambda _, l=item["agree_link"]: self._action("Accept", l))
            r4.addWidget(btn_acc)

            btn_dec = QPushButton("✕ Decline")
            btn_dec.setProperty("class", "btn-decline")
            btn_dec.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_dec.clicked.connect(lambda _, l=item["decline_link"]: self._action("Decline", l))
            r4.addWidget(btn_dec)

            btn_ab = QPushButton("Abstract")
            btn_ab.setProperty("class", "btn-abstract")
            btn_ab.setCursor(Qt.CursorShape.PointingHandCursor)
            r4.addWidget(btn_ab)

            r4.addStretch()
            cl.addLayout(r4)

            self.card_layout.addWidget(card)

    def _action(self, kind, link):
        logging.info(f"[Invitation] {kind} clicked → {link}")


# ─────────────────────── PENDING ───────────────────────

class PendingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #0a1628;")
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 8)
        root.setSpacing(6)

        self.scroll = VScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.card_layout = QVBoxLayout(self.container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(8)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container)
        _enable_touch_scroll(self.scroll)
        root.addWidget(self.scroll)

    def _clear(self):
        while self.card_layout.count():
            c = self.card_layout.takeAt(0)
            if c.widget():
                c.widget().deleteLater()

    def refresh_data(self):
        logging.info("Pending refresh")
        self._clear()
        items = database.get_reviews_by_status("accepted")

        if not items:
            lbl = QLabel("No pending reviews.")
            lbl.setStyleSheet("color: #556b88; font-style: italic; font-size: 10px;")
            self.card_layout.addWidget(lbl)
            return

        for item in items:
            card = QFrame()
            card.setProperty("class", "review-card")
            cl = QHBoxLayout(card)
            cl.setContentsMargins(10, 8, 10, 8)
            cl.setSpacing(10)

            # Icon block
            icon_frame = QFrame()
            icon_frame.setFixedSize(36, 36)
            icon_frame.setStyleSheet("background: #1a3a5c; border-radius: 6px;")
            il = QVBoxLayout(icon_frame)
            il.setContentsMargins(0, 0, 0, 0)
            ic = QLabel("📄")
            ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ic.setStyleSheet("font-size: 16px; background: transparent;")
            il.addWidget(ic)
            cl.addWidget(icon_frame)

            # Info column
            info = QVBoxLayout()
            info.setSpacing(2)
            lbl_t = QLabel(item["paper_title"])
            lbl_t.setProperty("class", "card-title")
            lbl_t.setWordWrap(True)
            info.addWidget(lbl_t)

            badge_row = QHBoxLayout()
            badge_row.setSpacing(6)
            lbl_badge = QLabel("IN PROGRESS")
            lbl_badge.setProperty("class", "badge-progress")
            lbl_badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            badge_row.addWidget(lbl_badge)

            lbl_j = QLabel(item["journal_name"])
            lbl_j.setProperty("class", "card-abstract")
            badge_row.addWidget(lbl_j)
            badge_row.addStretch()
            info.addLayout(badge_row)

            cl.addLayout(info)
            cl.addStretch()

            # Right side: due date + portal button
            right = QVBoxLayout()
            right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            right.setSpacing(4)

            due_str = _format_date_short(item["review_due_date"])
            lbl_due = QLabel(f"Due: {due_str}")
            lbl_due.setProperty("class", "card-date")
            lbl_due.setAlignment(Qt.AlignmentFlag.AlignRight)
            right.addWidget(lbl_due)

            btn_p = QPushButton("Open Portal")
            btn_p.setProperty("class", "btn-portal")
            btn_p.setCursor(Qt.CursorShape.PointingHandCursor)
            link = item["manuscript_portal_link"] or item["direct_review_link"]
            btn_p.clicked.connect(lambda _, l=link: self._action(l))
            right.addWidget(btn_p)
            cl.addLayout(right)

            self.card_layout.addWidget(card)

    def _action(self, link):
        logging.info(f"[Pending] Open Portal → {link}")


# ─────────────────────── COMPLETED ───────────────────────

class CompletedScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #0a1628;")
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 8)
        root.setSpacing(6)

        self.scroll = VScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.card_layout = QVBoxLayout(self.container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(8)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container)
        _enable_touch_scroll(self.scroll)
        root.addWidget(self.scroll)

    def _clear(self):
        while self.card_layout.count():
            c = self.card_layout.takeAt(0)
            if c.widget():
                c.widget().deleteLater()

    def refresh_data(self):
        logging.info("Completed refresh")
        self._clear()
        items = database.get_reviews_by_status("completed")

        if not items:
            lbl = QLabel("No completed reviews yet.")
            lbl.setStyleSheet("color: #556b88; font-style: italic; font-size: 10px;")
            self.card_layout.addWidget(lbl)
            return

        for item in items:
            card = QFrame()
            card.setProperty("class", "review-card")
            cl = QHBoxLayout(card)
            cl.setContentsMargins(10, 8, 10, 8)
            cl.setSpacing(10)

            # Icon
            icon_frame = QFrame()
            icon_frame.setFixedSize(36, 36)
            icon_frame.setStyleSheet("background: #0b3d2e; border-radius: 6px;")
            il = QVBoxLayout(icon_frame)
            il.setContentsMargins(0, 0, 0, 0)
            ic = QLabel("✅")
            ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ic.setStyleSheet("font-size: 14px; background: transparent;")
            il.addWidget(ic)
            cl.addWidget(icon_frame)

            # Info
            info = QVBoxLayout()
            info.setSpacing(2)
            lbl_t = QLabel(item["paper_title"])
            lbl_t.setProperty("class", "card-title")
            lbl_t.setWordWrap(True)
            info.addWidget(lbl_t)

            meta_row = QHBoxLayout()
            meta_row.setSpacing(6)
            lbl_badge = QLabel("COMPLETED")
            lbl_badge.setProperty("class", "badge-completed")
            lbl_badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            meta_row.addWidget(lbl_badge)
            lbl_j = QLabel(item["journal_name"])
            lbl_j.setProperty("class", "card-abstract")
            meta_row.addWidget(lbl_j)
            meta_row.addStretch()
            info.addLayout(meta_row)
            cl.addLayout(info)
            cl.addStretch()

            # Date
            lbl_d = QLabel(_format_date_short(item["date_completed"]))
            lbl_d.setProperty("class", "activity-time")
            lbl_d.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            cl.addWidget(lbl_d)

            self.card_layout.addWidget(card)
