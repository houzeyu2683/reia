import json
import os
import glob


'''
建立 縣市 -> 行政區名稱 -> 行政區代碼 的 mapping, 存成 town_codes.json
租賃 item 沒有 town 代碼, 由買賣/預售屋 item 的 town 對照資料夾名稱整理而來
.cache/<期間>/<查詢類型>/<縣市>/<行政區>/items.json
'''

# 買賣/預售屋都沒有成交紀錄的行政區, 無法從資料取得代碼, 手動補上
supplement = {
    '臺東縣': {
        '蘭嶼鄉': 'V16',                # 臺東縣其他鄉鎮為 V01-V15, 依順序推定
    },
}

codes = {}
for title in ['買賣查詢', '預售屋查詢']:
    paths = glob.glob(f"C:/Users/houzeyu2683/Projects/realtime-data-monitoring-system/.cache/*/{title}/*/*/items.json")
    for path in paths:
        town = os.path.basename(os.path.dirname(path))
        city = os.path.basename(os.path.dirname(os.path.dirname(path)))
        with open(path, 'r', encoding='utf-8') as paper:
            items = json.load(paper)
            pass
        if not items: continue
        code = items[0]['town']
        known = codes.setdefault(city, {}).setdefault(town, code)
        assert known == code, f'{city}{town} 出現多個代碼: {known}, {code}'
        continue
    continue

for city in supplement:
    for town in supplement[city]:
        codes.setdefault(city, {}).setdefault(town, supplement[city][town])
        continue
    continue

# 依代碼排序, 例: 臺北市 A01, A02, ...
codes = {
    city: dict(sorted(codes[city].items(), key=lambda x: x[1]))
    for city in sorted(codes, key=lambda x: min(codes[x].values()))
}
path = os.path.join(os.path.dirname(__file__), 'town_codes.json')
with open(path, 'w', encoding='utf-8') as paper:
    json.dump(codes, paper, ensure_ascii=False, indent=4)
    pass
print(f'縣市：{len(codes)}，行政區：{sum(len(towns) for towns in codes.values())}')
