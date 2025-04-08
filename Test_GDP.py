import pyodbc
import requests
from bs4 import BeautifulSoup

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

# 測試資料網站
url = 'https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)'

# 發送 HTTP GET 請求
response = requests.get(url)
response.encoding = 'utf-8'

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    # 找到所有的表格
    tables = soup.find_all('table', {'class': 'wikitable'})

    # 假設我們要抓取第一個表格
    target_table = tables[0]

    # 解析表格標頭
    headers = [header.text.strip() for header in target_table.find_all('th')]

    # 解析表格內容
    rows = []
    for row in target_table.find_all('tr')[1:]:
        cells = row.find_all('td')
        if len(cells) > 0:
            row_data = [cell.text.strip() for cell in cells]
            rows.append(row_data)

    # 將資料插入 SQL Server
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            for i, row in enumerate(rows):
                # 防止欄位不足造成錯誤
                if len(row) < 7:
                    print(f"第 {i+1} 筆資料欄位不足，略過：{row}")
                    continue

                # 處理特殊值，如 em dash（—）
                def clean(value):
                    cleaned = value.replace("—", "").replace("[n 1]", "").replace("[n 3]", "").replace("[n 4]", "").strip()
                    return None if cleaned == '' else cleaned

                # 準備清理後的資料
                country = clean(row[0])
                forecast = clean(row[1])
                forecast_year = clean(row[2])
                world_bank_est = clean(row[3])
                world_bank_year = clean(row[4])
                un_est = clean(row[5])
                un_year = clean(row[6])

                #查詢是否有填寫過
                check_query = '''
                SELECT COUNT(*) FROM Test_GDP
                WHERE Country = ? AND Forecast = ? AND Forecast_Year = ? AND
                    World_Bank_Estimate = ? AND World_Bank_Year = ? AND
                    United_Nations_Estimate = ? AND United_Nations_Year = ?
                '''
                cursor.execute(check_query, country, forecast, forecast_year,
                            world_bank_est, world_bank_year, un_est, un_year)
                exists = cursor.fetchone()[0]

                #如果沒有新增過，那就新增進去
                if exists == 0:
                    insert_query = '''
                    INSERT INTO Test_GDP (Number, Country, Forecast, Forecast_Year, 
                                        World_Bank_Estimate, World_Bank_Year, 
                                        United_Nations_Estimate, United_Nations_Year)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    cursor.execute(insert_query, str(i+1), country, forecast, forecast_year,
                                world_bank_est, world_bank_year, un_est, un_year)
                    print(f"✅ 插入第 {i+1} 筆：{country}")
                else:
                    print(f"⚠️ 已存在第 {i+1} 筆：{country}，略過")

            conn.commit()
            print("資料插入成功")
    except Exception as e:
        print(f"資料插入失敗: {e}")
else:
    print(f"網頁抓取失敗，狀態碼：{response.status_code}")