import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask import Flask, render_template_string, request, jsonify
import matplotlib
import matplotlib.font_manager as fm
from datetime import datetime

from fontTools.ttLib.tables.otTables import DeltaSetIndexMap

app = Flask(__name__)

# 한글 폰트 설정 (MacOS에서 AppleSDGothicNeo 사용)
font_path = '/System/Library/Fonts/AppleSDGothicNeo.ttc'  # 폰트 경로 확인 필요
prop = fm.FontProperties(fname=font_path)

# matplotlib 폰트 설정
matplotlib.rcParams['font.family'] = prop.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 처리


# SQLite3 데이터베이스에서 데이터를 불러오는 함수
def get_data_from_db(year=None, month=None, db_file='OrderStatistics.db'):
    conn = sqlite3.connect(db_file)
    query = '''
    SELECT o.region, o.business_type, oi.alcohol_type, strftime('%Y', o.order_date) AS year, 
           strftime('%m', o.order_date) AS month, 
           SUM(CAST(REPLACE(oi.total_price, ',', '') AS FLOAT)) AS total_sales
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    '''

    conditions = []
    if year and year != '전체':
        conditions.append(f"strftime('%Y', o.order_date) = '{year}'")
    if month and month != '전체':
        conditions.append(f"strftime('%m', o.order_date) = '{month:02}'")

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' GROUP BY o.region, o.business_type, oi.alcohol_type'

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Ensure total_sales is numeric and handle any NaN values
    df['total_sales'] = pd.to_numeric(df['total_sales'], errors='coerce')  # Convert to numeric
    df = df.dropna(subset=['total_sales'])  # Drop rows where total_sales is NaN

    return df

