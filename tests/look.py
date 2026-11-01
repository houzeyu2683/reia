import glob
import pandas

tables = []
paths = glob.glob("C:/Users/houzeyu2683/Projects/realtime-data-monitoring-system/.cache/*/預售屋查詢/*/*/*.csv")
for path in paths:
    if '108' in path: continue
    if '109' in path: continue
    if '110' in path: continue
    if '111' in path: continue
    if '112' in path: continue
    if '113' in path: continue

    if (
        # '嘉義市' in path,
        # '嘉義縣' in path,
        # '基隆市' in path,
        # '宜蘭縣' in path,
        '新北市' in path or
        # '新竹市' in path,
        # '新竹縣' in path,
        '桃園市' in path or
        '臺中市' in path or
        '臺北市' in path or
        '臺南市' in path or
        '高雄市' in path
        # '115' in path or
        # '114' in path or
        # '113' in path or
        # '112' in path or
        # '111' in path
    ):
        tables += [pandas.read_csv(path)]
        pass
    continue
frame = pandas.concat(tables, axis=0)
frame = pandas.DataFrame(frame).sort_values(by='trade_date').reset_index(drop=True)
# frame = pandas.DataFrame(frame).sort_values(by='lease_date').reset_index(drop=True)
# frame['main_index'] = frame.index
frame.insert(0, 'presale_index', frame.index)
frame.to_csv('presale.csv', encoding='utf-8', index=False)
# empty = frame.isna().sum(axis=0) / len(frame)
# print(empty)
