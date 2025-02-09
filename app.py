import dash
import json
from flask import Flask, render_template_string, request, jsonify, render_template, url_for

from prompt.research_prompt import output
from 통계분석_분석조회 import order_statists
from 통계분석_목록조회 import order_listview_index, get_order_items_from_db, view_index as get_view_index
#
from 상품관리_db import list_products, add_product, edit_product, delete_product, get_product
#
from 통계분석_그리드_app import generate_layout as statics_generate_layout  # 그리드테스트.py에서 generate_layout 불러옴
from 그리드테스트 import generate_layout
#
from 통계분석_파싱방식_db import process_order_parsing
from 통계분석_db_utils import save_to_db  # 외부 파일에서 save_to_db 함수 임포트
#
from datetime import datetime
from flask import redirect
app = Flask(__name__)

# 그리드 Dash 애플리케이션 초기화
#app1 = dash.Dash(__name__, server=app, url_base_pathname='/statics_grid/')
app2 = dash.Dash(__name__, server=app, url_base_pathname='/grid_test/')

# Dash 앱의 레이아웃 설정
#app1.layout = statics_generate_layout()
app2.layout = generate_layout()

# 사용자 계정 정보 (예제용)
USER_CREDENTIALS = {"admin": "1"}

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            return redirect(url_for("main"))
        else:
            # Pass the error message to the template
            return render_template("login.html", error="로그인 실패! 다시 시도하세요.")
    return render_template("login.html")

# 메인 페이지
@app.route("/main")
def main():
    return render_template("main.html")

@app.route("/main_menu")
def main_menu():
    return render_template("main_menu.html")

@app.route("/main_content")
def main_content():
    return render_template("main_content.html")

@app.route("/statitics_main")
def statitics_main():
    return render_template("통계분석_main.html")

# 통계분석 시작
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

    return render_template("통계분석.html",
                                  region_chart=region_chart,
                                  business_type_chart=business_type_chart,
                                  alcoholic_chart=alcoholic_chart,
                                  selected_year=selected_year,
                                  selected_month=selected_month,
                                  chart_type=chart_type,
                                  year_list=year_list,
                                  month_list=month_list)

# 통계분석 조회시
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


# 통계분석 주문목록 시작
@app.route('/order_listview', methods=['GET'])
def list_view():
    #
    result = order_listview_index('전체', '전체', '전체', '전체', '')

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

    return render_template("통계주문목록.html",
                                  year_list=year_list,
                                  month_list=month_list,
                                  business_type_list=business_type_list,
                                  region_list=region_list,
                                  selected_year=selected_year,
                                  selected_month=selected_month,
                                  selected_business_type=selected_business_type,
                                  selected_region=selected_region,
                                  df_records=df_records,
                                  df=df)


# 통계분석 주문목록 조건검색시
@app.route('/order_listview/update', methods=['POST'])
def update_order_listview():
    selected_year = request.form.get('year')
    selected_month = request.form.get('month')
    selected_business_type = request.form.get('business_type')
    selected_region= request.form.get('region')
    company_name = request.form.get("company_name")

    result = order_listview_index(selected_year, selected_month, selected_business_type, selected_region, company_name)
    df_records = result['df'].to_dict(orient='records')

    # Print each row in df_records
    #for index, row in enumerate(df_records):
    #    print(f"Row {index + 1}: {row}")

    return jsonify({
        'df_records': df_records,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'selected_business_type': selected_business_type,
        'selected_region': selected_region
    })


# 선택주문 분석품목목록
@app.route('/order_listview/get_order_items', methods=['GET'])
def get_order_items():
    order_id = request.args.get('order_id')

    # 해당 주문 ID에 대한 품목 목록 가져오기
    df_items = get_order_items_from_db(order_id)
    items = [{'product_code': row['product_code'], 'product_name': row['product_name'], 'alcohol_type': row['alcohol_type'],
              'product_price': row['product_price'], 'quantity': row['quantity'], 'total_price': row['total_price']}
             for index, row in df_items.iterrows()]

    return jsonify({'items': items})

# 품목관리
@app.route("/product_main")
def product_main():
    return render_template("product_main.html")

@app.route("/product_list")
def product_list():
    return render_template("product_list.html")

@app.route('/product/search', methods=['GET'])
def search():
    alcohol_type = request.args.get('alcohol_type', '')
    product_name = request.args.get('product_name', '')

    # Assuming list_products returns a list of dictionaries
    products = list_products(alcohol_type, product_name)

    return render_template('product_list.html',
                           alcohol_type=alcohol_type,
                           product_name=product_name,
                           products=products)


