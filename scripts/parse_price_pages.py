"""將 .cache/買賣查詢/<縣市>/<行政區>/page_XXXX.html 抽取成單一 CSV。

用法:
    python scripts/parse_price_pages.py [輸入目錄或檔案 ...] [-o 輸出.csv]
預設輸入 .cache/買賣查詢,預設輸出 output/sale_records.csv。
"""
import argparse
import csv
import html
import re
import sys
from pathlib import Path

TYPE_NAMES = {
    "01": "公寓", "02": "透天厝", "03": "店面", "04": "辦公大樓",
    "05": "住宅大樓", "06": "華廈", "07": "套房", "08": "工廠",
    "09": "廠辦", "10": "農舍", "11": "倉庫", "A": "土地",
}
SPECIAL_KEYWORDS = ("親友", "員工", "共有人", "特殊關係", "法拍", "債權債務", "增建", "頂樓加蓋", "未登記", "預售")
CN_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

FIELDS = [
    "city", "district", "page", "address", "community", "total_price_wan", "trade_date_roc", "trade_date",
    "unit_price_wan_ping", "area_ping", "main_building_ratio", "type_code", "type_name", "age_year",
    "floor", "total_floors", "purpose", "land_cnt", "building_cnt", "parking_cnt", "layout", "rooms",
    "halls", "baths", "parking_price_wan", "management", "elevator", "remark", "is_special_trade",
]

ROW_RE = re.compile(r'<tr role="row".*?</tr>', re.S)
TD_RE = re.compile(r"<td.*?</td>", re.S)
HIDDEN_SPAN_RE = re.compile(r'<span style="display:none;">.*?</span>', re.S)
TAG_RE = re.compile(r"<[^>]+>")


def text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub("", fragment))).strip()


def num(value: str):
    value = value.replace(",", "").strip()
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return ""


def cn_to_int(value: str):
    """一~九十九的中文數字轉整數,例如 二十二 -> 22。"""
    if not value:
        return ""
    if "十" in value:
        tens, _, ones = value.partition("十")
        return (CN_DIGITS.get(tens, 1)) * 10 + CN_DIGITS.get(ones, 0)
    return CN_DIGITS.get(value, "")


def parse_floor(raw: str):
    """'七層/十三層' -> ('七層', 13);'全/二層' -> ('全', 2)。"""
    floor, _, total = raw.partition("/")
    total_n = cn_to_int(total.replace("層", "").strip())
    return floor.strip(), total_n


def parse_date(roc: str) -> str:
    m = re.fullmatch(r"(\d+)/(\d+)/(\d+)", roc)
    return f"{int(m[1]) + 1911:04d}-{int(m[2]):02d}-{int(m[3]):02d}" if m else ""


def parse_row(row_html: str) -> dict:
    tds = TD_RE.findall(row_html)
    cells = [text(HIDDEN_SPAN_RE.sub("", td)) for td in tds]
    cells += [""] * (19 - len(cells))

    type_code = ""
    m = re.search(r'<span style="display:none;">bt(\w+)</span>', row_html)
    if m:
        type_code = m[1]

    target = re.search(r"土\s*(\d+)\s*建\s*(\d+)\s*車\s*(\d+)", cells[11])
    land, building, parking = target.groups() if target else ("", "", "")

    layout = cells[12]
    lm = re.search(r"(\d+)房(\d+)廳(\d+)衛", layout)
    rooms, halls, baths = lm.groups() if lm else ("", "", "")

    floor, total_floors = parse_floor(cells[9])
    remark = cells[18]

    return {
        "address": cells[0],
        "community": cells[1],
        "total_price_wan": num(cells[2]),
        "trade_date_roc": cells[3],
        "trade_date": parse_date(cells[3]),
        "unit_price_wan_ping": num(cells[4]),
        "area_ping": num(cells[5]),
        "main_building_ratio": num(cells[6]),
        "type_code": type_code,
        "type_name": TYPE_NAMES.get(type_code, type_code),
        "age_year": num(cells[8]),
        "floor": floor,
        "total_floors": total_floors,
        "purpose": cells[10],
        "land_cnt": land,
        "building_cnt": building,
        "parking_cnt": parking,
        "layout": layout,
        "rooms": rooms,
        "halls": halls,
        "baths": baths,
        "parking_price_wan": num(cells[13]),
        "management": cells[14],
        "elevator": cells[15],
        "remark": remark,
        "is_special_trade": int(any(k in remark for k in SPECIAL_KEYWORDS)),
    }


def parse_file(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8", errors="replace")
    start = content.find('id="table-item-tbody"')
    if start < 0:
        return []
    body = content[start:content.find("</tbody>", start)]

    district, city = path.parent.name, path.parent.parent.name
    page_m = re.search(r"page_(\d+)", path.name)
    page = int(page_m[1]) if page_m else ""

    records = []
    for row in ROW_RE.findall(body):
        rec = parse_row(row)
        rec.update(city=city, district=district, page=page)
        records.append(rec)
    return records


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="*", default=[".cache/買賣查詢"])
    ap.add_argument("-o", "--output", default="output/sale_records.csv")
    args = ap.parse_args()

    all_records = []
    for item in args.inputs:
        p = Path(item)
        files = sorted(p.rglob("page_*.html")) if p.is_dir() else [p]
        for f in files:
            all_records.extend(parse_file(f))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as fh:  # utf-8-sig 讓 Excel 正確顯示中文
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_records)
    print(f"{len(all_records)} 筆 -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
