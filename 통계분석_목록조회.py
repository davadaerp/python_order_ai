import sqlite3
import pandas as pd
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

app = Flask(__name__)

# SQLite3 데이터베이스에서 데이터를 불러오는 함수
def get_orders_from_db(year=None, month=None, business_type=None, region=None, company_name=None, db_file='OrderStatistics.db'):
    conn = sqlite3.connect(db_file)
    query = '''
    SELECT o.order_id, o.order_date, o.company_name, o.region, o.business_type, o.orders AS order_description, o.af_orders AS order_after, 
            o.address, o.latitude, o.longitude,
            SUM(CAST(REPLACE(oi.total_price, ',', '') AS INTEGER)) AS total_price
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    '''

    conditions = []
    if year and year != '전체':
        conditions.append(f"strftime('%Y', o.order_date) = '{year}'")
    if month and month != '전체':
        conditions.append(f"strftime('%m', o.order_date) = '{month:02}'")
    if business_type and business_type != '전체':
        conditions.append(f"o.business_type = '{business_type}'")
    if region and region != '전체':
        conditions.append(f"o.region = '{region}'")
    if company_name != '':
        conditions.append(f"o.company_name LIKE '%{company_name}%'")

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' GROUP BY o.order_id, o.order_date, o.region, o.business_type'

    # Limit the results to 500 rows
    query += ' LIMIT 500'

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# SQLite3에서 주문 품목을 가져오는 함수
def get_order_items_from_db(order_id, db_file='OrderStatistics.db'):
    conn = sqlite3.connect(db_file)
    query = '''
    SELECT oi.product_code, oi.product_name, oi.alcohol_type, oi.product_price, oi.quantity, oi.total_price
    FROM order_items oi
    WHERE oi.order_id = ?
    '''
    df = pd.read_sql_query(query, conn, params=(order_id,))
    conn.close()
    return df

