#!/usr/bin/env python3
"""食品和化妆品保质期管理工具 - GUI版"""

import json
import os
import shutil
from collections import OrderedDict
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView,
    QFileDialog, QDialog, QFrame, QGraphicsDropShadowEffect,
    QDateEdit, QMenu, QListWidget, QListWidgetItem, QCheckBox,
    QStackedWidget, QDockWidget,
)
from PySide6.QtCore import Qt, QSize, QRect, QDate
from PySide6.QtGui import (
    QPixmap, QColor, QImage, QPainter, QPainterPath, QFont,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
CATEGORIES_FILE = os.path.join(BASE_DIR, "categories.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
IMAGE_DIR = os.path.join(BASE_DIR, "images")

DEFAULT_CATEGORIES = ["食品", "化妆品", "其他"]
THUMB_SIZE = 48
ROW_HEIGHT = 64
GROUP_HEADER_HEIGHT = 40

STATUS_STYLE = {
    "expired": ("#FF6B6B", "已过期"),
    "urgent":  ("#FFA94D", "即将过期"),
    "warning": ("#FFE066", "注意"),
    "normal":  ("#B2F2BB", "正常"),
}

FONT_FAMILY = "'Microsoft YaHei UI', 'PingFang SC', 'Noto Sans CJK SC', sans-serif"

# 生成下拉箭头 PNG 图标
_ARROW_PATH = os.path.join(BASE_DIR, "icons")
os.makedirs(_ARROW_PATH, exist_ok=True)
_ARROW_DOWN = os.path.join(_ARROW_PATH, "arrow_down.png")
_ARROW_UP = os.path.join(_ARROW_PATH, "arrow_up.png")
if not os.path.exists(_ARROW_DOWN):
    for path, direction in [(_ARROW_DOWN, "down"), (_ARROW_UP, "up")]:
        img = QImage(16, 16, QImage.Format.Format_ARGB32)
        img.fill(QColor(0, 0, 0, 0))
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#666666"))
        triangle = QPainterPath()
        if direction == "down":
            triangle.moveTo(2, 4)
            triangle.lineTo(14, 4)
            triangle.lineTo(8, 12)
        else:
            triangle.moveTo(2, 12)
            triangle.lineTo(14, 12)
            triangle.lineTo(8, 4)
        triangle.closeSubpath()
        p.drawPath(triangle)
        p.end()
        img.save(path)


def make_date_edit(date_str=None, default_days=None):
    """创建统一风格的 QDateEdit"""
    de = QDateEdit()
    de.setCalendarPopup(True)
    de.setDisplayFormat("yyyy年MM月dd日")
    de.setMinimumHeight(32)
    if date_str:
        de.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
    elif default_days is not None:
        de.setDate(QDate.currentDate().addDays(default_days))
    else:
        de.setDate(QDate.currentDate())
    return de

GLOBAL_QSS = f"""
* {{
    font-family: {FONT_FAMILY};
}}

QMainWindow {{
    background: #F8F9FA;
}}

QPushButton {{
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 500;
    color: #fff;
    background: #5C7CFA;
}}
QPushButton:hover {{ background: #4C6EF5; }}
QPushButton:pressed {{ background: #3B5BDB; }}

QPushButton[class="add"] {{
    background: #5C7CFA;
    font-size: 14px;
    font-weight: 600;
    padding: 10px 28px;
}}
QPushButton[class="add"]:hover {{ background: #4C6EF5; }}

QPushButton[class="secondary"] {{
    background: #E9ECEF;
    color: #495057;
}}
QPushButton[class="secondary"]:hover {{ background: #DEE2E6; }}

QPushButton[class="danger"] {{
    background: #FF6B6B;
}}
QPushButton[class="danger"]:hover {{ background: #FA5252; }}

QPushButton[class="dialog_add"] {{
    background: #5C7CFA;
    font-size: 14px;
    padding: 10px 0;
}}
QPushButton[class="dialog_add"]:hover {{ background: #4C6EF5; }}

QPushButton[class="dialog_img"] {{
    background: #E9ECEF;
    color: #495057;
    padding: 8px 14px;
}}
QPushButton[class="dialog_img"]:hover {{ background: #DEE2E6; }}

QLineEdit {{
    border: 1px solid #DEE2E6;
    border-radius: 6px;
    padding: 8px 12px;
    background: #fff;
    font-size: 13px;
    color: #495057;
    selection-background-color: #D0EBFF;
}}
QLineEdit:focus {{
    border-color: #5C7CFA;
}}

QComboBox {{
    border: 1px solid #DEE2E6;
    border-radius: 6px;
    padding: 8px 12px;
    background: #fff;
    font-size: 13px;
    color: #495057;
}}
QComboBox:focus {{ border-color: #5C7CFA; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox QAbstractItemView {{
    border: 1px solid #DEE2E6;
    border-radius: 6px;
    background: #fff;
    selection-background-color: #EDF2FF;
    outline: none;
}}

QTableWidget {{
    border: none;
    background: transparent;
    gridline-color: transparent;
    font-size: 13px;
    color: #495057;
    outline: none;
}}
QTableWidget::item {{
    padding: 4px;
    border-bottom: 1px solid #F1F3F5;
}}
QTableWidget::item:selected {{
    background: #EDF2FF;
    color: #364FC7;
}}

QTableWidget QCheckBox {{
    background: transparent;
}}
QTableWidget QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #CED4DA;
    background: #fff;
}}
QTableWidget QCheckBox::indicator:checked {{
    background: #5C7CFA;
    border-color: #5C7CFA;
}}

QHeaderView::section {{
    background: transparent;
    color: #ADB5BD;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding: 12px 8px 8px 8px;
    border: none;
    border-bottom: 2px solid #E9ECEF;
}}

QScrollBar:vertical {{
    width: 6px;
    background: transparent;
}}
QScrollBar::handle:vertical {{
    background: #CED4DA;
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QLabel[class="count"] {{
    color: #ADB5BD;
    font-size: 12px;
}}

QDateEdit {{
    border: 1px solid #DEE2E6;
    border-radius: 6px;
    padding: 6px 10px;
    padding-right: 28px;
    background: #fff;
    font-size: 13px;
    color: #333333;
}}
QDateEdit::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
}}
QDateEdit::down-arrow {{
    width: 16px;
    height: 16px;
    image: url({_ARROW_DOWN});
}}

QCalendarWidget {{
    background: #fff;
    color: #495057;
    min-width: 280px;
    max-width: 320px;
}}
QCalendarWidget QToolButton {{
    background: #fff;
    color: #333333;
    border: none;
    padding: 4px;
    font-size: 13px;
    font-weight: 600;
}}
QCalendarWidget QToolButton::up-arrow {{
    image: url({_ARROW_DOWN});
    width: 16px;
    height: 16px;
}}
QCalendarWidget QToolButton::down-arrow {{
    image: url({_ARROW_DOWN});
    width: 16px;
    height: 16px;
}}
QCalendarWidget QToolButton:hover {{
    background: #EDF2FF;
}}
QCalendarWidget QMenu {{
    background: #fff;
    color: #495057;
}}
QCalendarWidget QAbstractItemView {{
    background: #fff;
    color: #333333;
    selection-background-color: #EDF2FF;
    selection-color: #364FC7;
    alternate-background-color: #F8F9FA;
}}
QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background: #fff;
}}
QCalendarWidget QWidget#qt_calendar_calendarview {{
    background: #fff;
}}
"""


# ── 数据 ──

def load_items():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_items(items):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def load_categories():
    if os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
            cats = json.load(f)
            if cats:
                return cats
    return list(DEFAULT_CATEGORIES)


def save_categories(categories):
    with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            s = json.load(f)
            if "remind_days" in s:
                # 补齐 AI 配置默认值（向后兼容老 settings.json）
                s.setdefault("api_key", "")
                s.setdefault("base_url", DEFAULT_BASE_URL)
                s.setdefault("model", DEFAULT_MODEL)
                return s
    return {"remind_days": 30, "api_key": "", "base_url": DEFAULT_BASE_URL, "model": DEFAULT_MODEL}


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def save_image(src_path, item_id):
    os.makedirs(IMAGE_DIR, exist_ok=True)
    ext = os.path.splitext(src_path)[1]
    dst = os.path.join(IMAGE_DIR, f"{item_id}{ext}")
    shutil.copy2(src_path, dst)
    return dst


def _item_remind_days(item, global_days):
    return item.get("remind_days") or global_days


def get_status(item, global_days=30):
    remind_days = _item_remind_days(item, global_days)
    today = datetime.now().date()
    expiry = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
    days_left = (expiry - today).days

    if days_left < 0:
        return f"已过期 {abs(days_left)}天", "expired"
    elif days_left <= 7:
        return f"剩 {days_left}天", "urgent"
    elif days_left <= remind_days:
        return f"剩 {days_left}天", "warning"
    else:
        return f"剩 {days_left}天", "normal"


def count_alerts(items, global_days=30):
    today = datetime.now().date()
    expired = 0
    expiring = 0
    for item in items:
        remind_days = _item_remind_days(item, global_days)
        expiry = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
        days_left = (expiry - today).days
        if days_left < 0:
            expired += 1
        elif days_left <= remind_days:
            expiring += 1
    return expired, expiring


def expiry_sort_key(item):
    today = datetime.now().date()
    expiry = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
    days_left = (expiry - today).days
    # 已过期排最前面（days_left 负数越小越靠前），然后按剩余天数升序
    if days_left < 0:
        return (0, days_left)
    else:
        return (1, days_left)


# ── 缩略图 ──

def make_thumbnail(path):
    img = QImage(path)
    if img.isNull():
        return None
    size = THUMB_SIZE * 2
    scaled = img.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation)
    x = (scaled.width() - size) // 2
    y = (scaled.height() - size) // 2
    cropped = scaled.copy(x, y, size, size)
    pixmap = QPixmap.fromImage(cropped)
    pixmap.setDevicePixelRatio(2.0)
    return pixmap


# ── 表格自定义组件 ──

class ThumbnailWidget(QWidget):
    def __init__(self, pixmap=None, image_path="", parent=None):
        super().__init__(parent)
        self._pixmap = pixmap
        self._image_path = image_path
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(THUMB_SIZE + 8, THUMB_SIZE + 8)

    def paintEvent(self, event):
        if not self._pixmap:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = 8
        rect = QRect(4, 4, THUMB_SIZE, THUMB_SIZE)
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        painter.setClipPath(path)
        painter.drawPixmap(rect, self._pixmap)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._image_path:
            dlg = ImagePreviewDialog(self._image_path, self.window())
            dlg.exec()
        super().mousePressEvent(event)


class StatusBadge(QWidget):
    def __init__(self, text, level, parent=None):
        super().__init__(parent)
        self._text = text
        self._color = QColor(STATUS_STYLE[level][0])
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(self._text) + 20
        th = 24
        x = (self.width() - tw) / 2
        y = (self.height() - th) / 2
        rect = QRect(int(x), int(y), int(tw), th)

        bg = QColor(self._color)
        bg.setAlpha(40)
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 6, 6)

        painter.setPen(self._color)
        painter.setFont(QFont("sans-serif", 11, QFont.Weight.Medium))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._text)
        painter.end()


