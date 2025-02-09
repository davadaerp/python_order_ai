from flask import Flask, render_template_string, request, jsonify
from 통계분석_분석조회 import order_statists
from 통계분석_목록조회 import order_listview_index, get_order_items_from_db, view_index as get_view_index

app = Flask(__name__)
# test git hub
@app.route('/')
def index():
    html_content = '''
    <html>
    <head>
        <title>통계 선택</title>
        <style>
            body {
                font-family: Arial, sans-serif;
            }
            .popup {
                display: none;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 80%;
                height: 80%;
                background-color: white;
                border: 1px solid #ccc;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                z-index: 1000;
                overflow: auto;
                resize: both;
            }
            .popup-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background-color: #f2f2f2;
                padding: 10px;
                border-bottom: 1px solid #ccc;
                cursor: move; /* 드래그 커서 */
                position: sticky; /* 헤더 고정 */
                top: 0;
                z-index: 10;
            }
            .popup-title {
                font-size: 16px;
                margin: 0;
            }
            .popup-close {
                cursor: pointer;
                font-size: 20px;
                font-weight: bold;
                color: #333;
            }
            .popup-content {
                padding: 10px;
            }
            .overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 999;
            }
        </style>

        <!-- JQuery 추가 -->
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

        <script>
            let isDragging = false;
            let startX, startY, popupStartX, popupStartY;

            document.addEventListener("DOMContentLoaded", function () {
                const popup = document.getElementById("popup");
                const header = document.querySelector(".popup-header");

                header.addEventListener("mousedown", function (event) {
                    isDragging = true;
                    startX = event.clientX;
                    startY = event.clientY;

                    // 팝업의 현재 위치 저장
                    const rect = popup.getBoundingClientRect();
                    popupStartX = rect.left;
                    popupStartY = rect.top;

                    event.preventDefault();
                });

                document.addEventListener("mousemove", function (event) {
                    if (isDragging) {
                        const deltaX = event.clientX - startX;
                        const deltaY = event.clientY - startY;

                        // 새 위치 계산
                        let newLeft = popupStartX + deltaX;
                        let newTop = popupStartY + deltaY;

                        // 화면 경계를 벗어나지 않도록 제한
                        const windowWidth = window.innerWidth;
                        const windowHeight = window.innerHeight;
                        const popupWidth = popup.offsetWidth;
                        const popupHeight = popup.offsetHeight;

                        if (newLeft < 0) newLeft = 0;
                        if (newTop < 0) newTop = 0;
                        if (newLeft + popupWidth > windowWidth) newLeft = windowWidth - popupWidth;
                        if (newTop + popupHeight > windowHeight) newTop = windowHeight - popupHeight;

                        // 새 위치 적용
                        popup.style.left = newLeft + "px";
                        popup.style.top = newTop + "px";

                        // transform 제거
                        popup.style.transform = "none";
                    }
                });

                document.addEventListener("mouseup", function () {
                    isDragging = false;
                });
            });

            function openPopup(url, title) {
                const popup = document.getElementById('popup');
                const overlay = document.getElementById('overlay');
                const popupContent = document.getElementById('popup-content');

                popup.style.display = 'block';
                overlay.style.display = 'block';

                // 설정 팝업 제목
                document.getElementById('popup-title').textContent = title;

                // 콘텐츠 로드
                fetch(url)
                    .then(response => response.text())
                    .then(data => {
                        popupContent.innerHTML = data;
                    });
            }

            function closePopup() {
                const popup = document.getElementById('popup');
                const overlay = document.getElementById('overlay');

                popup.style.display = 'none';
                overlay.style.display = 'none';
                document.getElementById('popup-content').innerHTML = '';
            }

            function updateStatistics() {
                const chartType = document.getElementById('chart_type').value;
                const year = document.getElementById('year').value;
                const month = document.getElementById('month').value;

                $.ajax({
                    url: "/order/update",
                    method: "POST",
                    data: {
                        chart_type: chartType,
                        year: year,
                        month: month
                    },
                    success: function(response) {
                        document.getElementById("region_chart").src = "data:image/png;base64," + response.region_chart;
                        document.getElementById("business_type_chart").src = "data:image/png;base64," + response.business_type_chart;
                        document.getElementById("alcoholic_chart").src = "data:image/png;base64," + response.alcoholic_chart;
                    },
                    error: function(xhr, status, error) {
                        console.error("AJAX 요청 중 오류 발생:", error);
                    }
                });
            }

            // 분석통계목록 조건조회 
            function updateListView() {
                const year = document.getElementById('year').value;
                const month = document.getElementById('month').value;
                const business_type = document.getElementById('business_type').value;
                const region = document.getElementById('region').value;

                $.ajax({
                    url: "/order_listview/update",
                    method: "POST",
                    data: {
                        year: year,
                        month: month,
                        business_type: business_type,
                        region: region
                    },
                    success: function(response) {
                        // Update the dropdowns with selected values
                        document.getElementById('year').value = response.selected_year;
                        document.getElementById('month').value = response.selected_month;
                        document.getElementById('business_type').value = response.selected_business_type;
                        document.getElementById('region').value = response.selected_region;

                        // Clear the current table body
                        const tableBody = document.querySelector('table tbody');
                        tableBody.innerHTML = ''; // 기존의 내용 제거

                        // Check if response.df_records is available and is an array
                        if (Array.isArray(response.df_records) && response.df_records.length > 0) {
                            // Dynamically add new rows to the table
                            response.df_records.forEach(row => {
                                const tr = document.createElement('tr');

                                // Ensure the values are not undefined or null before inserting
                                tr.innerHTML = `
                                    <td>${row.order_id || 'N/A'}</td>
                                    <td>${row.order_date || 'N/A'}</td>
                                     <td>${row.company_name || 'N/A'}</td>
                                    <td>${row.region || 'N/A'}</td>
                                    <td>${row.business_type || 'N/A'}</td>
                                    <td>₩${row.total_price ? row.total_price.toLocaleString() : '0'}</td>
                                    <td><span class="popup-button" onclick="openItemPopup(${row.order_id}, '${row.order_description || 'N/A'}')">${row.order_description || 'N/A'}</span></td>
                                    <td><span class="popup-button" onclick="openItemPopup(${row.order_id}, '${row.order_after || 'N/A'}')">${row.order_after || 'N/A'}</span></td>
                                    <td>
                                        <button onclick="moveToLocation(${row.latitude || 0}, ${row.longitude || 0}, '${row.address ? row.address.replace(/'/g, "\\'") : 'N/A'}')">위치 이동</button>
                                    </td>
                                `;
                                tableBody.appendChild(tr);
                            });
                        } else {
                            // If no records are returned, show a message in the table
                            const tr = document.createElement('tr');
                            tr.innerHTML = '<td colspan="7">데이터가 없습니다.</td>';
                            tableBody.appendChild(tr);
                        }
                    },
                    error: function(xhr, status, error) {
                        console.error("AJAX 요청 중 오류 발생:", error);
                    }
                });
            }

            // 분석통계목록 상세품목목록 
            function openItemPopup(orderId) {
                var overlay = document.getElementById('popupItem-overlay');
                var popup = document.getElementById('popupItem');
                var content = document.getElementById('popupItem-content');

                overlay.style.display = 'block';
                popup.style.display = 'block';

                // Clear previous content
                content.innerHTML = '<p>Loading...</p>';

                // Fetch items from the server
                fetch('/order_listview/get_order_items?order_id=' + orderId)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Failed to fetch order items.');
                        }
                        return response.json();
                    })
                    .then(data => {
                        content.innerHTML = '<h3>품목 목록</h3>';
                        if (data.items && data.items.length > 0) {
                            let table = '<table><thead><tr>' +
                                        '<th>순번</th><th>품목 코드</th><th>품목명</th><th>주종</th><th>단가</th><th>수량</th><th>금액</th>' +
                                        '</tr></thead><tbody>';

                            data.items.forEach((item, index) => {
                                table += '<tr>' +
                                         '<td>' + (index + 1) + '</td>' +  // 순번 추가
                                         '<td>' + item.product_code + '</td>' +
                                         '<td>' + item.product_name + '</td>' +
                                         '<td>' + item.main_type + '</td>' +
                                         '<td>₩' + item.unit_price.toLocaleString() + '</td>' +
                                         '<td>' + item.quantity + '</td>' +
                                         '<td>₩' + item.total_price.toLocaleString() + '</td>' +
                                         '</tr>';
                            });

                            table += '</tbody></table>';
                            content.innerHTML += table;
                        } else {
                            content.innerHTML += '<p>품목이 없습니다.</p>';
                        }
                        content.innerHTML += '<button onclick="closeItemPopup()">닫기</button>';
                    })
                    .catch(error => {
                        content.innerHTML = '<p>Error loading items: ' + error.message + '</p>';
                        content.innerHTML += '<button onclick="closeItemPopup()">닫기</button>';
                    });
            }

            function closeItemPopup() {
                var overlay = document.getElementById('popupItem-overlay');
                var popup = document.getElementById('popupItem');
                overlay.style.display = 'none';
                popup.style.display = 'none';
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
        <h1>통계 서비스</h1>
        <ul>
            <li><a href="javascript:void(0);" onclick="openPopup('/order', '통계 분석')">통계분석</a></li>
            <li><a href="javascript:void(0);" onclick="openPopup('/order_listview', '통계 목록')">통계목록</a></li>
        </ul>

        <!-- 팝업 HTML 구조 -->
        <div id="overlay" class="overlay" onclick="closePopup()"></div>
        <div id="popup" class="popup">
            <div class="popup-header">
                <h2 id="popup-title" class="popup-title">Popup Title</h2>
                <span class="popup-close" onclick="closePopup()">&times;</span>
            </div>
            <div id="popup-content" class="popup-content">
                <!-- 동적으로 로드될 콘텐츠 -->
            </div>
        </div>

        <!-- 상세품목팝업 -->
        <div id="popupItem-overlay" onclick="closePopup()"></div>
        <div id="popupItem">
            <div id="popupItem-content">
                <!-- Content will be dynamically inserted here -->
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_content)


@app.route('/order/update', methods=['POST'])
def update_order_statistics():
    chart_type = request.form.get('chart_type')
    year = request.form.get('year')
    month = request.form.get('month')

    result = order_statists(chart_type=chart_type, year=year, month=month)

    return jsonify({
        'chart_type': result['chart_type'],
        'region_chart': result['region_chart'],
        'business_type_chart': result['business_type_chart'],
        'alcoholic_chart': result['alcoholic_chart']
    })


@app.route('/order', methods=['GET', 'POST'])
def order_view():
    # 초기 데이터 로딩
    result = order_statists('pie', '전체', '전체')

    region_chart = result['region_chart']
    business_type_chart = result['business_type_chart']
    alcoholic_chart = result['alcoholic_chart']
    selected_year = result['selected_year']
    selected_month = result['selected_month']
    chart_type = result['chart_type']
    year_list = result['year_list']
    month_list = result['month_list']

    # HTML 내용 작성
    html_content = '''
    <html>
    <head>
        <title>Sales Statistics</title>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    </head>
    <body>
        <h1>분석목록</h1>
        <form method="post">
            <label for="chart_type">차트 유형:</label>
            <select name="chart_type" id="chart_type" onchange="updateStatistics()">
                <option value="pie" {% if chart_type == 'pie' %}selected{% endif %}>파이 차트</option>
                <option value="bar" {% if chart_type == 'bar' %}selected{% endif %}>막대 차트</option>
            </select>

            <label for="year">년도:</label>
            <select name="year" id="year" onchange="updateStatistics()">
                {% for year in year_list %}
                    <option value="{{ year }}" {% if selected_year == year %}selected{% endif %}>{{ year }}</option>
                {% endfor %}
            </select>

            <label for="month">월:</label>
            <select name="month" id="month" onchange="updateStatistics()">
                {% for month in month_list %}
                    <option value="{{ month }}" {% if selected_month == month %}selected{% endif %}>{{ month }}</option>
                {% endfor %}
            </select>
        </form>

        <div id="charts">
            <h2>지역별 판매 분포</h2>
            <img id="region_chart" src="data:image/png;base64,{{ region_chart }}" />

            <h2>업종별 판매 분포</h2>
            <img id="business_type_chart" src="data:image/png;base64,{{ business_type_chart }}" />

            <h2>주종별 판매 분포</h2>
            <img id="alcoholic_chart" src="data:image/png;base64,{{ alcoholic_chart }}" />
        </div>
    </body>
    </html>
    '''

    return render_template_string(html_content,
                                  region_chart=region_chart,
                                  business_type_chart=business_type_chart,
                                  alcoholic_chart=alcoholic_chart,
                                  selected_year=selected_year,
                                  selected_month=selected_month,
                                  chart_type=chart_type,
                                  year_list=year_list,
                                  month_list=month_list)


@app.route('/order_listview/update', methods=['POST'])
def update_order_listview():
    selected_year = request.form.get('year')
    selected_month = request.form.get('month')
    selected_business_type = request.form.get('business_type')
    selected_region = request.form.get('region')

    result = order_listview_index(selected_year, selected_month, selected_business_type, selected_region)
    df_records = result['df'].to_dict(orient='records')

    # Print each row in df_records
    # for index, row in enumerate(df_records):
    #    print(f"Row {index + 1}: {row}")

    return jsonify({
        'df_records': df_records,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'selected_business_type': selected_business_type,
        'selected_region': selected_region
    })


@app.route('/order_listview', methods=['GET'])
def list_view():
    #
    result = order_listview_index('전체', '전체', '전체', '전체')

    year_list = result['year_list']
    month_list = result['month_list']
    business_type_list = result['business_type_list']
    region_list = result['region_list']
    selected_year = result['selected_year']
    selected_month = result['selected_month']
    selected_business_type = result['selected_business_type']
    selected_region = result['selected_region']
    df = result['df']

    # Convert the pandas DataFrame to a list of dictionaries
    df_records = df.to_dict(orient='records')

    html_content = '''
    <html>
    <head>
        <title>Order Statistics</title>
        <style>
            #popupItem {
                display: none;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 20px;
                z-index: 1000;
                max-width: 80%;
                max-height: 80%;
                overflow: auto;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            #popupItem-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 999;
            }
            .popup-button {
                color: blue;
                cursor: pointer;
                text-decoration: underline;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            button {
                margin-top: 20px;
                padding: 10px 20px;
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:hover {
                background-color: #0056b3;
            }
        </style>
        <script>

        </script>
    </head>
    <body>
        <h1>주문목록</h1>
        <select id="year" onchange="updateListView()">
            <option value="전체">전체</option>
            {% for year in year_list %}
                <option value="{{ year }}" {% if year == selected_year %}selected{% endif %}>{{ year }}</option>
            {% endfor %}
        </select>
        <select id="month" onchange="updateListView()">
            <option value="전체">전체</option>
            {% for month in month_list %}
                <option value="{{ month }}" {% if month == selected_month %}selected{% endif %}>{{ month }}</option>
            {% endfor %}
        </select>
        <select id="business_type" onchange="updateListView()">
            <option value="전체">전체</option>
            {% for business_type in business_type_list %}
                <option value="{{ business_type }}" {% if business_type == selected_business_type %}selected{% endif %}>{{ business_type }}</option>
            {% endfor %}
        </select>
        <select id="region" onchange="updateListView()">
            <option value="전체">전체</option>
            {% for region in region_list %}
                <option value="{{ region }}" {% if region == selected_region %}selected{% endif %}>{{ region }}</option>
            {% endfor %}
        </select>

        {% if df.empty %}
            <p>선택한 조건에 해당하는 데이터가 없습니다.</p>
        {% else %}
            <table border="1">
                <thead>
                    <tr>
                        <th>주문 ID</th>
                        <th>주문 날짜</th>
                         <th>상호명</th>
                        <th>지역</th>
                        <th>업종</th>
                        <th>총 금액</th>
                        <th>주문 내용</th>
                        <th>변역 내용</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in df_records %}
                    <tr>
                        <td>{{ row['order_id'] }}</td>
                        <td>{{ row['order_date'] }}</td>
                        <td>{{ row['company_name'] }}</td>
                        <td>{{ row['region'] }}</td>
                        <td>{{ row['business_type'] }}</td>
                        <td>₩{{ "{:,.0f}".format(row['total_price']) }}</td>
                        <td><span class="popup-button" onclick="openItemPopup({{ row['order_id'] }})">{{ row['order_description'] }}</span></td>
                        <td><span class="popup-button" onclick="openItemPopup({{ row['order_id'] }})">{{ row['order_after'] }}</span></td>
                        <!-- 위치 이동 버튼 -->
                        <td>
                            <button onclick="moveToLocation({{ row['latitude'] }}, {{ row['longitude'] }}, '{{ row['address'] }}' )">위치 이동</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% endif %}

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
                                  df_records=df_records, df=df)


@app.route('/order_listview/get_order_items', methods=['GET'])
def get_order_items():
    order_id = request.args.get('order_id')

    # 해당 주문 ID에 대한 품목 목록 가져오기
    df_items = get_order_items_from_db(order_id)
    items = [{'product_code': row['product_code'], 'product_name': row['product_name'],
              'main_type': row['alcoholic_beverage'],
              'unit_price': row['unit_price'], 'quantity': row['quantity'], 'total_price': row['total_price']}
             for index, row in df_items.iterrows()]

    return jsonify({'items': items})


if __name__ == '__main__':
    app.run(debug=True)
