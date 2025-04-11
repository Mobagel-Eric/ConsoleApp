import requests
import json
import pyodbc
from datetime import datetime, timedelta
import calendar
import requests
import csv
from io import StringIO

import twstock #股票套件

# 資料庫連線設定
server = 'localhost'
database = 'ConsoleAppDB'
username = 'mobagel'
password = 'mobagel'
connection_string = f'''
    DRIVER={{ODBC Driver 17 for SQL Server}};
    SERVER={server};
    DATABASE={database};
    UID={username};
    PWD={password};
'''

#獲得所有股票代碼
csv_url = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=20240410&type=ALL'

response = requests.get(csv_url)
response.encoding = 'utf-8'

valid_stock_list = []

if response.status_code == 200:
    raw = response.text
    # 處理資料列
    csv_data = csv.reader(StringIO(raw))
    for row in csv_data:
        if len(row) > 1 and row[0].isdigit():  # 股票代碼為數字
            stock_no = row[0].strip()
            valid_stock_list.append(stock_no)

print(valid_stock_list)
print(f"共抓到 {len(valid_stock_list)} 支有效股票代碼")

# 計算過去三年的每個月份起始日（TWSE 要求格式 YYYYMMDD）
def get_last_3_years_month_starts():
    today = datetime.today()
    dates = []
    #今年、去年、大去年
    for y in range(today.year - 2, today.year + 1):
        #1月~
        for m in range(1, 13):
            if y == today.year and m > today.month:
                break
            dates.append(f"{y}{str(m).zfill(2)}01")  # 每月第一天
    return dates

# 開始抓資料
for stock_no in valid_stock_list:
    test_date = datetime.today().strftime('%Y%m01')
    test_url = f'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={test_date}&stockNo={stock_no}'
    test_response = requests.get(test_url)
    test_response.encoding = 'utf-8'

    if test_response.status_code != 200:
        print(f"{stock_no}：無法連接網站，跳過")
        continue

    test_data = test_response.json()
    if test_data.get('stat') != 'OK':
        print(f"{stock_no}：查詢失敗（無資料或非上市公司），跳過")
        continue

    for date in get_last_3_years_month_starts():
        url = f'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date}&stockNo={stock_no}'
        response = requests.get(url)
        response.encoding = 'utf-8'

        if response.status_code == 200:
            data = response.json()
            if data['stat'] == 'OK':
                rows = data['data']
                try:
                    with pyodbc.connect(connection_string) as conn:
                        cursor = conn.cursor()
                        for row in rows:
                            full_title = data.get("title", "")
                            # 用 split + strip 擷取
                            import re
                            match = re.search(r"\d{4}\s+[\u4e00-\u9fa5]+", full_title)
                            stock_info = match.group().strip() if match else ""

                            # 清理數字字串中的逗號
                            cleaned_row = [
                                row[0].replace("/", "-"),                      # 日期：轉為 YYYY-MM-DD
                                int(row[1].replace(',', '')),                 # 成交股數
                                int(row[2].replace(',', '')),                 # 成交金額
                                float(row[3].replace(',', '')),               # 開盤價
                                float(row[4].replace(',', '')),               # 最高價
                                float(row[5].replace(',', '')),               # 最低價
                                float(row[6].replace(',', '')),               # 收盤價
                                row[7],                                       # 漲跌價差（可能含符號）
                                int(row[8].replace(',', '')),                 # 成交筆數
                                int(stock_no),                                # 股票代碼
                                stock_info                                    # 股票名稱
                            ]

                            #避免重複
                            check_query = '''
                                SELECT COUNT(*) FROM TWSE_Stock_Data
                                WHERE 
                                    date = ? AND
                                    stock_no = ?
                                '''
                            cursor.execute(check_query, (cleaned_row[0], cleaned_row[9]))
                            
                            insert_query = '''
                            INSERT INTO TWSE_Stock_Data 
                            (date, volume, turnover, open_price, high, low, close_price, change, trades, stock_no,stock_name)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            '''

                            #沒有重複，就新增進入DB
                            if cursor.fetchone()[0] == 0:
                                cursor.execute(insert_query, cleaned_row)
                                print(f"{stock_no} - {date}：資料插入成功，共 {len(rows)} 筆")
                            else:
                                print("已經有這筆資料了！")
                        conn.commit()
                except Exception as e:
                    print(f"{stock_no} - {date}：資料插入失敗：{e}")
            else:
                print(f"{stock_no} - {date}：查詢失敗，訊息：{data['stat']}")
        else:
            print(f"{stock_no} - {date}：HTTP請求失敗，狀態碼：{response.status_code}")
