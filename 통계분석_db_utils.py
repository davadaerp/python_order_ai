import sqlite3

def save_to_db(data, db_file='OrderStatistics.db'):
    # SQLite3 데이터베이스 연결
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 주문 테이블 생성 (주소 추가)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_date TEXT,
            company_code TEXT,
            business_number TEXT,
            company_name TEXT,
            region TEXT,
            region_detail TEXT,
            business_category TEXT,
            business_type TEXT,
            business_detail TEXT,
            orders TEXT,
            af_orders TEXT,
            address TEXT,  -- 주소 추가
           latitude REAL DEFAULT 0,  -- 위도 기본값 0
            longitude REAL DEFAULT 0  -- 경도 기본값 0
        )
    ''')

    # 품목 주문 상세 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_code TEXT,
            product_name TEXT,
            alcohol_type TEXT,
            product_price INTEGER,
            quantity INTEGER,
            total_price INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
        )
    ''')

    # 데이터를 테이블에 삽입
    for order in data:
        # 위도와 경도 값 가져오기
        latitude = order.get('latitude', 0)  # 기본값 0으로 설정
        longitude = order.get('longitude', 0)  # 기본값 0으로 설정
        address = order.get('address')  # 주소 값 가져오기

        # 주문 테이블에 삽입 (주소, 위도, 경도 값 추가)
        cursor.execute('''
            INSERT INTO orders (order_date, company_code, business_number, company_name, region, region_detail, business_category, business_type, business_detail, orders, af_orders, address, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order['order_date'], order['company_code'], order['business_number'], order['company_name'],
              order['region'], order['region_detail'],
              order['business_category'], order['business_type'], order['business_detail'],
              order['orders'], order['af_orders'],
              address, latitude, longitude))

        # 방금 삽입한 주문의 ID 가져오기
        order_id = cursor.lastrowid

        # 품목 주문 상세 테이블에 삽입
        for item in order['order_items']:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_code, product_name, alcohol_type, product_price, quantity, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, item['product_code'], item['product_name'], item['alcohol_type'],
                  item['product_price'], item['quantity'], item['total_price']))

    # 커밋 후 연결 종료
    conn.commit()
    conn.close()
