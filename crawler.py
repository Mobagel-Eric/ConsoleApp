import pyodbc
import requests
from bs4 import BeautifulSoup

server = 'localhost' # SQL 主機名稱
database = 'ConsoleAppDB' # 資料庫名稱
username = 'mobagel' # 使用者帳號(資料庫)
password = 'mobagel' # 使用者密碼(資料庫)

#資料庫連線設定
connection_string = f'''
    DRIVER={{ODBC Driver 17 for SQL Server}};
    SERVER={server};
    DATABASE={database};
    UID={username};
    PWD={password};
'''

url = 'https://linyencheng.github.io/2021/10/05/python-crawler/'

response = requests.get(url)

response.encoding = 'utf-8' #設定字元編碼

if response.status_code == 200:
    soup = BeautifulSoup(response.text,'html.parser')

    #網頁標題
    title = soup.find('title').text.strip()
    print(f"\n 網頁標題：{title}\n")

    # paragraphs = soup.find_all('p')
    
    # for idx,p in enumerate(paragraphs,1):
    #     text = p.text.strip()
    #     if text:
    #         print(f"{idx:02d}:{text}")

    #get_text()可以用來擷取HTML或是XML的所有文字內容。
    #separator代表分隔符號，strip默認是True，表示去除開頭跟結尾的空白字符。
    body_text = soup.get_text(separator="\n",strip=True)

    print("\n 網頁全部文字：")
    print(body_text)

else:
    print("網頁抓取失敗，狀態碼：",response.status_code)