class GroupHeaderWidget(QWidget):
    """分组标题行：箭头 + 类别名 + 角标"""
    def __init__(self, category, count, expired_count, expiring_count, expanded=True, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        arrow = QLabel("▼" if expanded else "▶")
        arrow.setStyleSheet("color:#868E96; font-size:11px; background:transparent;")
        arrow.setFixedWidth(14)
        layout.addWidget(arrow)

        name = QLabel(category)
        name.setStyleSheet("font-size:14px; font-weight:600; color:#343A40; background:transparent;")
        layout.addWidget(name)

        total = QLabel(f"{count} 件")
        total.setStyleSheet("font-size:12px; color:#ADB5BD; background:transparent;")
        layout.addWidget(total)

        layout.addStretch()

        parts = []
        if expired_count > 0:
            parts.append(f"已过期{expired_count}")
        if expiring_count > 0:
            parts.append(f"即将过期{expiring_count}")
        if parts:
            badge = QLabel(" " + " · ".join(parts) + " ")
            badge.setStyleSheet(
                "background:#FF6B6B; color:#fff; font-size:11px; font-weight:600;"
                " border-radius:10px; padding:2px 8px;"
            )
            layout.addWidget(badge)


class ImageItem(QTableWidgetItem):
    def __init__(self):
        super().__init__()
        self.setSizeHint(QSize(THUMB_SIZE + 8, THUMB_SIZE + 8))
        self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsSelectable)


class StatusItem(QTableWidgetItem):
    def __init__(self):
        super().__init__()
        self.setSizeHint(QSize(1, ROW_HEIGHT))
        self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsSelectable)


class GroupHeaderItem(QTableWidgetItem):
    def __init__(self):
        super().__init__()
        self.setSizeHint(QSize(1, GROUP_HEADER_HEIGHT))
        self.setFlags(Qt.ItemFlag.NoItemFlags)


# ── 添加商品弹窗 ──

