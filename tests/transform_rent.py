import json
import pandas
import os
import glob
import re


'''
items = [{"a": 1, 'b': 2, ...}, {...}, ...]
把租賃的 list[{}, ...] 轉換成 pandas table
.cache\115_1-115_6\租賃查詢
'''

# 租賃 item 的 key -> 表格欄位名稱 (兩個單字以 _ 串接; 值未轉換, 單位與格式照原始資料)
# 與買賣共用的 key 沿用 transform_sales.py 的名稱, 但價格類的意義不同 (月租金), 改用租賃的名稱
# 租賃沒有 town, gmk, gmkNote, mark, parkmain, reid; town_code 由資料夾名稱查 town_codes.json 補上
mapping = {
    # 位置
    'city': 'city_code',                # 縣市代碼, 例: C (基隆市)
    'a': 'street_address',              # 地址, 開頭為行政區, 例: 七堵區東新街８３之５號７樓
    'bn': 'building_name',              # 社區名稱, 多為空
    'lat': 'location_latitude',         # 緯度
    'lon': 'location_longitude',        # 經度
    # 租金
    'tp': 'monthly_rent',               # 月租金 (元), 例: 18,000
    'p': 'unit_rent',                   # 每坪月租金 (元/坪), 例: 549, 偶爾為空
    'cp': 'parking_rent',               # 車位月租金 (元), 例: 3,000, 多為空
    'msg': 'price_formula',             # 單價計算方式, 例: 總價/總面積
    'note': 'trade_note',               # 備註, 例: 續租案件; 租金總額含稅;
    # 租約
    'e': 'lease_date',                  # 租約日期 (民國), 例: 115/06/03
    'rperiod': 'lease_period',          # 租賃期間 (民國), 例: 1150607~1160606 (租賃才有)
    'rtype': 'rental_type',             # 出租型態, 例: 整戶出租 / 獨立套房 / 分租套房 (租賃才有)
    'rserviec': 'rental_service',       # 租賃住宅服務, 例: 社會住宅代管 (租賃才有, 原 key 拼字如此)
    't': 'trade_target',                # 交易標的, 例: 租賃房屋 / 租賃房屋+車位
    'j': 'land_count',                  # 土地筆數 (推測)
    'k': 'building_count',              # 建物筆數 (推測)
    'l': 'parking_count',               # 車位筆數 (推測)
    'ho': 'room_count',                 # 分租房間數 (推測), 多為空 (租賃才有)
    # 建物
    'b': 'building_type',               # 建物型態, 例: 公寓(5樓含以下無電梯)
    'f': 'floor_info',                  # 樓層/總樓層, 例: 七層/十層
    'g': 'building_age',                # 屋齡 (年)
    'v': 'room_layout',                 # 格局, 例: 3房2廳1衛
    's': 'total_area',                  # 總面積 (坪), 分租套房為整戶面積而非套房面積
    'bs': 'main_ratio',                 # 主建物佔比, 租賃一律為空
    'es': 'adjusted_ratio',             # 扣除車位後的主建物佔比, 租賃一律為空
    'fn': 'included_equipment',         # 附屬設備, 例: 冷氣、熱水器、洗衣機; 舊資料常只寫 有 (租賃才有)
    'el': 'has_elevator',               # 電梯 (有/無)
    'm': 'has_management',              # 管理組織 (有/無)
    'ms': 'has_manager',                # 管理員 (有/無) (推測, 租賃才有)
    'pu': 'usage_type',                 # 用途, 例: 住家用
    'AA11': 'urban_zoning',             # 都市計畫使用分區, 例: 住 / 商, 多為空
    'AA12': 'rural_zoning',             # 非都市土地使用編定, AA11 為非都市分區時才有
    # 識別碼
    # 'commid': 'case_number',            # 案件編號 (推測), 例: C1CD1150513000401, 多為空
    'sq': 'community_id',               # 加密的 ID, 每筆皆不同
    # 'id': 'query_index',                # 該次查詢結果的流水號, 每次查詢可能不同
    # 網頁顯示用, 意義不明或用途有限
    # 'r': 'field_r',
    # 'type': 'record_type',              # 租賃一律為 Rent
    # 'pimg': 'icon_image',
    # 'unit': 'base_unit',
    # 'punit': 'price_unit',
    # 'tunit': 'total_unit',
    # 'fi': 'field_fi',
}


# 縣市 -> 行政區名稱 -> 行政區代碼, 由買賣/預售屋資料的 town 整理而來 (蘭嶼鄉 V16 為推定)
with open(os.path.join(os.path.dirname(__file__), 'town_codes.json'), 'r', encoding='utf-8') as paper:
    codes = json.load(paper)
    pass

paths = glob.glob("C:/Users/houzeyu2683/Projects/realtime-data-monitoring-system/.cache/*/租賃查詢/*/*/*.json")
for path in paths:
    archive = os.path.join(
        os.path.dirname(path),
        os.path.basename(path).replace(".json", ".csv")
    )
    # 租賃 item 沒有 town, 從 .cache/<期間>/租賃查詢/<縣市>/<行政區>/items.json 的資料夾名稱查出代碼
    city = os.path.basename(os.path.dirname(os.path.dirname(path)))
    town = codes[city][os.path.basename(os.path.dirname(path))]
    with open(path, 'r', encoding='utf-8') as paper:
        items = json.load(paper)
        pass
    len(items)
    data = pandas.DataFrame(items)
    if data.empty:
        frame = pandas.DataFrame({name: [] for name in mapping.values()})
    else:
        frame = data[list(mapping.keys())].rename(columns=mapping)
    frame.insert(frame.columns.get_loc('city_code') + 1, 'town_code', town)
    frame.to_csv(archive, index=False)
    continue