@app.route('/product_detail/get/<int:product_id>', methods=['GET'])
def product_detail(product_id):
    #product_id = request.args.get('product_id')
    product = get_product(product_id)

    return render_template('product_detail.html', product=product)

# 상품관리 입력/수정/삭제/조회 처리는 아래에..
@app.route('/product_detail/add', methods=['POST'])
def product_add():
    data = request.form
    result = add_product(data)  # jsonify({'message': 'Product added successfully'})

    return jsonify({
        'product_id': result.get('product_id'),
        'product_code': result.get('product_code'),
        'message': result.get('message')
    })

   # return render_template('product_detail.html', message=result.get('message'))

@app.route('/product_detail/edit/<int:product_id>', methods=['PUT'])
def product_edit(product_id):
    print(product_id)
    data = request.form
    print(data)
    result = edit_product(product_id, data)

    print(result)

    return jsonify({'message': result.get('message')})

@app.route('/product_detail/delete/<int:product_id>', methods=['DELETE'])
def product_delete(product_id):
    print(product_id)
    result = delete_product(product_id)

    return jsonify({'message': result.get('message')})


# 거래처(소매점)관리
@app.route("/retailshop_main")
def retailshop_main():
    return render_template("retailshop_main.html")

@app.route("/retailshop_list")
def retailshop_list():
    return render_template("retailshop_list.html")

@app.route('/retailshop/search', methods=['GET'])
def retailshop_search():
    business_category = request.args.get('business_category', '')
    business_type = request.args.get('business_type', '')
    business_detail = request.args.get('business_detail', '')
    srch_text = request.args.get('srch_text', '')

    return render_template('retailshop_list.html',
                           business_category=business_category,
                           business_type=business_type,
                           business_detail=business_detail,
                           srch_text=srch_text)

@app.route('/retailshop_detail/get/<busi_r_no>/<ordr_busi_r_no>', methods=['GET'])
def retailshop_detail(busi_r_no, ordr_busi_r_no):
    #
    return render_template('retailshop_detail.html', busi_r_no=busi_r_no, ordr_busi_r_no=ordr_busi_r_no)

@app.route("/statics_grid")
def statics_grid():
    return redirect("http://127.0.0.1:8050")
    #return app1.index()  # Dash 애플리케이션의 index()를 호출하여 HTML 콘텐츠를 반환

@app.route("/grid_test")
def grid_test():
    return app2.index()  # Dash 애플리케이션의 index()를 호출하여 HTML 콘텐츠를 반환

@app.route("/order_parsing")
def order_parsing():
    return render_template("주문_문자열파싱.html")

@app.route('/order_parsing/search', methods=['POST'])
def order_parsing_search():
    data = request.get_json()
    order_text = data.get("keyword", "")

    current_date = datetime.today().strftime('%Y-%m-%d')

    # 샘플 데이터 생성
    row = {
        "ordr_date": current_date,
        "busi_r_no": "123-45-67890",
        "ordr_busi_r_no": "A12345",
        "entprs_name": "강남놀부",
        "region": "서울",
        "sigungu": "강남구",
        "business_category": "음식점",
        "business_type": "한식",
        "business_detail": "고기",
        "addr1": "서울특별시 강남구 테헤란로 123",
        "orderContent": order_text
        #"주문내용": "SMS](010-9947-6336) 주류. 주문요참이슬. 처음. 이즈백 새로 1짝씩요"
    }
    parsing_data = process_order_parsing(row)[0]    # json형식
    parsing_result = process_order_parsing(row)[1]

    return jsonify({
                    'data': parsing_data,
                    'result': parsing_result
                    })


@app.route('/order_parsing/save_data', methods=['POST'])
def order_parsing_save():
    # Get the data sent from the front-end
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "No data received"}), 400

    try:
        json_datas = []
        fetched_data = data['data']
        # Append the new data to the existing array
        json_datas.append(fetched_data)
        #print(json.dumps(json_datas, ensure_ascii=False, indent=4))

        # 통계분석_db_utils 저장
        save_to_db(json_datas)
        return jsonify({"message": "Data saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred while saving the data: {str(e)}"}), 500


# 차후 다바다 웹서비스에서 호출시 삭제할 예정임.
@app.route('/davada_orders_list', methods=['GET'])
def davada_orders_list():
    # 저장된 JSON 파일 읽기
    with open("orders.json", "r", encoding="utf-8") as f:
        loaded_data = json.load(f)

    # 읽은 데이터를 출력
    for order in loaded_data:
        print(f"업체명: {order['entprs_name']}, 주문일자: {order['ordr_date']}, 주문내용: {order['orderContent']}")
    return loaded_data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
