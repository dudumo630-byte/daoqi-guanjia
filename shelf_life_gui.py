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
    QStackedWidget,
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
                return s
    return {"remind_days": 30}


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
        else:
            self._image_path = None
            self.img_label.setText("未选择")
            self.img_label.setStyleSheet("color:#CED4DA; font-size:12px;")

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
        return {"remind_days": self._days}


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


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
