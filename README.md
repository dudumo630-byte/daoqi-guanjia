# Shelf Life Manager / 保质期管理

[English](#english) | [中文](#中文)

---

## English

A lightweight desktop tool for tracking expiration dates of food, cosmetics, documents, and other items. Built with PySide6.

### Features

- **Grouped display** — Items are grouped by category (collapsible), sorted by days remaining within each group (expired items first).
- **Expiration alerts** — Red badges on group headers show expired and soon-to-expire counts. A reminder popup appears on launch.
- **Global & per-item reminders** — Set a default reminder window (7 / 15 / 30 days or custom) in Settings, or override it for individual items.
- **Add / Edit items** — Dialog with name, category, purchase date, expiry date, optional photo, and custom reminder days. Shelf life auto-calculates expiry from purchase date.
- **Custom categories** — Add or remove categories freely; persisted across sessions.
- **Image support** — Thumbnail preview in the table; click to view full-size.
- **Search & filter** — Real-time filtering by item name or category.
- **Batch delete** — Select multiple items and delete them at once.
- **Empty state** — Friendly placeholder when no items exist.
- **Persistent data** — All data stored as local JSON files. No server or account required.

### Project Structure

```
shelf-life-manager/
├── shelf_life_gui.py   # Main application
├── data.json           # Item data
├── categories.json     # Custom categories
├── settings.json       # User settings (auto-created)
├── images/             # Item photos
└── icons/              # UI icon assets (auto-generated)
```

### Getting Started

**Prerequisites:** Python 3.10+ and PySide6.

```bash
pip install PySide6
cd shelf-life-manager
python3 shelf_life_gui.py
```

### Screenshots

<p align="center">
  <img src="screenshots/主界面（有商品的状态）.png" width="45%" alt="Main Window">
  <img src="screenshots/添加商品弹窗.png" width="45%" alt="Add Item">
</p>

<p align="center">
  <img src="screenshots/空状态界面.png" width="45%" alt="Empty State">
</p>

---

## 中文

一个轻量级桌面工具，用于管理食品、化妆品、证件等物品的保质期 / 有效期。基于 PySide6 开发。

### 功能

- **分组显示** — 按类别分组折叠，组内按剩余天数排序，已过期排最前。
- **过期提醒** — 分组标题红色角标统计已过期和即将过期数量，启动时自动弹窗提醒。
- **全局 + 逐条提醒** — 在设置中配置默认提醒天数（7 / 15 / 30 天或自定义），也可为单个商品单独设置。
- **添加 / 编辑商品** — 弹窗支持名称、类别、购买日期、过期日期、可选图片、自定义提醒天数。保质期可自动计算过期日期。
- **自定义类别** — 自由添加和删除类别，持久保存。
- **图片支持** — 表格内缩略图预览，点击查看大图。
- **搜索过滤** — 按商品名称或类别实时筛选。
- **批量删除** — 勾选多条记录一键删除。
- **空状态提示** — 无商品时显示友好的引导提示。
- **本地存储** — 所有数据以 JSON 文件存储在本地，无需服务器或账号。

### 项目结构

```
shelf-life-manager/
├── shelf_life_gui.py   # 主程序
├── data.json           # 商品数据
├── categories.json     # 自定义类别
├── settings.json       # 用户设置（自动创建）
├── images/             # 商品图片
└── icons/              # 界面图标资源（自动生成）
```

### 如何运行

**前置条件：** Python 3.10+ 和 PySide6。

```bash
pip install PySide6
cd shelf-life-manager
python3 shelf_life_gui.py
```

### 截图说明

<p align="center">
  <img src="screenshots/主界面（有商品的状态）.png" width="45%" alt="主界面">
  <img src="screenshots/添加商品弹窗.png" width="45%" alt="添加商品">
</p>

<p align="center">
  <img src="screenshots/空状态界面.png" width="45%" alt="空状态">
</p>

---

## License

MIT