# 지역별 파이 차트 시각화 함수
def plot_region_pie_chart(df):
    if df.empty:
        return None  # Return None if the dataframe is empty

    region_sales = df.groupby('region')['total_sales'].sum()
    plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = plt.pie(region_sales, labels=region_sales.index,
                                       autopct=lambda p: f'{p:.1f}%\n₩{p * sum(region_sales) / 100:,.0f}',
                                       startangle=90)
    plt.title('지역별 판매 분포', fontproperties=prop, fontsize=16, fontweight='bold')
    plt.legend(wedges, region_sales.index, title="지역", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return img_data


# 업종별 파이 차트 시각화 함수
def plot_business_type_pie_chart(df):
    if df.empty:
        return None  # Return None if the dataframe is empty

    business_type_sales = df.groupby('business_type')['total_sales'].sum()
    plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = plt.pie(business_type_sales, labels=business_type_sales.index,
                                       autopct=lambda p: f'{p:.1f}%\n₩{p * sum(business_type_sales) / 100:,.0f}',
                                       startangle=90)
    plt.title('업종별 판매 분포', fontproperties=prop, fontsize=16, fontweight='bold')
    plt.legend(wedges, business_type_sales.index, title="업종", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return img_data


# 주종별 파이 차트 시각화 함수
def plot_alcoholic_beverage_pie_chart(df):
    if df.empty:
        return None  # Return None if the dataframe is empty

    alcoholic_sales = df.groupby('alcohol_type')['total_sales'].sum()
    plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = plt.pie(alcoholic_sales, labels=alcoholic_sales.index,
                                       autopct=lambda p: f'{p:.1f}%\n₩{p * sum(alcoholic_sales) / 100:,.0f}',
                                       startangle=90)
    plt.title('주종별 판매 분포', fontproperties=prop, fontsize=16, fontweight='bold')
    plt.legend(wedges, alcoholic_sales.index, title="주종", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return img_data


# 지역별 막대그래프 시각화 함수
# def plot_region_bar_chart(df):
#     if df.empty:
#         return None  # Return None if the dataframe is empty
#
#     region_sales = df.groupby('region')['total_sales'].sum()
#     plt.figure(figsize=(10, 6))
#     region_sales.plot(kind='bar', color='skyblue')
#     plt.title('지역별 판매 분포', fontproperties=prop, fontsize=16, fontweight='bold')
#     plt.ylabel('판매 금액 (₩)', fontproperties=prop)
#     plt.xlabel('지역', fontproperties=prop)
#     plt.xticks(rotation=45)
#     img = BytesIO()
#     plt.savefig(img, format='png')
#     img.seek(0)
#     img_data = base64.b64encode(img.getvalue()).decode('utf-8')
#     plt.close()
#     return img_data

def plot_region_bar_chart(df):
    if df.empty:
        return None  # Return None if the dataframe is empty

    df['total_sales_k'] = df['total_sales'] / 1000  # 1000원 단위로 변경
    df['total_sales_k_str'] = df['total_sales_k'].apply(lambda x: f'{x:,.0f}')  # 콤마 추가된 문자열 저장

    region_sales = df.groupby('region')['total_sales_k'].sum()  # Sum numeric values

    # 색상 리스트 생성
    colors = plt.cm.get_cmap('tab20', len(region_sales))(range(len(region_sales)))

    plt.figure(figsize=(10, 6))
    ax = region_sales.plot(kind='bar', color=colors)

    plt.title('지역별 판매 분포', fontproperties=prop, fontsize=16, fontweight='bold')
    plt.ylabel('판매 금액 (₩-천단위)', fontproperties=prop)
    plt.xlabel('지역', fontproperties=prop)
    plt.xticks(rotation=45)

    # 막대 상단에 금액 표시
    for index, value in enumerate(region_sales):
        ax.text(index, value + (max(region_sales) * 0.01), f'{value:,.0f}',
                ha='center', fontsize=12, fontweight='bold', color='black')

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return img_data


# 업종별 막대그래프 시각화 함수
def plot_business_type_bar_chart(df):
    if df.empty:
        return None  # Return None if the dataframe is empty

    business_type_sales = df.groupby('business_type')['total_sales'].sum()
    # 색상 리스트 생성
    colors = plt.cm.get_cmap('tab20', len(business_type_sales))(range(len(business_type_sales)))

    plt.figure(figsize=(10, 6))
    business_type_sales.plot(kind='bar', color=colors)
    plt.title('업종별 판매 분포', fontproperties=prop, fontsize=16, fontweight='bold')
    plt.ylabel('판매 금액 (₩)', fontproperties=prop)
    plt.xlabel('업종', fontproperties=prop)
    plt.xticks(rotation=45)
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return img_data


# 주종별 막대그래프 시각화 함수 (각 item별 색상 다르게 처리)
def plot_alcoholic_beverage_bar_chart(df):
    if df.empty:
        return None  # Return None if the dataframe is empty

    alcoholic_sales = df.groupby('alcohol_type')['total_sales'].sum()
    # 색상 리스트 생성
    colors = plt.cm.get_cmap('tab20', len(alcoholic_sales))(range(len(alcoholic_sales)))

    plt.figure(figsize=(10, 6))
    alcoholic_sales.plot(kind='bar', color=colors)
    plt.title('주종별 판매 분포', fontproperties=prop, fontsize=16, fontweight='bold')
    plt.ylabel('판매 금액 (₩)', fontproperties=prop)
    plt.xlabel('주종', fontproperties=prop)
    plt.xticks(rotation=45)
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return img_data

# 지역별 트렌드(추세) 차트
def plot_region_trend_chart(df):
    if df.empty:
        return None

    trend_data = df.groupby(['year', 'region'])['total_sales'].sum().unstack()

    plt.figure(figsize=(8, 6))
    trend_data.plot(marker='o')
    plt.title('지역별 연도별 판매 추이', fontproperties=prop, fontsize=16, fontweight='bold')
    plt.ylabel('판매 금액 (₩)', fontproperties=prop)
    plt.xlabel('년도(월)', fontproperties=prop, fontsize=8)
    plt.xticks(rotation=45)
    #plt.legend(title='지역')
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return img_data

# 업종별 트렌드(추세) 차트
def plot_business_type_trend_chart(df):
    if df.empty:
        return None

    trend_data = df.groupby(['year', 'business_type'])['total_sales'].sum().unstack()
    plt.figure(figsize=(10, 6))
    trend_data.plot(marker='o')
    plt.title('업종별 연도별 판매 추이', fontproperties=prop, fontsize=16, fontweight='bold')
    plt.ylabel('판매 금액 (₩)', fontproperties=prop)
    plt.xlabel('연도', fontproperties=prop)
    plt.xticks(rotation=45)
    #plt.legend(title='업종')
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return img_data

# 주종별 트렌드(추세) 차트
def plot_alcoholic_beverage_trend_chart(df):
    if df.empty:
        return None

    trend_data = df.groupby(['year', 'alcohol_type'])['total_sales'].sum().unstack()
    plt.figure(figsize=(10, 6))
    trend_data.plot(marker='o')
    plt.title('주종별 연도별 판매 추이', fontproperties=prop, fontsize=16, fontweight='bold')
    plt.ylabel('판매 금액 (₩)', fontproperties=prop)
    plt.xlabel('연도', fontproperties=prop)
    plt.xticks(rotation=45)
    #plt.legend(title='주종')
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_data = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return img_data

@app.route('/', methods=['GET', 'POST'])
def order_index():
    # 기본값 설정
    selected_year = request.form.get('year', '전체')
    selected_month = request.form.get('month', '전체')
    chart_type = request.form.get('chart_type', 'pie')

    # 데이터 가져오기
    df = get_data_from_db(year=selected_year, month=selected_month)

    # Ensure we have data before trying to plot
    if df.empty:
        region_chart = business_type_chart = alcoholic_chart = alcoholic_bar_chart = None
    else:
        if chart_type == 'pie':
            region_chart = plot_region_pie_chart(df)
            business_type_chart = plot_business_type_pie_chart(df)
            alcoholic_chart = plot_alcoholic_beverage_pie_chart(df)
        elif chart_type == 'bar':
            region_chart = plot_region_bar_chart(df)
            business_type_chart = plot_business_type_bar_chart(df)
            alcoholic_chart = plot_alcoholic_beverage_bar_chart(df)
        else:
            region_chart = plot_region_trend_chart(df)
            business_type_chart = plot_business_type_trend_chart(df)
            alcoholic_chart = plot_alcoholic_beverage_trend_chart(df)

    # 연도 및 월 목록 생성
    # 현재 연도 가져오기
    current_year = datetime.now().year

    # -5년부터 현재 연도까지의 연도 목록 생성 (역순)
    year_list = [str(year) for year in range(current_year, current_year - 6, -1)]
    month_list = [f"{i:02}" for i in range(1, 13)]

    year_list.insert(0, '전체')
    month_list.insert(0, '전체')

    html_content = '''
    <html>
    <head>
        <title>Sales Statistics</title>
    </head>
    <body>
        <form method="post">
            <label for="chart_type">차트 유형:</label>
            <select name="chart_type" id="chart_type" onchange="this.form.submit()">
                <option value="pie" {% if chart_type == 'pie' %}selected{% endif %}>파이 차트</option>
                <option value="bar" {% if chart_type == 'bar' %}selected{% endif %}>막대 차트</option>
            </select>
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
        </form>

        <h2>지역별 판매 분포</h2>
        {% if region_chart %}
            <img src="data:image/png;base64,{{ region_chart }}" />
        {% endif %}

        <h2>업종별 판매 분포</h2>
        {% if business_type_chart %}
            <img src="data:image/png;base64,{{ business_type_chart }}" />
        {% endif %}

        <h2>주종별 판매 분포</h2>
        {% if alcoholic_chart %}
            <img src="data:image/png;base64,{{ alcoholic_chart }}" />
        {% endif %}
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


# 통계값을 app.py에 리턴한다.
def order_statists(chart_type, year, month):

    # 전달된 파라미터 값 출력
    print(f"Chart Type: {chart_type}")
    print(f"Year: {year}")
    print(f"Month: {month}")

    # 데이터 가져오기
    df = get_data_from_db(year=year, month=month)

    # Ensure we have data before trying to plot
    if df.empty:
        region_chart = business_type_chart = alcoholic_chart = alcoholic_bar_chart = None
    else:
        if chart_type == 'pie':
            region_chart = plot_region_pie_chart(df)
            business_type_chart = plot_business_type_pie_chart(df)
            alcoholic_chart = plot_alcoholic_beverage_pie_chart(df)
        elif chart_type == 'bar':
            region_chart = plot_region_bar_chart(df)
            business_type_chart = plot_business_type_bar_chart(df)
            alcoholic_chart = plot_alcoholic_beverage_bar_chart(df)
        else:
            region_chart = plot_region_trend_chart(df)
            business_type_chart = plot_business_type_trend_chart(df)
            alcoholic_chart = plot_alcoholic_beverage_trend_chart(df)

    # 연도 및 월 목록 생성
    # 현재 연도 가져오기
    current_year = datetime.now().year

    # -5년부터 현재 연도까지의 연도 목록 생성 (역순)
    year_list = [str(year) for year in range(current_year, current_year - 6, -1)]
    month_list = [f"{i:02}" for i in range(1, 13)]

    year_list.insert(0, '전체')
    month_list.insert(0, '전체')

    print(f"Chart --- Type: {chart_type}")

    # 예시로 데이터를 딕셔너리로 반환
    return {
        'region_chart': region_chart,
        'business_type_chart': business_type_chart,
        'alcoholic_chart': alcoholic_chart,
        'selected_year': year,
        'selected_month': month,
        'chart_type': chart_type,
        'year_list': year_list,
        'month_list': month_list
    }

if __name__ == '__main__':
    app.run(debug=True, port=5001)