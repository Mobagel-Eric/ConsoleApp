import pyodbc

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

try:
    #建立連線
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print("成功連線到SQL Server！")

    #查詢Test 資料表(執行SQL查詢)
    cursor.execute("Select Name,Number FROM Test")

    for row in cursor.fetchall():
        print(f"Name:{row.Name},Number:{row.Number}")

    conn.close()

except Exception as e:
    print("發生錯誤：",e)