class AddItemDialog(QDialog):
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self._categories = list(categories)
        self._new_cat_saved = False
        self.settings = getattr(parent, "settings", {}) if parent else {}
        self.setWindowTitle("添加商品")
        self.setFixedWidth(380)
        self.setStyleSheet(f"""
            QDialog {{
                background: #fff;
                border-radius: 16px;
                font-family: {FONT_FAMILY};
            }}
            QLabel {{
                color: #868E96;
                font-size: 12px;
                font-weight: 600;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("添加新商品")
        title.setStyleSheet("font-size:18px; font-weight:700; color:#343A40;")
        layout.addWidget(title)

        layout.addWidget(QLabel("商品名称"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：全脂牛奶")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("类别"))
        cat_row = QHBoxLayout()
        cat_row.setSpacing(6)
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(self._categories)
        cat_row.addWidget(self.cat_combo, stretch=1)
        btn_add_cat = QPushButton("添加")
        btn_add_cat.setProperty("class", "secondary")
        btn_add_cat.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_cat.clicked.connect(self._add_category)
        cat_row.addWidget(btn_add_cat)
        btn_manage_cat = QPushButton("管理")
        btn_manage_cat.setProperty("class", "secondary")
        btn_manage_cat.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_manage_cat.clicked.connect(self._manage_category)
        cat_row.addWidget(btn_manage_cat)
        layout.addLayout(cat_row)

        layout.addWidget(QLabel("购买日期"))
        self.purchase_date = make_date_edit()
        layout.addWidget(self.purchase_date)

        layout.addWidget(QLabel("过期日期"))
        self.expiry_date = make_date_edit(default_days=30)
        layout.addWidget(self.expiry_date)

        shelf_row = QHBoxLayout()
        shelf_row.setSpacing(8)
        self.shelf_spin = QLineEdit()
        self.shelf_spin.setFixedWidth(80)
        self.shelf_spin.setPlaceholderText("如 12")
        self.shelf_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shelf_row.addWidget(self.shelf_spin)
        self.shelf_unit = QComboBox()
        self.shelf_unit.addItems(["天", "月", "年"])
        self.shelf_unit.setFixedWidth(80)
        shelf_row.addWidget(self.shelf_unit)
        btn_calc = QPushButton("计算过期日期")
        btn_calc.setProperty("class", "secondary")
        btn_calc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_calc.clicked.connect(self._calc_expiry)
        shelf_row.addWidget(btn_calc)
        shelf_row.addStretch()
        layout.addLayout(shelf_row)

        layout.addWidget(QLabel("商品图片（可选）"))
        img_row = QHBoxLayout()
        self._image_path = None
        btn_img = QPushButton("选择图片")
        btn_img.setProperty("class", "dialog_img")
        btn_img.clicked.connect(self._pick_image)
        img_row.addWidget(btn_img)
        self.img_label = QLabel("未选择")
        self.img_label.setStyleSheet("color:#CED4DA; font-size:12px;")
        img_row.addWidget(self.img_label)
        self._btn_ai_recognize = QPushButton("🔍 AI 识别")
        self._btn_ai_recognize.setProperty("class", "dialog_img")
        self._btn_ai_recognize.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_ai_recognize.setEnabled(False)
        self._btn_ai_recognize.clicked.connect(self._ai_recognize)
        img_row.addWidget(self._btn_ai_recognize)
        img_row.addStretch()
        layout.addLayout(img_row)

        layout.addWidget(QLabel("自定义提醒天数（可选，留空使用全局默认）"))
        remind_row = QHBoxLayout()
        remind_row.setSpacing(8)
        self.remind_input = QLineEdit()
        self.remind_input.setFixedWidth(80)
        self.remind_input.setPlaceholderText("如 7")
        self.remind_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        remind_row.addWidget(self.remind_input)
        remind_row.addWidget(QLabel("天"))
        remind_row.addStretch()
        layout.addLayout(remind_row)

        layout.addSpacing(8)
        btn_submit = QPushButton("确认添加")
        btn_submit.setProperty("class", "dialog_add")
        btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_submit.clicked.connect(self._submit)
        layout.addWidget(btn_submit)

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择商品图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self._image_path = path
            self.img_label.setText(os.path.basename(path))
            self.img_label.setStyleSheet("color:#495057; font-size:12px;")
            self._btn_ai_recognize.setEnabled(True)
        else:
            self._image_path = None
            self.img_label.setText("未选择")
            self.img_label.setStyleSheet("color:#CED4DA; font-size:12px;")
            self._btn_ai_recognize.setEnabled(False)

    def _ai_recognize(self):
        if not self._image_path:
            QMessageBox.information(self, "提示", "请先选择商品图片")
            return
        if not self.settings.get("api_key", "").strip():
            QMessageBox.warning(
                self, "未配置 API Key",
                "AI 拍照识别需要 DeepSeek API Key。\n请到「设置」中配置后再试。\n\n配置后可自动识别：\n• 商品名称\n• 类别（食品/化妆品/其他）\n• 建议保质期"
            )
            return
        self._btn_ai_recognize.setEnabled(False)
        self._btn_ai_recognize.setText("识别中…")
        try:
            with open(self._image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            ext = os.path.splitext(self._image_path)[1].lower().lstrip(".") or "png"
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
        except Exception as e:
            QMessageBox.critical(self, "图片读取失败", str(e))
            self._btn_ai_recognize.setEnabled(True)
            self._btn_ai_recognize.setText("🔍 AI 识别")
            return

        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": RECOGNIZE_PROMPT},
            ],
        }]
        worker = AIWorker(
            self.settings["api_key"],
            self.settings.get("base_url") or DEFAULT_BASE_URL,
            self.settings.get("model") or DEFAULT_MODEL,
            messages, temperature=0.3, max_tokens=500,
        )
        worker.finished_ok.connect(self._on_recognize_ok)
        worker.failed.connect(self._on_recognize_fail)
        worker.start()
        self._recog_worker = worker  # 防止被 GC

    def _on_recognize_ok(self, text):
        self._btn_ai_recognize.setEnabled(True)
        self._btn_ai_recognize.setText("🔍 AI 识别")
        try:
            # 提取 JSON（可能包在 ```json ... ``` 中）
            t = text.strip()
            if t.startswith("```"):
                t = t.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            data = json.loads(t)
            name = (data.get("name") or "").strip()
            category = (data.get("category") or "").strip()
            days = data.get("expiry_days")
            if name:
                self.name_input.setText(name)
            if category:
                # 类别可能不在现有列表中
                existing = [self.cat_combo.itemText(i) for i in range(self.cat_combo.count())]
                if category not in existing:
                    self.cat_combo.addItem(category)
                self.cat_combo.setCurrentText(category)
            if isinstance(days, (int, float)) and days > 0:
                self.shelf_spin.setText(str(int(days)))
                self._calc_expiry()  # 自动算过期日期
            QMessageBox.information(self, "识别成功", f"✅ 已自动填充：\n• 名称：{name or '(未识别)'}\n• 类别：{category or '(未识别)'}\n• 保质期：{days} 天" if days else f"识别完成：{name} / {category}")
        except Exception as e:
            QMessageBox.warning(self, "解析失败", f"AI 返回内容无法解析：\n{text}\n\n错误：{e}")

    def _on_recognize_fail(self, err):
        self._btn_ai_recognize.setEnabled(True)
        self._btn_ai_recognize.setText("🔍 AI 识别")
        QMessageBox.critical(self, "识别失败", f"API 调用失败：{err}")

    def _add_category(self):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "新增类别", "请输入类别名称：")
        text = text.strip()
        if not ok or not text:
            return
        existing = [self.cat_combo.itemText(i) for i in range(self.cat_combo.count())]
        if text in existing:
            QMessageBox.information(self, "提示", "该类别已存在")
            return
        self._categories.append(text)
        self.cat_combo.addItem(text)
        self.cat_combo.setCurrentText(text)
        self._new_cat_saved = True

    def _manage_category(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("管理类别")
        dlg.setFixedSize(280, 360)
        dlg.setStyleSheet(f"""
            QDialog {{ background:#fff; font-family:{FONT_FAMILY}; }}
            QLabel {{ color:#868E96; font-size:12px; font-weight:600; background:transparent; }}
        """)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(24, 20, 24, 20)
        dlg_layout.setSpacing(12)
        dlg_layout.addWidget(QLabel("选择要删除的类别（可多选）："))
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for cat in self._categories:
            list_widget.addItem(QListWidgetItem(cat))
        list_widget.setStyleSheet(
            "QListWidget { background:#fff; border:1px solid #DEE2E6; border-radius:6px; padding:4px; font-size:13px; }"
            "QListWidget::item { padding:8px; border-radius:4px; color:#495057; }"
            "QListWidget::item:selected { background:#EDF2FF; color:#364FC7; }"
        )
        dlg_layout.addWidget(list_widget)
        btn_del = QPushButton("删除选中")
        btn_del.setProperty("class", "danger")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.clicked.connect(dlg.accept)
        dlg_layout.addWidget(btn_del)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            selected = [item.text() for item in list_widget.selectedItems()]
            if not selected:
                return
            names = "、".join(selected)
            if QMessageBox.question(self, "确认", f"删除类别：{names}？") == QMessageBox.StandardButton.Yes:
                for name in selected:
                    self._categories.remove(name)
                    idx = self.cat_combo.findText(name)
                    if idx >= 0:
                        self.cat_combo.removeItem(idx)
                self._new_cat_saved = True

    def _calc_expiry(self):
        try:
            num = int(self.shelf_spin.text().strip())
        except ValueError:
            QMessageBox.warning(self, "提示", "请输入有效的数字")
            return
        if num <= 0:
            QMessageBox.warning(self, "提示", "数量需大于0")
            return
        unit = self.shelf_unit.currentText()
        base = self.purchase_date.date()
        if unit == "天":
            expiry = base.addDays(num)
        elif unit == "月":
            expiry = base.addMonths(num)
        else:
            expiry = base.addYears(num)
        self.expiry_date.setDate(expiry)

    def get_categories(self):
        return self._categories, self._new_cat_saved

    def _submit(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "提示", "请输入商品名称")
            return
        self.accept()

    def get_data(self):
        remind_text = self.remind_input.text().strip()
        remind_days = int(remind_text) if remind_text and remind_text.isdigit() else None
        return {
            "name": self.name_input.text().strip(),
            "category": self.cat_combo.currentText(),
            "purchase_date": self.purchase_date.date().toString("yyyy-MM-dd"),
            "expiry_date": self.expiry_date.date().toString("yyyy-MM-dd"),
            "image_path": self._image_path,
            "remind_days": remind_days,
        }


# ── 编辑商品弹窗 ──

class EditItemDialog(QDialog):
    def __init__(self, item_data, categories, parent=None):
        super().__init__(parent)
        self._categories = list(categories)
        self._image_path = None
        self._keep_image = True
        self.setWindowTitle("编辑商品")
        self.setFixedWidth(380)
        self.setStyleSheet(f"""
            QDialog {{
                background: #fff;
                border-radius: 16px;
                font-family: {FONT_FAMILY};
            }}
            QLabel {{
                color: #868E96;
                font-size: 12px;
                font-weight: 600;
            }}
            QDateEdit {{
                border: 1px solid #DEE2E6;
                border-radius: 6px;
                padding: 6px 10px;
                background: #fff;
                font-size: 13px;
                color: #495057;
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 24px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("编辑商品")
        title.setStyleSheet("font-size:18px; font-weight:700; color:#343A40;")
        layout.addWidget(title)

        layout.addWidget(QLabel("商品名称"))
        self.name_input = QLineEdit()
        self.name_input.setText(item_data["name"])
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("类别"))
        cat_row = QHBoxLayout()
        cat_row.setSpacing(6)
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(self._categories)
        idx = self.cat_combo.findText(item_data["category"])
        if idx >= 0:
            self.cat_combo.setCurrentIndex(idx)
        cat_row.addWidget(self.cat_combo, stretch=1)
        layout.addLayout(cat_row)

        layout.addWidget(QLabel("购买日期"))
        self.purchase_date = make_date_edit(date_str=item_data["purchase_date"])
        layout.addWidget(self.purchase_date)

        layout.addWidget(QLabel("过期日期"))
        self.expiry_input = QLineEdit()
        self.expiry_input.setText(item_data["expiry_date"])
        self.expiry_input.setPlaceholderText("YYYY-MM-DD 或通过保质期计算")
        layout.addWidget(self.expiry_input)

        shelf_row = QHBoxLayout()
        shelf_row.setSpacing(8)
        self.shelf_spin = QLineEdit()
        self.shelf_spin.setFixedWidth(80)
        self.shelf_spin.setPlaceholderText("如 12")
        self.shelf_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shelf_row.addWidget(self.shelf_spin)
        self.shelf_unit = QComboBox()
        self.shelf_unit.addItems(["天", "月", "年"])
        self.shelf_unit.setFixedWidth(80)
        shelf_row.addWidget(self.shelf_unit)
        btn_calc = QPushButton("计算过期日期")
        btn_calc.setProperty("class", "secondary")
        btn_calc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_calc.clicked.connect(self._calc_expiry)
        shelf_row.addWidget(btn_calc)
        shelf_row.addStretch()
        layout.addLayout(shelf_row)

        layout.addWidget(QLabel("商品图片"))
        img_row = QHBoxLayout()
        btn_img = QPushButton("更换图片")
        btn_img.setProperty("class", "dialog_img")
        btn_img.clicked.connect(self._pick_image)
        img_row.addWidget(btn_img)

        current_img = item_data.get("image", "")
        if current_img and os.path.exists(current_img):
            self.img_label = QLabel(os.path.basename(current_img))
            self.img_label.setStyleSheet("color:#495057; font-size:12px;")
            self._keep_image = True
        else:
            self.img_label = QLabel("未设置")
            self.img_label.setStyleSheet("color:#CED4DA; font-size:12px;")
            self._keep_image = False
        img_row.addWidget(self.img_label)
        img_row.addStretch()
        layout.addLayout(img_row)

        layout.addWidget(QLabel("自定义提醒天数（可选，留空使用全局默认）"))
        remind_row = QHBoxLayout()
        remind_row.setSpacing(8)
        self.remind_input = QLineEdit()
        self.remind_input.setFixedWidth(80)
        self.remind_input.setPlaceholderText("如 7")
        self.remind_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if item_data.get("remind_days"):
            self.remind_input.setText(str(item_data["remind_days"]))
        remind_row.addWidget(self.remind_input)
        remind_row.addWidget(QLabel("天"))
        remind_row.addStretch()
        layout.addLayout(remind_row)

        layout.addSpacing(8)
        btn_save = QPushButton("保存修改")
        btn_save.setProperty("class", "dialog_add")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._submit)
        layout.addWidget(btn_save)

        self._item_data = item_data

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择商品图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self._image_path = path
            self._keep_image = False
            self.img_label.setText(os.path.basename(path))
            self.img_label.setStyleSheet("color:#495057; font-size:12px;")

    def _calc_expiry(self):
        try:
            num = int(self.shelf_spin.text().strip())
        except ValueError:
            QMessageBox.warning(self, "提示", "请输入有效的数字")
            return
        if num <= 0:
            QMessageBox.warning(self, "提示", "数量需大于0")
            return
        unit = self.shelf_unit.currentText()
        base = self.purchase_date.date()
        if unit == "天":
            expiry = base.addDays(num)
        elif unit == "月":
            expiry = base.addMonths(num)
        else:
            expiry = base.addYears(num)
        self.expiry_input.setText(expiry.toString("yyyy-MM-dd"))

    def _submit(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "提示", "请输入商品名称")
            return
        expiry = self.expiry_input.text().strip()
        if not expiry:
            QMessageBox.warning(self, "提示", "请输入过期日期")
            return
        try:
            datetime.strptime(expiry, "%Y-%m-%d")
        except ValueError:
            QMessageBox.critical(self, "错误", "日期格式不正确")
            return
        self.accept()

    def get_data(self):
        remind_text = self.remind_input.text().strip()
        remind_days = int(remind_text) if remind_text and remind_text.isdigit() else None
        return {
            "name": self.name_input.text().strip(),
            "category": self.cat_combo.currentText(),
            "purchase_date": self.purchase_date.date().toString("yyyy-MM-dd"),
            "expiry_date": self.expiry_input.text().strip(),
            "image_path": self._image_path,
            "keep_image": self._keep_image,
            "remind_days": remind_days,
        }


# ── 图片预览 ──

class ImagePreviewDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("图片预览")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(f"QDialog {{ background:#fff; font-family:{FONT_FAMILY}; }}")

        img = QImage(image_path)
        if img.isNull():
            self.close()
            return

        screen = parent.screen().geometry() if parent else QApplication.primaryScreen().geometry()
        max_w = min(screen.width() * 0.8, 800)
        max_h = min(screen.height() * 0.8, 600)
        scaled = img.scaled(int(max_w), int(max_h),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)
        pixmap = QPixmap.fromImage(scaled)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel()
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.mousePressEvent = lambda e: self.close()
        layout.addWidget(label)

        btn_close = QPushButton("关闭")
        btn_close.setFixedWidth(100)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(
            "QPushButton { background:#ADB5BD; color:#fff; font-size:13px;"
            " border:none; border-radius:6px; padding:8px 0; }"
            "QPushButton:hover { background:#868E96; }"
        )
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        self.keyPressEvent = lambda e: self.close()


# ── 设置弹窗 ──

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedWidth(400)
        self.setStyleSheet(f"""
            QDialog {{
                background: #fff;
                border-radius: 16px;
                font-family: {FONT_FAMILY};
            }}
            QLabel {{
                color: #868E96;
                font-size: 12px;
                font-weight: 600;
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("设置")
        title.setStyleSheet("font-size:18px; font-weight:700; color:#343A40;")
        layout.addWidget(title)

        layout.addWidget(QLabel("提前提醒天数（全局默认）"))
        row = QHBoxLayout()
        row.setSpacing(6)
        self._days_buttons = []
        for d in [7, 15, 30]:
            btn = QPushButton(f"{d}天")
            btn.setProperty("class", "secondary")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _, val=d: self._set_days(val))
            row.addWidget(btn)
            self._days_buttons.append((btn, d))
        self._custom_input = QLineEdit()
        self._custom_input.setFixedWidth(64)
        self._custom_input.setPlaceholderText("自定义")
        self._custom_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._custom_input.textChanged.connect(self._clear_preset_highlight)
        row.addWidget(self._custom_input)
        row.addWidget(QLabel("天"))
        row.addStretch()
        layout.addLayout(row)

        self._days = settings["remind_days"]
        self._custom_input.setText(str(self._days))
        self._highlight_preset(self._days)

        layout.addSpacing(8)
        layout.addWidget(QLabel("DeepSeek API Key（用于 4 个 AI 功能）"))
        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setPlaceholderText("sk-...（留空则使用本地规则降级）")
        self._api_key_input.setText(settings.get("api_key", ""))
        layout.addWidget(self._api_key_input)

        layout.addWidget(QLabel("API Base URL（OpenAI 兼容协议）"))
        self._base_url_input = QLineEdit()
        self._base_url_input.setPlaceholderText(DEFAULT_BASE_URL)
        self._base_url_input.setText(settings.get("base_url", DEFAULT_BASE_URL))
        layout.addWidget(self._base_url_input)

        layout.addWidget(QLabel("模型名称"))
        self._model_input = QLineEdit()
        self._model_input.setPlaceholderText(DEFAULT_MODEL)
        self._model_input.setText(settings.get("model", DEFAULT_MODEL))
        layout.addWidget(self._model_input)

        btn_save = QPushButton("保存")
        btn_save.setProperty("class", "dialog_add")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._submit)
        layout.addWidget(btn_save)

    def _set_days(self, days):
        self._days = days
        self._custom_input.setText(str(days))
        self._highlight_preset(days)

    def _clear_preset_highlight(self):
        text = self._custom_input.text().strip()
        for btn, d in self._days_buttons:
            btn.setProperty("class", "secondary")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        try:
            val = int(text)
            if any(d == val for _, d in self._days_buttons):
                self._highlight_preset(val)
        except ValueError:
            pass

    def _highlight_preset(self, days):
        for btn, d in self._days_buttons:
            is_active = d == days
            btn.setProperty("class", "add" if is_active else "secondary")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _submit(self):
        text = self._custom_input.text().strip()
        try:
            val = int(text)
        except ValueError:
            QMessageBox.warning(self, "提示", "请输入有效的数字")
            return
        if val <= 0:
            QMessageBox.warning(self, "提示", "天数需大于0")
            return
        self._days = val
        self.accept()

    def get_data(self):
        return {
            "remind_days": self._days,
            "api_key": self._api_key_input.text().strip(),
            "base_url": self._base_url_input.text().strip() or DEFAULT_BASE_URL,
            "model": self._model_input.text().strip() or DEFAULT_MODEL,
        }


# ── 主窗口 ──

COL_CHECK, COL_IMAGE, COL_NAME, COL_PURCHASE, COL_EXPIRY, COL_STATUS, COL_ACTION = range(7)
HEADERS = ["", "图片", "名称", "购买日期", "过期日期", "状态", "操作"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("保质期管理")
        self.resize(860, 580)
        self.setStyleSheet(GLOBAL_QSS)

        self.items = load_items()
        self.categories = load_categories()
        self.settings = load_settings()
        self._next_id = max((i.get("id", 0) for i in self.items), default=0) + 1
        self._expanded_groups = set()
        self._row_item_map = {}

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(16)

        # 顶栏
        top = QHBoxLayout()
        title = QLabel("保质期管理")
        title.setStyleSheet("font-size:22px; font-weight:700; color:#343A40; background:transparent;")
        top.addWidget(title)
        top.addStretch()
        self._btn_insight = QPushButton("🧠 AI 洞察")
        self._btn_insight.setProperty("class", "secondary")
        self._btn_insight.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_insight.clicked.connect(self._on_insight)
        top.addWidget(self._btn_insight)

        self._btn_chat = QPushButton("💬 AI 助手")
        self._btn_chat.setProperty("class", "secondary")
        self._btn_chat.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_chat.clicked.connect(self._toggle_chat_dock)
        top.addWidget(self._btn_chat)

        btn_settings = QPushButton("⚙ 设置")
        btn_settings.setProperty("class", "secondary")
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.clicked.connect(self._open_settings)
        top.addWidget(btn_settings)

        btn_add = QPushButton("+ 添加商品")
        btn_add.setProperty("class", "add")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._open_add_dialog)
        top.addWidget(btn_add)
        root.addLayout(top)

        # 搜索栏
        search_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索商品名称或类别…")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setMaximumWidth(360)
        self._search_input.textChanged.connect(self._refresh_table)
        search_row.addWidget(self._search_input)
        search_row.addStretch()
        root.addLayout(search_row)

        # 卡片表格
        card = QFrame()
        card.setStyleSheet("QFrame { background:#fff; border-radius:12px; border:1px solid #F1F3F5; }")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 8)

        self.table = QTableWidget(0, len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.cellClicked.connect(self._on_cell_clicked)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(COL_CHECK, QHeaderView.ResizeMode.Fixed)
        hdr.resizeSection(COL_CHECK, 44)
        hdr.setSectionResizeMode(COL_IMAGE, QHeaderView.ResizeMode.Fixed)
        hdr.resizeSection(COL_IMAGE, THUMB_SIZE + 24)
        hdr.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(COL_PURCHASE, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(COL_EXPIRY, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeMode.Fixed)
        hdr.resizeSection(COL_STATUS, 130)
        hdr.setSectionResizeMode(COL_ACTION, QHeaderView.ResizeMode.Fixed)
        hdr.resizeSection(COL_ACTION, 70)

        card_layout.addWidget(self.table)

        # 空状态页
        empty = QWidget()
        empty.setStyleSheet("background:transparent;")
        empty_layout = QVBoxLayout(empty)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(12)
        empty_icon = QLabel("📦")
        empty_icon.setStyleSheet("font-size:48px; background:transparent;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)
        empty_hint = QLabel("还没有添加任何商品\n点击右上角 ＋ 添加你的第一件商品")
        empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_hint.setStyleSheet("color:#ADB5BD; font-size:14px; background:transparent;")
        empty_layout.addWidget(empty_hint)

        self._stack = QStackedWidget()
        self._stack.addWidget(card)
        self._stack.addWidget(empty)
        root.addWidget(self._stack, stretch=1)

        # 底栏
        bottom = QHBoxLayout()
        self._select_all_btn = QPushButton("全选")
        self._select_all_btn.setProperty("class", "secondary")
        self._select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._select_all_btn.clicked.connect(self._toggle_all_checks)
        bottom.addWidget(self._select_all_btn)

        btn_del = QPushButton("删除选中")
        btn_del.setProperty("class", "danger")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.clicked.connect(self._delete_item)
        bottom.addWidget(btn_del)
        bottom.addStretch()

        self._count_label = QLabel()
        self._count_label.setProperty("class", "count")
        bottom.addWidget(self._count_label)
        root.addLayout(bottom)

        self._refresh_table()
        self._check_reminders()

        # ── AI 助手侧边栏（QDockWidget 右侧停靠，默认隐藏）──
        self._chat_panel = ChatPanel(self.items, self.settings, self)
        self._chat_dock = QDockWidget("💬 AI 助手", self)
        self._chat_dock.setWidget(self._chat_panel)
        self._chat_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self._chat_dock.setMinimumWidth(380)
        self._chat_dock.setMaximumWidth(560)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._chat_dock)
        self._chat_dock.hide()

    # ── 分组数据 ──

    def _group_items(self):
        keyword = self._search_input.text().strip().lower()
        groups = OrderedDict()
        filtered = self.items
        if keyword:
            filtered = [
                i for i in self.items
                if keyword in i.get("name", "").lower()
                or keyword in i.get("category", "").lower()
            ]
        all_cats = list(dict.fromkeys(i.get("category", "其他") for i in filtered))
        for cat in all_cats:
            cat_items = [i for i in filtered if i.get("category", "其他") == cat]
            cat_items.sort(key=expiry_sort_key)
            groups[cat] = cat_items
        if not keyword:
            for cat in self.categories:
                if cat not in groups:
                    groups[cat] = []
        return groups

    # ── 操作 ──

    def _on_cell_clicked(self, row, col):
        # 点击分组标题行切换折叠
        item = self.table.item(row, COL_NAME)
        if item and item.data(Qt.ItemDataRole.UserRole) == "group_header":
            cat = item.data(Qt.ItemDataRole.UserRole + 1)
            if cat in self._expanded_groups:
                self._expanded_groups.discard(cat)
            else:
                self._expanded_groups.add(cat)
            self._refresh_table()
            return
        # 点击 group header 行的任意列都触发折叠
        check_item = self.table.item(row, COL_CHECK)
        if check_item and check_item.data(Qt.ItemDataRole.UserRole) == "group_header":
            cat = check_item.data(Qt.ItemDataRole.UserRole + 1)
            if cat in self._expanded_groups:
                self._expanded_groups.discard(cat)
            else:
                self._expanded_groups.add(cat)
            self._refresh_table()

    def _open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.settings = dlg.get_data()
            save_settings(self.settings)
            self._refresh_table()

    def _open_add_dialog(self):
        dlg = AddItemDialog(self.categories, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()

        cats, changed = dlg.get_categories()
        if changed:
            self.categories = cats
            save_categories(self.categories)

        item_id = self._next_id
        self._next_id += 1

        saved_image = ""
        if data["image_path"]:
            saved_image = save_image(data["image_path"], item_id)

        self.items.append({
            "id": item_id,
            "name": data["name"],
            "category": data["category"],
            "purchase_date": data["purchase_date"],
            "expiry_date": data["expiry_date"],
            "image": saved_image,
            "remind_days": data.get("remind_days"),
        })
        save_items(self.items)
        self._refresh_table()

    def _toggle_all_checks(self):
        checked = self._select_all_btn.text() == "全选"
        for row in range(self.table.rowCount()):
            cb = self._get_checkbox(row)
            if cb:
                cb.setChecked(checked)
        self._select_all_btn.setText("取消全选" if checked else "全选")

    def _get_checkbox(self, row):
        w = self.table.cellWidget(row, COL_CHECK)
        if w:
            return w.findChild(QCheckBox)
        return None

    def _delete_item(self):
        rows = []
        for row, idx in self._row_item_map.items():
            cb = self._get_checkbox(row)
            if cb and cb.isChecked():
                rows.append((row, idx))
        if not rows:
            QMessageBox.information(self, "提示", "请先勾选要删除的商品")
            return
        names = [self.items[idx]["name"] for _, idx in rows]
        if QMessageBox.question(self, "确认", f"确定删除：{', '.join(names)}？") == QMessageBox.StandardButton.Yes:
            item_indices = sorted([idx for _, idx in rows], reverse=True)
            for idx in item_indices:
                img = self.items[idx].get("image", "")
                if img and os.path.exists(img):
                    os.remove(img)
                self.items.pop(idx)
            save_items(self.items)
            self._refresh_table()
            self._select_all_btn.setText("全选")

    def _open_edit_dialog(self, row):
        if row not in self._row_item_map:
            return
        idx = self._row_item_map[row]
        data = self.items[idx]

        dlg = EditItemDialog(data, self.categories, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        new_data = dlg.get_data()

        # 处理图片
        if new_data["keep_image"]:
            image_path = data.get("image", "")
        elif new_data["image_path"]:
            # 删除旧图片
            old_img = data.get("image", "")
            if old_img and os.path.exists(old_img):
                os.remove(old_img)
            image_path = save_image(new_data["image_path"], data["id"])
        else:
            image_path = data.get("image", "")

        self.items[idx] = {
            "id": data["id"],
            "name": new_data["name"],
            "category": new_data["category"],
            "purchase_date": new_data["purchase_date"],
            "expiry_date": new_data["expiry_date"],
            "image": image_path,
            "remind_days": new_data.get("remind_days"),
        }
        save_items(self.items)
        self._refresh_table()

    def _insert_item_row(self, row, data, item_idx):
        self.table.insertRow(row)
        self.table.setRowHeight(row, ROW_HEIGHT)
        self._row_item_map[row] = item_idx

        # 复选框
        cb = QCheckBox()
        cb_container = QWidget()
        cb_container.setStyleSheet("background:transparent;")
        cb_layout = QHBoxLayout(cb_container)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cb_layout.addWidget(cb)
        self.table.setCellWidget(row, COL_CHECK, cb_container)

        # 图片
        img_path = data.get("image", "")
        pixmap = make_thumbnail(img_path) if img_path and os.path.exists(img_path) else None
        img_item = ImageItem()
        self.table.setItem(row, COL_IMAGE, img_item)
        if pixmap:
            self.table.setCellWidget(row, COL_IMAGE, ThumbnailWidget(pixmap, img_path))

        # 名称
        name_item = QTableWidgetItem(data["name"])
        name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, COL_NAME, name_item)

        # 购买日期
        purchase_item = QTableWidgetItem(data["purchase_date"])
        purchase_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, COL_PURCHASE, purchase_item)

        # 过期日期
        expiry_item = QTableWidgetItem(data["expiry_date"])
        expiry_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, COL_EXPIRY, expiry_item)

        # 状态
        status_text, level = get_status(data, self.settings["remind_days"])
        status_item = StatusItem()
        self.table.setItem(row, COL_STATUS, status_item)
        self.table.setCellWidget(row, COL_STATUS, StatusBadge(status_text, level))

        # 编辑按钮
        btn_edit = QPushButton("编辑")
        btn_edit.setProperty("class", "secondary")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setStyleSheet(
            "QPushButton { background:#EDF2FF; color:#5C7CFA; font-size:12px; padding:4px 12px; }"
            "QPushButton:hover { background:#DBE4FF; }"
        )
        btn_edit.clicked.connect(lambda _, r=row: self._open_edit_dialog(r))
        action_container = QWidget()
        action_container.setStyleSheet("background:transparent;")
        action_layout = QHBoxLayout(action_container)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_layout.addWidget(btn_edit)
        self.table.setCellWidget(row, COL_ACTION, action_container)

    def _insert_group_header(self, row, category, count, expired_count, expiring_count, expanded):
        self.table.insertRow(row)
        self.table.setRowHeight(row, GROUP_HEADER_HEIGHT)

        header_widget = GroupHeaderWidget(category, count, expired_count, expiring_count, expanded)
        self.table.setCellWidget(row, COL_CHECK, header_widget)
        self.table.setSpan(row, COL_CHECK, 1, len(HEADERS))

        # 用 UserRole 标记为 group header，保存类别名
        for col in range(len(HEADERS)):
            item = GroupHeaderItem()
            item.setData(Qt.ItemDataRole.UserRole, "group_header")
            item.setData(Qt.ItemDataRole.UserRole + 1, category)
            self.table.setItem(row, col, item)

    def _refresh_table(self):
        self.table.setRowCount(0)
        self._row_item_map = {}
        self._select_all_btn.setText("全选")

        if not self.items:
            self._stack.setCurrentIndex(1)
            self._count_label.setText("共 0 件商品")
            return
        self._stack.setCurrentIndex(0)

        groups = self._group_items()
        row = 0

        for cat, cat_items in groups.items():
            expired_count, expiring_count = count_alerts(cat_items, self.settings["remind_days"])
            expanded = cat in self._expanded_groups or cat not in self._expanded_groups and len(self._expanded_groups) == 0

            # 默认全部展开
            if len(self._expanded_groups) == 0:
                self._expanded_groups.add(cat)
                expanded = True

            self._insert_group_header(row, cat, len(cat_items), expired_count, expiring_count, expanded)
            row += 1

            if expanded:
                for item_idx, data in enumerate(cat_items):
                    # 找到在 self.items 中的真实索引
                    real_idx = self.items.index(data)
                    self._insert_item_row(row, data, real_idx)
                    row += 1

        keyword = self._search_input.text().strip()
        if keyword:
            total_shown = sum(len(v) for v in groups.values())
            self._count_label.setText(f"找到 {total_shown} 件商品（共 {len(self.items)} 件）")
        else:
            self._count_label.setText(f"共 {len(self.items)} 件商品")

    def _check_reminders(self):
        reminders = []
        for item in self.items:
            status_text, level = get_status(item, self.settings["remind_days"])
            if level in ("expired", "urgent", "warning"):
                reminders.append(f"  {item['name']}（{item['category']}）— {status_text}")
        if reminders:
            QMessageBox.warning(self, "保质期提醒", "以下商品需要注意：\n\n" + "\n".join(reminders))

    # ── AI 入口（3 个） ──

    def _has_api_key(self):
        return bool(self.settings.get("api_key", "").strip())

    def _ai_common(self, btn, title, prompt, fallback_local, temperature=0.7, max_tokens=1500):
        """AI 调用通用流程：禁用按钮 → Worker → Markdown 弹窗 / 本地降级"""
        btn.setEnabled(False)
        original_text = btn.text()
        btn.setText(original_text + " 思考中…")
        remind = self.settings["remind_days"]

        def restore():
            btn.setEnabled(True)
            btn.setText(original_text)

        if not self._has_api_key():
            text = fallback_local(self.items, remind)
            dlg = AIMarkdownDialog(title + "（本地降级）", text, self)
            restore()
            dlg.exec()
            return

        items_json = json.dumps(_items_for_ai(self.items, remind), ensure_ascii=False, indent=2)
        messages = [{"role": "user", "content": prompt.format(items_json=items_json)}]
        worker = AIWorker(
            self.settings["api_key"],
            self.settings.get("base_url") or DEFAULT_BASE_URL,
            self.settings.get("model") or DEFAULT_MODEL,
            messages, temperature, max_tokens,
        )

        def on_ok(text):
            dlg = AIMarkdownDialog(title, text, self)
            dlg.exec()
            restore()

        def on_fail(err):
            text = fallback_local(self.items, remind) + f"\n\n> ⚠️ API 调用失败：{err}"
            dlg = AIMarkdownDialog(title + "（本地降级）", text, self)
            dlg.exec()
            restore()

        worker.finished_ok.connect(on_ok)
        worker.failed.connect(on_fail)
        worker.start()

    def _on_insight(self):
        self._ai_common(
            self._btn_insight,
            "🧠 AI 洞察报告",
            INSIGHT_PROMPT,
            generate_insight_local,
            temperature=0.7,
            max_tokens=2000,
        )

    def _toggle_chat_dock(self):
        """切换 AI 助手侧边栏显示/隐藏"""
        if self._chat_dock.isVisible():
            self._chat_dock.hide()
        else:
            self._chat_dock.show()
            self._chat_dock.raise_()
            self._chat_panel._input.setFocus()


def generate_insight_local(items, remind_days):
    """无 API Key 时的本地洞察降级：4 维度基础分析"""
    if not items:
        return "📭 当前没有任何库存，暂无洞察可生成。先添加商品吧！"
    today = datetime.now().date()
    rows = []
    for it in items:
        try:
            expiry = datetime.strptime(it["expiry_date"], "%Y-%m-%d").date()
            days = (expiry - today).days
        except Exception:
            continue
        rows.append({"name": it.get("name", ""), "category": it.get("category", ""), "days": days})

    expired = [r for r in rows if r["days"] < 0]
    urgent = [r for r in rows if 0 <= r["days"] <= remind_days]
    soon = [r for r in rows if remind_days < r["days"] <= remind_days * 3]
    safe = [r for r in rows if r["days"] > remind_days * 3]

    # 类别统计
    cat_count = {}
    cat_expired = {}
    for r in rows:
        cat_count[r["category"]] = cat_count.get(r["category"], 0) + 1
        if r["days"] < 0:
            cat_expired[r["category"]] = cat_expired.get(r["category"], 0) + 1

    out = ["# 🧠 本地洞察报告\n", "> ⚠️ 未配置 API Key，已切换到本地规则模式。\n"]

    out.append("\n# 🧠 本周关注\n")
    if expired:
        for r in expired[:3]:
            out.append(f"- 🔴 **{r['name']}**（{r['category']}）已过期 {-r['days']} 天，需立即处理")
    if urgent:
        for r in urgent[:3]:
            out.append(f"- 🟠 **{r['name']}**（{r['category']}）剩 {r['days']} 天，本周内处理")
    if not (expired or urgent):
        out.append("- ✅ 本周没有紧急商品，继续保持")

    out.append("\n# 💡 处理建议\n")
    if expired:
        out.append("- 已过期商品建议直接丢弃，避免健康风险")
    if urgent:
        food_u = [r for r in urgent if r["category"] == "食品"]
        cos_u = [r for r in urgent if r["category"] == "化妆品"]
        if food_u:
            out.append(f"- 食品类（{len(food_u)} 件）建议尽快食用，可考虑做菜、做成果酱")
        if cos_u:
            out.append(f"- 化妆品（{len(cos_u)} 件）建议评估是否仍可使用")
    if not (expired or urgent):
        out.append("- 当前无需特殊处理，按时检查即可")

    out.append("\n# 📈 趋势发现\n")
    if cat_expired:
        worst = max(cat_expired, key=cat_expired.get)
        out.append(f"- **{worst}**类过期最多（{cat_expired[worst]} 件），建议减少该类采购量")
    out.append(f"- 当前库存共 {len(items)} 件，{len(cat_count)} 个类别（{', '.join(cat_count.keys())}）")
    if safe:
        out.append(f"- {len(safe)} 件商品状态健康（剩余 {remind_days*3}+ 天）")

    out.append("\n# ⚠️ 重要提醒\n")
    if expired:
        out.append(f"- 🔴 {len(expired)} 件已过期商品存在健康/安全风险，建议立即丢弃")
    if urgent:
        out.append(f"- 🟠 {len(urgent)} 件即将过期，需在本周内优先消耗")
    if not (expired or urgent):
        out.append("- 当前所有商品状态良好，继续保持定期检查习惯")

    total_risk = len(expired) + len(urgent)
    if total_risk == 0:
        out.append("\n---\n\n🎉 总体评价：库存管理优秀，无任何风险！")
    elif total_risk <= 3:
        out.append(f"\n---\n\n📊 总体评价：库存基本健康，{total_risk} 件需关注。")
    else:
        out.append(f"\n---\n\n⚠️ 总体评价：需立即处理 {total_risk} 件商品，建议尽快清理。")

    return "\n".join(out)


# ── AI 2：对话助手 ──────────────────────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """你是「到期管家」AI 助手，用户的家庭保质期管家。

能力：
- 查询用户的库存（即将过期 / 已过期 / 某类别）
- 给出食品保鲜建议（如"酸奶过期 2 天还能吃吗"）
- 给出生活类提醒（护照/健身卡/化妆品/药品）

回答要求：
1. 简洁（≤80 字），口语化
2. 涉及用户具体库存时引用实际数据
3. 不确定时如实说"建议查询官方"
4. 不寒暄，直接回答

用户当前库存：
{items_json}
"""


def generate_chat_local(messages, items, remind_days):
    """无 API Key 时的本地对话降级：基于规则的关键字匹配"""
    if not messages:
        return "你好！我是到期管家助手（本地模式）。配置 API Key 后可解锁 AI 对话。"
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break
    if not last_user_msg:
        return "请告诉我你想了解什么？"

    msg = last_user_msg.lower()
    today = datetime.now().date()
    expired = []
    urgent = []
    for it in items:
        try:
            expiry = datetime.strptime(it["expiry_date"], "%Y-%m-%d").date()
            days = (expiry - today).days
        except Exception:
            continue
        if days < 0:
            expired.append((it["name"], it["category"], -days))
        elif days <= remind_days:
            urgent.append((it["name"], it["category"], days))

    # 规则匹配
    if "过期" in msg and ("化妆品" in msg or "口红" in msg or "面霜" in msg):
        return "化妆品过期后可能引起皮肤刺激或感染，建议立即停用。护肤品开封后保质期通常 6-12 个月。"
    if "过期" in msg and ("牛奶" in msg or "酸奶" in msg or "食品" in msg):
        return "牛奶/酸奶过期后细菌可能大量繁殖，建议立即丢弃。即使闻起来正常也不建议食用。"
    if "护照" in msg or "签证" in msg:
        return "护照过期需到出入境管理局办理换发，一般 10-15 个工作日。多数国家要求护照剩余有效期 ≥6 个月，建议提前 6 个月办理。"
    if "健身卡" in msg or "会员" in msg:
        return "健身卡到期建议评估使用频率：每周 ≥2 次值得续；<1 次建议暂停。也可以和销售谈折扣或转卡。"
    if ("哪些" in msg or "什么" in msg) and ("过期" in msg or "到期" in msg):
        if not (expired or urgent):
            return "✅ 当前没有紧急过期或即将过期的商品，继续保持！"
        lines = []
        if expired:
            lines.append(f"已过期 {len(expired)} 件：" + "、".join(n for n, _, _ in expired[:5]))
        if urgent:
            lines.append(f"即将过期 {len(urgent)} 件：" + "、".join(f"{n}(剩{d}天)" for n, _, d in urgent[:5]))
        return "📋 " + "；".join(lines) + "。建议优先处理。"
    if "消耗" in msg or "吃" in msg or "用" in msg:
        if urgent:
            n, c, d = urgent[0]
            return f"建议优先消耗 **{n}**（{c}），还剩 {d} 天。可以做菜、烘焙或做成果酱。"
        if expired:
            return f"已过期商品建议直接丢弃，避免健康风险。"
        return "当前没有紧急需要消耗的商品。"

    # 默认兜底
    return f"（本地模式）你问的是「{last_user_msg}」。配置 API Key 后可获得 AI 智能回答。本地模式支持：哪些过期 / 怎么吃 / 护照 / 健身卡 / 化妆品 / 牛奶 相关问题。"


def load_chat_history():
    p = os.path.join(BASE_DIR, "chat_history.json")
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_chat_history(history):
    p = os.path.join(BASE_DIR, "chat_history.json")
    try:
        # 只保留最近 50 轮
        history = history[-100:]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class ChatPanel(QWidget):
    """AI 对话助手侧边栏面板（嵌入 QDockWidget，不打断主界面）"""
    def __init__(self, items, settings, parent=None):
        super().__init__(parent)
        self.items_ref = items
        self.settings = settings
        self.messages = []  # 当前会话上下文
        self.history = load_chat_history()  # 持久化历史
        self._worker = None

        self.setStyleSheet(f"""
            QWidget {{
                background: #fff;
                font-family: {FONT_FAMILY};
            }}
            QListWidget {{
                background: #F8F9FA;
                border: none;
                border-radius: 12px;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 8px;
                margin: 4px 0;
            }}
            QLineEdit {{
                background: #F1F3F5;
                border: 2px solid transparent;
                border-radius: 20px;
                padding: 10px 16px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 2px solid #4C6EF5;
                background: #fff;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 标题 + 历史按钮
        header = QHBoxLayout()
        title = QLabel("💬 AI 助手")
        title.setStyleSheet("font-size:18px; font-weight:700; color:#343A40;")
        header.addWidget(title)
        header.addStretch()
        self._btn_history = QPushButton("📜 查看聊天记录")
        self._btn_history.setProperty("class", "secondary")
        self._btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_history.clicked.connect(self._show_history)
        header.addWidget(self._btn_history)
        layout.addLayout(header)

        # 消息列表
        self._list = QListWidget()
        self._list.setWordWrap(True)
        layout.addWidget(self._list, stretch=1)

        # 预设问题
        preset_label = QLabel("点击下方问题即可提问：")
        preset_label.setStyleSheet("color:#868E96; font-size:12px;")
        layout.addWidget(preset_label)
        preset_row = QHBoxLayout()
        preset_row.setSpacing(6)
        for i, q in enumerate(PRESET_QUESTIONS, 1):
            btn = QPushButton(f"{i} {q[:6]}…")
            btn.setProperty("class", "secondary")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(q)
            btn.clicked.connect(lambda _, qq=q: self._send(qq))
            preset_row.addWidget(btn)
        layout.addLayout(preset_row)

        # 输入区
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self._input = QLineEdit()
        self._input.setPlaceholderText("输入你的问题…")
        self._input.returnPressed.connect(lambda: self._send(self._input.text().strip()))
        input_row.addWidget(self._input, stretch=1)
        self._btn_send = QPushButton("发送")
        self._btn_send.setProperty("class", "dialog_add")
        self._btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_send.clicked.connect(lambda: self._send(self._input.text().strip()))
        input_row.addWidget(self._btn_send)
        layout.addLayout(input_row)

        # 欢迎语
        self._append_msg("assistant", "👋 你好！我是到期管家助手。点击下方问题快速提问，或直接输入你的问题。")

    def _append_msg(self, role, text):
        prefix = "🧑 你" if role == "user" else "🤖 AI"
        item = QListWidgetItem(f"{prefix}\n{text}")
        if role == "user":
            item.setBackground(QColor("#E7F5FF"))
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            item.setBackground(QColor("#F8F9FA"))
        self._list.addItem(item)
        self._list.scrollToBottom()

    def _send(self, text):
        if not text:
            return
        self._append_msg("user", text)
        self._input.clear()
        self.messages.append({"role": "user", "content": text})
        self._btn_send.setEnabled(False)
        self._btn_send.setText("思考中…")

        if not self.settings.get("api_key", "").strip():
            # 本地降级
            reply = generate_chat_local(self.messages, self.items_ref, self.settings["remind_days"])
            self._finish_reply(reply)
            return

        # 真实 API 调用
        items_json = json.dumps(_items_for_ai(self.items_ref, self.settings["remind_days"]), ensure_ascii=False, indent=2)
        system_msg = {"role": "system", "content": CHAT_SYSTEM_PROMPT.format(items_json=items_json)}
        api_messages = [system_msg] + self.messages

        self._worker = AIWorker(
            self.settings["api_key"],
            self.settings.get("base_url") or DEFAULT_BASE_URL,
            self.settings.get("model") or DEFAULT_MODEL,
            api_messages, temperature=0.5, max_tokens=800,
        )
        self._worker.finished_ok.connect(self._finish_reply)
        self._worker.failed.connect(self._on_fail)
        self._worker.start()

    def _finish_reply(self, reply):
        self._append_msg("assistant", reply)
        self.messages.append({"role": "assistant", "content": reply})
        self._save_session()
        self._btn_send.setEnabled(True)
        self._btn_send.setText("发送")

    def _on_fail(self, err):
        # API 失败时本地降级
        reply = generate_chat_local(self.messages, self.items_ref, self.settings["remind_days"]) + f"\n\n> ⚠️ API 失败：{err}"
        self._finish_reply(reply)

    def _save_session(self):
        """保存当前会话到历史（最多保留最近 20 条消息）"""
        session = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "messages": self.messages[-20:],
        }
        self.history.append(session)
        save_chat_history(self.history)

    def _show_history(self):
        if not self.history:
            QMessageBox.information(self, "聊天记录", "暂无历史记录")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("聊天记录")
        dlg.resize(560, 480)
        layout = QVBoxLayout(dlg)
        title = QLabel(f"📜 历史会话（{len(self.history)} 次）")
        title.setStyleSheet("font-size:16px; font-weight:700; padding:8px;")
        layout.addWidget(title)
        list_w = QListWidget()
        for sess in reversed(self.history[-10:]):
            ts = sess.get("timestamp", "")
            msgs = sess.get("messages", [])
            first_user = next((m["content"][:30] for m in msgs if m["role"] == "user"), "(空)")
            item = QListWidgetItem(f"🕐 {ts}\n💬 {first_user}…")
            list_w.addItem(item)
        layout.addWidget(list_w)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close)
        dlg.exec()


# ────────────────────────────────────────────────────────────────────────────
# AI 模块（3 个：洞察 / 对话 / 拍照识别）
# ────────────────────────────────────────────────────────────────────────────

import base64
from openai import OpenAI
from PySide6.QtCore import QThread, Signal


# ── AI 1：拍照识别 ──────────────────────────────────────────────────────────

RECOGNIZE_PROMPT = """请识别这张商品图片中的信息。

严格按以下 JSON 格式输出（不要输出其他任何内容、不要 markdown 代码块标记）：
{
  "name": "商品名称（如'全脂牛奶 250ml'）",
  "category": "类别（从'食品'/'化妆品'/'药品'/'其他'中选最接近的）",
  "expiry_days": 数字（从图片中可见的保质期天数，没看到就根据商品类型估算，如牛奶7天、酸奶14天、化妆品365天）
}

只输出 JSON。"""


INSIGHT_PROMPT = """你是「到期管家」AI 分析师。基于用户库存生成 4 维度洞察报告。

要求按以下结构输出 Markdown：

# 🧠 本周关注
列出本周需要处理的 3-5 件商品（按紧急程度），每件 1 句说明

# 💡 处理建议
针对即将过期商品分类给出建议（如"食品类"→ 做菜、做成果酱；"化妆品"→ 评估是否继续使用）

# 📈 趋势发现
基于数据观察规律（如"食品类过期率最高"、"购买频率"），1-2 条

# ⚠️ 重要提醒
关键风险提示（如"已过期商品安全风险"、"即将过期食品需优先消耗"）

末尾用 1-2 句话给出总体评价（≤40 字）。

库存数据：
{items_json}
"""


def call_deepseek_text(api_key, base_url, model, messages, temperature=0.7, max_tokens=1500, timeout=45):
    """统一 DeepSeek 调用封装（OpenAI 兼容协议）"""
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


# 顶层可配置项
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
VL_MODEL = "deepseek-chat"  # DeepSeek-VL 通过同 base_url 复用，启用 base64 图像

PRESET_QUESTIONS = [
    "牛奶快过期了怎么消耗？",
    "护照过期了怎么续办？",
    "化妆品过期了还能用吗？",
    "健身卡到期了值得续吗？",
    "帮我看看哪些东西快到期了",
]


class AIWorker(QThread):
    """异步 AI 调用 Worker（通用基类）"""
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, api_key, base_url, model, messages, temperature=0.7, max_tokens=1500, parent=None):
        super().__init__(parent)
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.max_tokens = max_tokens

    def run(self):
        try:
            text = call_deepseek_text(
                self.api_key, self.base_url, self.model,
                self.messages, self.temperature, self.max_tokens,
            )
            self.finished_ok.emit(text)
        except Exception as e:
            self.failed.emit(str(e))


class AIMarkdownDialog(QDialog):
    """渲染 AI 输出（Markdown 简化版：粗体/标题/列表/换行）"""
    def __init__(self, title, markdown_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(560, 540)
        self.setStyleSheet(f"""
            QDialog {{
                background: #fff;
                font-family: {FONT_FAMILY};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:18px; font-weight:700; color:#343A40;")
        layout.addWidget(title_label)

        scroll = QFrame()
        scroll.setStyleSheet("QFrame { background:#F8F9FA; border-radius:12px; }")
        s_layout = QVBoxLayout(scroll)
        s_layout.setContentsMargins(16, 14, 16, 14)
        self._text = QLabel(self._md_to_html(markdown_text))
        self._text.setWordWrap(True)
        self._text.setTextFormat(Qt.TextFormat.RichText)
        self._text.setStyleSheet("font-size:13px; color:#343A40; line-height:1.6; background:transparent;")
        self._text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        s_layout.addWidget(self._text)
        layout.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setProperty("class", "secondary")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _md_to_html(self, md):
        import re
        lines = md.split("\n")
        out = []
        for ln in lines:
            ln = ln.rstrip()
            if ln.startswith("# "):
                out.append(f'<h2 style="color:#4C6EF5;">{ln[2:].strip()}</h2>')
            elif ln.startswith("## "):
                out.append(f'<h3 style="color:#343A40;">{ln[3:].strip()}</h3>')
            elif ln.startswith("### "):
                out.append(f'<b style="font-size:14px;">{ln[4:].strip()}</b>')
            elif ln.startswith(("- ", "* ")):
                content = ln[2:].strip()
                content = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content)
                out.append(f'&nbsp;&nbsp;• {content}')
            elif ln.startswith("> "):
                out.append(f'<i style="color:#868E96;">{ln[2:].strip()}</i>')
            elif ln.startswith("---"):
                out.append('<hr style="border:0; border-top:1px solid #DEE2E6; margin:8px 0;">')
            elif ln.strip() == "":
                out.append("<br>")
            else:
                ln = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", ln)
                out.append(ln)
        return "<br>".join(out)


def _items_for_ai(items, remind_days):
    """序列化 items 给 AI 用（含过期天数计算）"""
    today = datetime.now().date()
    rows = []
    for it in items:
        try:
            expiry = datetime.strptime(it["expiry_date"], "%Y-%m-%d").date()
            days = (expiry - today).days
        except Exception:
            days = None
        rows.append({
            "name": it.get("name", ""),
            "category": it.get("category", ""),
            "purchase_date": it.get("purchase_date", ""),
            "expiry_date": it.get("expiry_date", ""),
            "days_to_expiry": days,
            "remind_days": it.get("remind_days") or remind_days,
        })
    return rows


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