@app.route('/', methods=['GET', 'POST'])
def view_index():
    # 기본값 설정
    selected_year = request.form.get('year', '전체')
    selected_month = request.form.get('month', '전체')
    selected_business_type = request.form.get('business_type', '전체')
    selected_region = request.form.get('region', '전체')

    # 데이터 가져오기
    df = get_orders_from_db(year=selected_year, month=selected_month, business_type=selected_business_type, region=selected_region)

    # 연도 및 월 목록 생성
    conn = sqlite3.connect('OrderStatistics.db')
    #year_list = pd.read_sql_query("SELECT DISTINCT strftime('%Y', order_date) AS year FROM orders", conn)['year'].tolist()
    # -5년부터 현재 연도까지의 연도 목록 생성 (역순)
    # 현재 연도 가져오기
    current_year = datetime.now().year
    year_list = [str(year) for year in range(current_year, current_year - 5, -1)]
    month_list = [f"{i:02}" for i in range(1, 13)]
    business_type_list = pd.read_sql_query("SELECT DISTINCT business_type FROM orders", conn)['business_type'].tolist()
    region_list = pd.read_sql_query("SELECT DISTINCT region FROM orders", conn)['region'].tolist()
    conn.close()

    year_list.insert(0, '전체')
    month_list.insert(0, '전체')
    business_type_list.insert(0, '전체')
    region_list.insert(0, '전체')

    html_content = '''
    <html>
    <head>
        <title>Order Statistics</title>
        <style>
            /* 팝업 스타일 */
            #popup {
                display: none;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: white;
                border: 1px solid #ccc;
                padding: 20px;
                z-index: 1000;
                width: 60%;
                max-width: 600px;
            }
            #popup .popup-content {
                max-height: 400px;
                overflow-y: auto;
            }
            #popup-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 999;
            }
            /* 버튼 스타일 */
            .popup-button {
                color: blue;
                cursor: pointer;
            }
        </style>
        <script>
            // 팝업을 열고 닫는 함수
            function openPopup(orderId) {
                var overlay = document.getElementById('popup-overlay');
                var popup = document.getElementById('popup');
                var content = document.getElementById('popup-content');
                overlay.style.display = 'block';
                popup.style.display = 'block';
        
                // 주문 ID에 해당하는 품목 목록을 가져옵니다.
                fetch('/get_order_items?order_id=' + orderId)
                    .then(response => response.json())
                    .then(data => {
                        content.innerHTML = '<h3>품목 목록</h3>';
                        if (data.items.length > 0) {
                            // 테이블 형식으로 품목 목록 표시
                            let table = document.createElement('table');
                            table.style.border = '1px solid black';
                            table.style.borderCollapse = 'collapse';
                            let thead = document.createElement('thead');
                            let tbody = document.createElement('tbody');
                            
                            // 헤더 추가
                            let headerRow = document.createElement('tr');
                            ['품목 코드', '품목명', '주종', '단가', '수량', '금액'].forEach(text => {
                                let th = document.createElement('th');
                                th.textContent = text;
                                th.style.border = '1px solid black';
                                th.style.padding = '5px';
                                headerRow.appendChild(th);
                            });
                            thead.appendChild(headerRow);
                            table.appendChild(thead);
                            
                            // 품목 내용 추가
                            data.items.forEach(item => {
                                let row = document.createElement('tr');
                                ['product_code', 'product_name', 'main_type', 'unit_price', 'quantity', 'total_price'].forEach(field => {
                                    let td = document.createElement('td');
                                    if (field === 'unit_price' || field === 'total_price') {
                                        td.textContent = '₩' + item[field].toLocaleString();
                                    } else {
                                        td.textContent = item[field];
                                    }
                                    td.style.border = '1px solid black';
                                    td.style.padding = '5px';
                                    row.appendChild(td);
                                });
                                tbody.appendChild(row);
                            });
                            table.appendChild(tbody);
                            content.appendChild(table);
                        } else {
                            content.innerHTML += '<p>품목이 없습니다.</p>';
                        }
                        
                        // 닫기 버튼 추가
                        content.innerHTML += '<br><button onclick="closePopup()">닫기</button>';
                    });
            }
        
            // 팝업을 닫는 함수
            function closePopup() {
                document.getElementById('popup').style.display = 'none';
                document.getElementById('popup-overlay').style.display = 'none';
            }
            
            // Google Maps 위치 이동 함수
            function moveToLocation(latitude, longitude, address) {
                const googleMapsUrl = address
                ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)} (${latitude},${longitude})`
                : `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;
                
                // 팝업 창 옵션 설정
                const popupOptions = 'width=1024,height=900,top=100,left=500,scrollbars=yes,resizable=yes';
                window.open(googleMapsUrl, '_blank', popupOptions);
            }
        </script>
    </head>
    <body>
        <h1>주문 목록</h1>

        <form method="post">
            <label for="year">년도:</label>
            <select name="year" id="year" onchange="this.form.submit()">
                {% for year in year_list %}
                    <option value="{{ year }}" {% if selected_year == year %}selected{% endif %}>{{ year }}</option>
                {% endfor %}
            </select>

            <label for="month">월:</label>
            <select name="month" id="month" onchange="this.form.submit()">
                {% for month in month_list %}
                    <option value="{{ month }}" {% if selected_month == month %}selected{% endif %}>{{ month }}</option>
                {% endfor %}
            </select>

            <label for="business_type">업종:</label>
            <select name="business_type" id="business_type" onchange="this.form.submit()">
                {% for business_type in business_type_list %}
                    <option value="{{ business_type }}" {% if selected_business_type == business_type %}selected{% endif %}>{{ business_type }}</option>
                {% endfor %}
            </select>
            
            <label for="region">지역:</label>
            <select name="region" id="region" onchange="this.form.submit()">
                {% for region in region_list %}
                    <option value="{{ region }}" {% if selected_region == region %}selected{% endif %}>{{ region }}</option>
                {% endfor %}
            </select>
            
        </form>

        {% if df.empty %}
            <p>선택한 조건에 해당하는 데이터가 없습니다.</p>
        {% else %}
            <table border="1">
                <thead>
                    <tr>
                        <th>주문 ID</th>
                        <th>주문 날짜</th>
                        <th>지역</th>
                        <th>업종</th>
                        <th>총 금액</th>
                        <th>주문 내용</th>
                        <th>변경 주문 내용</th>
                    </tr>
                </thead>
                <tbody>
                    {% for index, row in df.iterrows() %}
                    <tr>
                        <td>{{ row['order_id'] }}</td>
                        <td>{{ row['order_date'] }}</td>
                        <td>{{ row['region'] }}</td>
                        <td>{{ row['business_type'] }}</td>
                        <td>₩{{ "{:,.0f}".format(row['total_price']) }}</td>
                        <td><span class="popup-button" onclick="openPopup({{ row['order_id'] }})">{{ row['order_description'] }}</span></td>
                        <td><span class="popup-button" onclick="openPopup({{ row['order_id'] }})">{{ row['order_after'] }}</span></td>
                        <!-- 위치 이동 버튼 -->
                        <td>
                            <button onclick="moveToLocation({{ row['latitude'] }}, {{ row['longitude'] }}, '{{ row['address'] }}' )">위치 이동</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% endif %}

        <!-- 팝업 오버레이 -->
        <div id="popup-overlay" onclick="closePopup()"></div>

        <!-- 팝업 -->
        <div id="popup">
            <div class="popup-content" id="popup-content">
                <button onclick="closePopup()">닫기</button>
            </div>
        </div>

    </body>
    </html>
    '''

    return render_template_string(html_content,
                                  year_list=year_list,
                                  month_list=month_list,
                                  business_type_list=business_type_list,
                                  region_list=region_list,
                                  selected_year=selected_year,
                                  selected_month=selected_month,
                                  selected_business_type=selected_business_type,
                                  selected_region=selected_region,
                                  df=df)


