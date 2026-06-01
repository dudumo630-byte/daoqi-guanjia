#!/usr/bin/env python3
"""食品和化妆品保质期管理工具"""

import json
import os
from datetime import datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def load_items():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_items(items):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def check_reminders(items):
    """检查30天内即将过期或已过期的商品，启动时自动提醒"""
    if not items:
        return

    today = datetime.now().date()
    alerts = []

    for i, item in enumerate(items):
        expiry = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
        days_left = (expiry - today).days

        if days_left < 0:
            alerts.append((i, item, days_left, "已过期"))
        elif days_left <= 30:
            alerts.append((i, item, days_left, "即将过期"))

    if not alerts:
        return

    print("\n" + "=" * 50)
    print("  ⚠️  保质期提醒")
    print("=" * 50)

    fmt = "{:<12} {:<8} {:<14} {:<16}"
    print(fmt.format("名称", "类别", "过期日期", "状态"))
    print("-" * 50)

    for _, item, days, status in alerts:
        if days < 0:
            label = f"已过期({abs(days)}天前)"
        else:
            label = f"还剩{days}天"
        print(fmt.format(item["name"], item["category"], item["expiry_date"], label))

    print("=" * 50 + "\n")


def add_item(items):
    name = input("商品名称: ").strip()
    if not name:
        print("名称不能为空")
        return

    category = input("类别 (1-食品 2-化妆品): ").strip()
    category = "食品" if category == "1" else "化妆品" if category == "2" else "其他"

    purchase_date = input("购买日期 (YYYY-MM-DD，留空用今天): ").strip()
    if not purchase_date:
        purchase_date = datetime.now().strftime("%Y-%m-%d")

    expiry_date = input("过期日期 (YYYY-MM-DD): ").strip()
    if not expiry_date:
        print("过期日期不能为空")
        return

    try:
        datetime.strptime(expiry_date, "%Y-%m-%d")
    except ValueError:
        print("日期格式不正确")
        return

    items.append({
        "name": name,
        "category": category,
        "purchase_date": purchase_date,
        "expiry_date": expiry_date,
    })
    save_items(items)
    print(f"已添加: {name}")


def list_items(items):
    if not items:
        print("暂无记录")
        return

    today = datetime.now().date()
    fmt = "{:<4} {:<12} {:<8} {:<14} {:<14} {:<10}"
    print(fmt.format("序号", "名称", "类别", "购买日期", "过期日期", "状态"))
    print("-" * 65)

    for i, item in enumerate(items):
        expiry = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
        days_left = (expiry - today).days

        if days_left < 0:
            status = "已过期"
        elif days_left <= 7:
            status = f"即将过期({days_left}天)"
        elif days_left <= 30:
            status = f"注意({days_left}天)"
        else:
            status = f"正常({days_left}天)"

        print(fmt.format(i + 1, item["name"], item["category"],
                         item["purchase_date"], item["expiry_date"], status))


def delete_item(items):
    list_items(items)
    if not items:
        return
    idx = input("输入要删除的序号: ").strip()
    try:
        idx = int(idx) - 1
        if 0 <= idx < len(items):
            removed = items.pop(idx)
            save_items(items)
            print(f"已删除: {removed['name']}")
        else:
            print("序号超出范围")
    except ValueError:
        print("请输入有效数字")


def main():
    items = load_items()
    check_reminders(items)

    menu = """
===== 保质期管理 =====
1. 添加商品
2. 查看所有商品
3. 删除商品
0. 退出
"""

    while True:
        print(menu)
        choice = input("请选择: ").strip()
        if choice == "1":
            add_item(items)
        elif choice == "2":
            list_items(items)
        elif choice == "3":
            delete_item(items)
        elif choice == "0":
            print("再见!")
            break
        else:
            print("无效选择")


if __name__ == "__main__":
    main()
