import json
import pandas
import os
import glob
import re


'''
items = [{"a": 1, 'b': 2, ...}, {...}, ...]
我想把一個 list[{}, ...] 轉換成 pndas table
.cache\114_1-114_12
'''

# 實價登錄 item 的 key -> 表格欄位名稱 (兩個單字以 _ 串接; 值未轉換, 單位與格式照原始資料)
mapping = {
    # 位置
    'city': 'city_code',                # 縣市代碼, 例: C (基隆市)
    'town': 'town_code',                # 行政區代碼, 例: C01 (中正區)
    'a': 'street_address',              # 地址, '#' 前為全形補零寫法, 後為一般寫法
    'bn': 'building_name',              # 社區/建案名稱, 例: 港都明珠
    'lat': 'location_latitude',         # 緯度
    'lon': 'location_longitude',        # 經度
    # 價格
    'tp': 'total_price',                # 總價 (元), 例: 20,550,000
    'p': 'unit_price',                  # 單價 (元/坪), 例: 459,845
    'cp': 'parking_price',              # 車位價 (萬元), 例: 160
    'msg': 'price_formula',             # 單價計算方式
    'note': 'trade_note',               # 備註, 例: 土地價款...建物價款...
    # 交易
    'e': 'trade_date',                  # 交易日期 (民國), 例: 115/06/01
    't': 'trade_target',                # 交易標的, 例: 房地(土地+建物)+車位
    'j': 'land_count',                  # 土地筆數 (推測)
    'k': 'building_count',              # 建物筆數 (推測)
    'l': 'parking_count',               # 車位筆數 (推測)
    # 建物
    'b': 'building_type',               # 建物型態, 例: 住宅大樓(11層含以上有電梯)
    'f': 'floor_info',                  # 樓層/總樓層, 例: 十二層/二十九層
    'g': 'building_age',                # 屋齡 (年)
    'v': 'room_layout',                 # 格局, 例: 3房2廳2衛
    's': 'total_area',                  # 總面積 (坪), 含公設與車位
    'bs': 'main_ratio',                 # 主建物佔比, 例: 51.95%
    'es': 'adjusted_ratio',             # 扣除車位後的主建物佔比
    'el': 'has_elevator',               # 電梯 (有/無)
    'm': 'has_management',              # 管理組織 (有/無)
    'pu': 'usage_type',                 # 用途, 例: 住家用
    'AA11': 'urban_zoning',             # 都市計畫使用分區, 例: 商/住
    'AA12': 'rural_zoning',             # 非都市土地使用分區 (推測, 多為空)
    # 'gmk': 'energy_label',              # 有無建築能效標示 (Y/N)
    # 'gmkNote': 'energy_note',           # 建築能效說明, 只在 gmk=Y 時出現
    # 識別碼
    'sq': 'community_id',               # 加密的社區 ID
    'commid': 'community_alias',        # 與 sq 相同
    'id': 'query_index',                # 該次查詢結果的流水號, 每次查詢可能不同
    # 網頁顯示用, 意義不明或用途有限
    # 'r': 'field_r',
    # 'type': 'record_type',
    # 'pimg': 'icon_image',
    # 'unit': 'base_unit',
    # 'punit': 'price_unit',
    # 'tunit': 'total_unit',
    # 'parkmain': 'parking_main',
    # 'mark': 'field_mark',
    # 'fi': 'field_fi',
    # 'reid': 'field_reid',
}

paths = glob.glob("C:/Users/houzeyu2683/Projects/realtime-data-monitoring-system/.cache/*/買賣查詢/*/*/*.json")
for path in paths:
    archive = os.path.join(
        os.path.dirname(path),
        os.path.basename(path).replace(".json", ".csv")
    )
    with open(path, 'r', encoding='utf-8') as paper:
        items = json.load(paper)
        pass
    len(items)
    data = pandas.DataFrame(items)
    if data.empty:
        frame = pandas.DataFrame({name: [] for name in mapping.values()})
        frame.to_csv(archive, index=False)
        continue
    frame = data[list(mapping.keys())].rename(columns=mapping)
    frame.to_csv(archive, index=False)
    continue

'''

'''





