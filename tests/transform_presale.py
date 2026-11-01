import json
import pandas
import os
import glob
import re


'''
items = [{"a": 1, 'b': 2, ...}, {...}, ...]
把預售屋的 list[{}, ...] 轉換成 pandas table
.cache\115_1-115_6\預售屋查詢
'''

# 預售屋 item 的 key -> 表格欄位名稱 (兩個單字以 _ 串接; 值未轉換, 單位與格式照原始資料)
# 與買賣共用的 key 沿用 transform_sales.py 的名稱; 預售屋沒有 el, gmk, gmkNote, mark, parkmain
mapping = {
    # 位置
    'city': 'city_code',                # 縣市代碼, 例: C (基隆市)
    'town': 'town_code',                # 行政區代碼, 例: C02 (七堵區)
    'a': 'street_address',              # 地址, 沒有 '#', 常為概略位置, 例: 長安街247巷2號之附近
    'bn': 'building_name',              # 建案名稱, 例: 暉騰織光霽
    'bu': 'unit_number',                # 棟別戶號, 例: B棟B1-9F號 (預售屋才有)
    'lat': 'location_latitude',         # 緯度
    'lon': 'location_longitude',        # 經度
    # 價格
    'tp': 'total_price',                # 總價 (元), 例: 22,580,000
    'p': 'unit_price',                  # 單價 (元/坪), 例: 557,831
    'cp': 'parking_price',              # 車位價 (萬元), 例: 200
    'msg': 'price_formula',             # 單價計算方式
    'note': 'trade_note',               # 備註, 例: 露臺戶
    # 交易
    'e': 'trade_date',                  # 交易日期 (民國), 例: 115/06/01
    't': 'trade_target',                # 交易標的, 例: 房地(土地+建物)+車位
    'j': 'land_count',                  # 土地筆數, 建案基地常為多筆, 例: 8
    'k': 'building_count',              # 建物筆數 (推測)
    'l': 'parking_count',               # 車位筆數 (推測)
    'cinfo': 'cancel_info',             # 解約紀錄, 例: 1140417全部解約, 多次以 ';' 分隔 (預售屋才有)
    # 建物
    'b': 'building_type',               # 建物型態, 例: 住宅大樓(11層含以上有電梯)
    'f': 'floor_info',                  # 樓層/總樓層, 阿拉伯數字, 例: 9/15
    'g': 'building_age',                # 屋齡 (年), 預售屋一律為 0
    'v': 'room_layout',                 # 格局, 例: 3房2廳2衛
    's': 'total_area',                  # 總面積 (坪), 含公設與車位
    'bs': 'main_ratio',                 # 主建物佔比, 例: 49.57%
    'es': 'adjusted_ratio',             # 扣除車位後的主建物佔比
    'ma': 'building_material',          # 主要建材, 例: 鋼筋混凝土造 (預售屋才有)
    'm': 'has_management',              # 管理組織, 預售屋一律為空
    'pu': 'usage_type',                 # 用途, 例: 住家用
    'AA11': 'urban_zoning',             # 都市計畫使用分區, 例: 住 / 鄉村區
    'AA12': 'rural_zoning',             # 非都市土地使用編定, AA11 為非都市分區時才有, 例: 乙種建築用地
    # 識別碼
    'reid': 'project_id',               # 建案備查編號 (推測), 同建案相同, 例: G2C011501080001
    'sq': 'community_id',               # 加密的 ID, 預售屋每筆皆不同
    'commid': 'community_alias',        # 預售屋一律為空
    'id': 'query_index',                # 該次查詢結果的流水號, 每次查詢可能不同
    # 網頁顯示用, 意義不明或用途有限
    # 'r': 'field_r',
    # 'type': 'record_type',              # 預售屋一律為 Sale
    # 'pimg': 'icon_image',
    # 'unit': 'base_unit',
    # 'punit': 'price_unit',
    # 'tunit': 'total_unit',
    # 'fi': 'field_fi',
}

paths = glob.glob("C:/Users/houzeyu2683/Projects/realtime-data-monitoring-system/.cache/*/預售屋查詢/*/*/*.json")
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