# 주문 품목 목록을 반환하는 라우트
@app.route('/get_order_items', methods=['GET'])
def get_order_items():
    order_id = request.args.get('order_id')

    # 해당 주문 ID에 대한 품목 목록 가져오기
    df_items = get_order_items_from_db(order_id)
    items = [{'product_code': row['product_code'], 'product_name': row['product_name'], 'main_type': row['alcoholic_type'],
              'unit_price': row['product_price'], 'quantity': row['quantity'], 'total_price': row['total_price']}
             for index, row in df_items.iterrows()]

    return jsonify({'items': items})

#
def order_listview_index(selected_year, selected_month, selected_business_type, selected_region, company_name):
    # 기본값 설정

    # 데이터 가져오기
    df = get_orders_from_db(year=selected_year, month=selected_month, business_type=selected_business_type, region=selected_region, company_name=company_name)

    # 연도 및 월 목록 생성
    conn = sqlite3.connect('OrderStatistics.db')
    # year_list = pd.read_sql_query("SELECT DISTINCT strftime('%Y', order_date) AS year FROM orders", conn)['year'].tolist()
    # -5년부터 현재 연도까지의 연도 목록 생성 (역순)
    # 현재 연도 가져오기
    current_year = datetime.now().year
    year_list = [str(year) for year in range(current_year, current_year - 5, -1)]
    month_list = [f"{i:02}" for i in range(1, 13)]
    business_type_list = pd.read_sql_query("SELECT DISTINCT business_type FROM orders", conn)['business_type'].tolist()
    region_list = pd.read_sql_query("SELECT DISTINCT region FROM orders", conn)['region'].tolist()
    conn.close()

    '''
    year_list.insert(0, '전체')
    month_list.insert(0, '전체')
    business_types.insert(0, '전체')
    '''

    # 예시로 데이터를 딕셔너리로 반환
    return {
        'selected_year': selected_year,
        'selected_month': selected_month,
        'selected_business_type': selected_business_type,
        'selected_region': selected_region,
        'year_list': year_list,
        'month_list': month_list,
        'business_type_list': business_type_list,
        'region_list': region_list,
        'df': df
    }


if __name__ == '__main__':
    app.run(debug=True)
