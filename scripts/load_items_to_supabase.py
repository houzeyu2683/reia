"""將 .cache/<期間>/<查詢類型>/<縣市>/<行政區>/items.json 整理後 upsert 到 Supabase 的 house_transactions。

用法:
    python scripts/load_items_to_supabase.py --period 115_1-115_6 --city 基隆市 臺北市
    python scripts/load_items_to_supabase.py --period 115_1-115_6 --dry-run   # 只解析、統計, 不寫入
    python scripts/load_items_to_supabase.py --period 115_1-115_6 --city 基隆市 --csv output/keelung.csv  # 輸出 CSV 觀察
    python scripts/load_items_to_supabase.py --period 115_1-115_6 --city 基隆市 --csv output/keelung_raw.csv --raw  # 原始 43 個 key

需要在 .env 設定 SUPABASE_URL 與 SUPABASE_SERVICE_ROLE_KEY。
資料表請先用 supabase/migrations/20261031000000_create_house_transactions.sql 建立。
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

from dotenv import dotenv_values

TABLE = "house_transactions"
CN_DIGITS = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
LAYOUT_RE = {part: re.compile(rf"(\d+){part}") for part in ("房", "廳", "衛")}
VOLATILE_KEYS = ("id", "r")  # 每次查詢可能不同, 不納入去重鍵
# 原始 item 的 43 個 key (gmkNote 只在 gmk = Y 時出現), 依 API 回傳順序
RAW_KEYS = [
    "AA11", "AA12", "a", "b", "bn", "bs", "city", "commid", "cp", "e", "el", "es", "f", "fi", "g", "gmk",
    "gmkNote", "id", "j", "k", "l", "lat", "lon", "m", "mark", "msg", "note", "p", "parkmain", "pimg", "pu",
    "punit", "r", "reid", "s", "sq", "t", "town", "tp", "tunit", "type", "unit", "v",
]


def none_if_blank(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def to_number(value, cast=float):
    value = none_if_blank(value)
    if value is None:
        return None
    try:
        return cast(value.replace(",", "").replace("%", ""))
    except ValueError:
        return None


def to_bool(value):
    value = none_if_blank(value)
    return {"有": True, "無": False}.get(value)


def cn_to_int(value: str):
    """中文數字轉整數, 支援到百位, 例如 二十九 -> 29, 一百零一 -> 101。"""
    if not value:
        return None
    total, current = 0, 0
    for char in value:
        if char in CN_DIGITS:
            current = CN_DIGITS[char]
        elif char == "百":
            total += (current or 1) * 100
            current = 0
        elif char == "十":
            total += (current or 1) * 10
            current = 0
        else:
            return None
    return total + current


def roc_to_date(value):
    """'115/06/01' -> date(2026, 6, 1)。"""
    value = none_if_blank(value)
    if value is None:
        return None
    try:
        year, month, day = (int(part) for part in value.split("/"))
        return date(year + 1911, month, day)
    except ValueError:
        return None


def record_key(item: dict) -> str:
    stable = {k: v for k, v in item.items() if k not in VOLATILE_KEYS}
    payload = json.dumps(stable, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def transform(item: dict, period: str, query_type: str, city: str, town: str) -> dict:
    address_raw = none_if_blank(item.get("a"))
    address = address_raw.split("#")[-1] if address_raw else None

    floor, _, total = (item.get("f") or "").partition("/")
    layout = none_if_blank(item.get("v"))
    # 格局可能缺項, 例: 1房1衛; 有格局但沒寫的項目視為 0
    rooms = halls = baths = None
    if layout:
        rooms, halls, baths = (
            int(match.group(1)) if (match := LAYOUT_RE[part].search(layout)) else 0
            for part in ("房", "廳", "衛")
        )

    parking_wan = to_number(item.get("cp"))
    trade_date = roc_to_date(item.get("e"))

    return {
        "record_key": record_key(item),
        "query_type": query_type,
        "source_period": period,
        "city_code": none_if_blank(item.get("city")),
        "town_code": none_if_blank(item.get("town")),
        "city_name": city,
        "town_name": town,
        "community_id": none_if_blank(item.get("sq")) or none_if_blank(item.get("commid")),
        "building_name": none_if_blank(item.get("bn")),
        "address": address,
        "address_raw": address_raw,
        "trade_date": trade_date.isoformat() if trade_date else None,
        "trade_date_roc": none_if_blank(item.get("e")),
        "total_price": to_number(item.get("tp"), int),
        "unit_price_per_ping": to_number(item.get("p")),
        "unit_price_formula": none_if_blank(item.get("msg")),
        "area_ping": to_number(item.get("s")),
        "parking_price": round(parking_wan * 10000) if parking_wan is not None else None,
        "main_building_ratio": to_number(item.get("bs")),
        "main_building_ratio_ex_parking": to_number(item.get("es")),
        "transaction_target": none_if_blank(item.get("t")),
        "building_type": none_if_blank(item.get("b")),
        "floor": none_if_blank(floor),
        "total_floors": cn_to_int(total.replace("層", "").strip()),
        "age_years": to_number(item.get("g"), int),
        "layout": layout,
        "rooms": rooms,
        "halls": halls,
        "baths": baths,
        "usage": none_if_blank(item.get("pu")),
        "zoning": none_if_blank(item.get("AA11")),
        "has_elevator": to_bool(item.get("el")),
        "has_management": to_bool(item.get("m")),
        "land_count": to_number(item.get("j"), int),
        "building_count": to_number(item.get("k"), int),
        "parking_count": to_number(item.get("l"), int),
        "note": none_if_blank(item.get("note")),
        "lat": item.get("lat"),
        "lon": item.get("lon"),
    }


def find_files(root: Path, periods, query_type, cities, towns):
    for path in sorted(root.glob(f"*/{query_type}/*/*/items.json")):
        period, _, city, town = path.parts[-5:-1]
        if periods and period not in periods:
            continue
        if cities and city not in cities:
            continue
        if towns and town not in towns:
            continue
        yield path, period, city, town


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".cache", help="快取根目錄 (預設 .cache)")
    parser.add_argument("--query-type", default="買賣查詢")
    parser.add_argument("--period", nargs="*", help="期間資料夾, 例: 115_1-115_6 (不給則全部)")
    parser.add_argument("--city", nargs="*", help="縣市, 例: 基隆市 (不給則全部)")
    parser.add_argument("--town", nargs="*", help="行政區, 例: 中正區 (不給則全部)")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true", help="只解析與統計, 不寫入 Supabase")
    parser.add_argument("--csv", help="輸出整理後的資料到 CSV (UTF-8 BOM, Excel 可直接開), 不寫入 Supabase")
    parser.add_argument("--raw", action="store_true", help="搭配 --csv: 原始 43 個 key 直接當欄位, 值不轉換")
    args = parser.parse_args()
    if args.raw and not args.csv:
        parser.error("--raw 只能搭配 --csv 使用")

    files = list(find_files(Path(args.root), args.period, args.query_type, args.city, args.town))
    if not files:
        print("找不到符合條件的 items.json", file=sys.stderr)
        return 1

    # 以 record_key 去重, 避免同一批 upsert 內出現重複鍵而失敗
    rows = {}
    for path, period, city, town in files:
        with open(path, encoding="utf-8") as paper:
            items = json.load(paper)
        for item in items:
            if args.raw:
                rows[record_key(item)] = {key: item.get(key, "") for key in RAW_KEYS}
                continue
            row = transform(item, period, args.query_type, city, town)
            rows[row["record_key"]] = row
    rows = list(rows.values())
    print(f"檔案數：{len(files)}，資料筆數（去重後）：{len(rows)}")

    if args.csv:
        output = Path(args.csv)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8-sig", newline="") as paper:
            writer = csv.DictWriter(paper, fieldnames=RAW_KEYS if args.raw else list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"已輸出 {output}")
        return 0

    if args.dry_run:
        print(json.dumps(rows[0], ensure_ascii=False, indent=2))
        return 0

    from supabase import create_client

    variables = dotenv_values(".env")
    client = create_client(variables["SUPABASE_URL"], variables["SUPABASE_SERVICE_ROLE_KEY"])
    for start in range(0, len(rows), args.batch_size):
        batch = rows[start:start + args.batch_size]
        client.table(TABLE).upsert(batch, on_conflict="record_key").execute()
        print(f"{min(start + args.batch_size, len(rows))}/{len(rows)}", end="\r")
    print(f"\n完成，已寫入 {len(rows)} 筆")
    return 0


if __name__ == "__main__":
    sys.exit(main())
