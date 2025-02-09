import re
import csv
import json
import sqlite3
import pandas as pd

import requests

from 통계분석_db_utils import save_to_db  # 외부 파일에서 save_to_db 함수 임포트

api_key = "AIzaSyAH_84wbHYlDMygF4uiok4k1EVQsShqnT8"  # 본인의 API 키를 입력하세요

# 한글 숫자 매핑
korean_number_map = {
    '한': '1', '두': '2',
    '한개': '1', '두개': '2', '세개': '3', '네개': '4', '다섯개': '5', '여섯개': '6',
    '일곱개': '7', '여덟개': '8', '아홉개': '9', '열개': '10',
    '하나': '1', '둘': '2', '셋': '3', '넷': '4', '다섯': '5', '여섯': '6',
    '일곱': '7', '여덟': '8', '아홉': '9', '열': '10', '열하나': '11', '열둘': '12',
    '열셋': '13', '열넷': '14', '열다섯': '15', '열여섯': '16', '열일곱': '17',
    '열여덟': '18', '열아홉': '19', '스물': '20', '스물하나': '21', '스물둘': '22',
    '스물셋': '23', '스물넷': '24', '스물다섯': '25', '스물여섯': '26', '스물일곱': '27',
    '스물여덟': '28', '스물아홉': '29', '서른': '30', '서른하나': '31', '서른둘': '32',
    '서른셋': '33', '서른넷': '34', '서른다섯': '35', '서른여섯': '36', '서른일곱': '37',
    '서른여덟': '38', '서른아홉': '39', '마흔': '40', '마흔하나': '41', '마흔둘': '42',
    '마흔셋': '43', '마흔넷': '44', '마흔다섯': '45', '마흔여섯': '46', '마흔일곱': '47',
    '마흔여덟': '48', '마흔아홉': '49', '쉰': '50', '쉰하나': '51', '쉰둘': '52', '쉰셋': '53',
    '쉰넷': '54', '쉰다섯': '55', '쉰여섯': '56', '쉰일곱': '57', '쉰여덟': '58', '쉰아홉': '59',
    '예순': '60', '예순하나': '61', '예순둘': '62', '예순셋': '63', '예순넷': '64', '예순다섯': '65',
    '예순여섯': '66', '예순일곱': '67', '예순여덟': '68', '예순아홉': '69', '일흔': '70',
    '일흔하나': '71', '일흔둘': '72', '일흔셋': '73', '일흔넷': '74', '일흔다섯': '75', '일흔여섯': '76',
    '일흔일곱': '77', '일흔여덟': '78', '일흔아홉': '79', '여든': '80', '여든하나': '81',
    '여든둘': '82', '여든셋': '83', '여든넷': '84', '여든다섯': '85', '여든여섯': '86', '여든일곱': '87',
    '여든여덟': '88', '여든아홉': '89', '아흔': '90', '아흔하나': '91', '아흔둘': '92', '아흔셋': '93',
    '아흔넷': '94', '아흔다섯': '95', '아흔여섯': '96', '아흔일곱': '97', '아흔여덟': '98',
    '아흔아홉': '99'
}

# 파일 경로
db_path = 'OrderStatistics.db';
orders_file = 'orders.json'

# 제거단어 추가
remove_keywords = ["태릉","연태","500미리","프레쉬도","소주좀","테나","냉동창고","330","소주잔","진성"]

# DB 파일 읽기 및 역방향 조회 테이블 생성
def read_db_and_create_reverse_lookup(db_path):
    """
    SQLite에서 products 테이블을 읽어 역방향 조회 테이블을 생성하는 함수.
    """
    reverse_lookup = {}
    product_aliases = set()
    whiskey_aliases = set()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT product_code, product_name, alcohol_type, product_price, product_nickname FROM product")
    rows = cursor.fetchall()

    for row in rows:
        product_code, product_name, alcohol_type, product_price, product_nickname = row
        product_alias_list = product_nickname.split(',') if product_nickname else []
        for alias in product_alias_list:
            product_aliases.add(alias)
            # 윈저17,화요17,임페리얼17등 경우에 비교할 alias_nickname 추가함
            pattern = re.compile(r'.*\d$')  # 문자열 끝이 숫자인 경우 매칭(주로 양주 + 전통주쪽 화요17,화요28등)
            if pattern.match(product_name):
                whiskey_aliases.add(alias)
            #
            if alias not in reverse_lookup:
                reverse_lookup[alias] = []
            reverse_lookup[alias].append((product_code, product_name, alcohol_type, product_price))

    conn.close()
    return reverse_lookup, list(product_aliases), list(whiskey_aliases)

def get_lat_lng(address: str, api_key: str):
    """
    주소를 입력받아 위도와 경도를 반환하는 함수.
    :param address: 주소 (예: '서울특별시 강남구 테헤란로 212')
    :param api_key: Google Maps API 키
    :return: 위도, 경도 튜플
    """
    # Geocoding API URL
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"

    # 요청 보내기
    response = requests.get(url)
    data = response.json()

    # 결과 확인 및 위도, 경도 반환
    if data['status'] == 'OK':
        lat = data['results'][0]['geometry']['location']['lat']
        lng = data['results'][0]['geometry']['location']['lng']
        return lat, lng
    else:
        print(f"Geocoding API 요청 오류: {data['status']}")
        return 0, 0


# 하위 항목을 통해 상위 항목을 찾는 함수
def find_parent_items(item, reverse_lookup):
    return reverse_lookup.get(item, [])

# 역방향 조회 테이블 생성
reverse_lookup, product_aliases, whiskey_aliases = read_db_and_create_reverse_lookup(db_path)

# 단위(개, 짝, 병 등) 제거하는 함수 (숫자 뒤의 단위 제거)
def remove_units(text):
    # 맨처음 품목별명을 찾아서 앞에 문장을 삭제하는게 문제네. => 처리함
    # text = re.sub(r'\d+층으로|층에서|층까지|층', '', text) # 숫자 + "층" 패턴 제거 (예: 1층, 2층, 10층 등)
    # text = re.sub(r'입니다|임니다|습니다|합니다|하세요|추가로|발주|요일|찌게\.?', ',', text)
    #
    text = re.sub(r'\s*(병|생)(\d)', r'\1\2', text)  # '병 2'와 같이 공백을 없앰
    text = re.sub(r'(\d)(개|짝|병|통|상자|box|세트|박스|팩|케그)', r'\1', text)  # 숫자 뒤 단위 제거
    return text

# 한글 숫자를 숫자로 변환
def convert_korean_numbers(text, korean_number_map):
    for kor_num, digit in korean_number_map.items():
        text = text.replace(kor_num, digit)
    #
    text = re.sub(r'\s+', '', text)  # 전체 공백 제거
    #text = re.sub(r'\s*(\d)', r'\1', text)  # 숫자 앞에 공백 제거
    return text

"""
주문 내용에서 특정 단어를 제거하는 함수
"""
def remove_specific_words(order_text, keywords):
    # 특정 단어 제거 (한글 단어만 정확히 일치하도록 처리)
    for keyword in remove_keywords:
        order_text = order_text.replace(keyword, '')

    # 연속된 공백 정리
    order_text = re.sub(r'\s+', ' ', order_text).strip()

    return order_text

# 위스키 제품같이 년도가 있는 제품만 필터링함 => 이유는 숫자처리 필터때문 ㅠ.ㅠ
def filter_whiskey_orders(order_text):

    # 특수문자 제거: 알파벳, 숫자, 한글, 공백만 남기기
    order_text = re.sub(r'[^a-zA-Z0-9가-힣\s]', '', order_text)

    whiskey_orders = []

    # whiskey_aliases에 해당하는 문자열 뒤에 숫자가 있으면 공백 추가
    for alias in whiskey_aliases:

        # 해당 품목 뒤에 공백이 있고, 그 뒤에 숫자가 있는 경우 찾기
        # 이경우 중복해서 찾을수 있슴 => 윈저시그니처12, 시그니처12를 같은걸로봄.
        # 위 중복품목은 실제 set(product_orders) 중복제거를 해서 보여줘야함.
        matches = re.findall(fr'({alias})\s*(\d+)', order_text)
        for match in matches:
            #print(f"품목명: {match[0]}, 숫자: {match[1]}")
            whiskey_orders.append((match[0], match[1]))

    return whiskey_orders

# 맨처음 위치 품목찾기
def first_item_find(order_text, product_aliases):

    start_index = len(order_text)  # 기본적으로 전체 문자열을 무시하는 값으로 설정

    # 상품별명이 등장하는 가장 앞 위치 찾기
    for alias in product_aliases:
        idx = order_text.find(alias)
        if idx != -1 and idx < start_index:
            start_index = idx

    # 해당 위치 이후의 문자열 저장
    filtered_order = order_text[start_index:] if start_index < len(order_text) else ""

    # 특수문자, 공백처리
    filtered_order = re.sub(r'[^\w\s]', ' ', filtered_order)  # 특수문자를 공백으로 변환
    filtered_order = re.sub(r'\s+', '', filtered_order).strip()  # 연속된 공백을 단일 공백으로 정리

    return filtered_order

# 짝식,박스씩, 각+숫자+박스 처리로직
def clean_and_parse(input_string):
    # 특수문자 제거: 알파벳, 숫자, 한글, 공백만 남기기
    cleaned_string = re.sub(r'[^a-zA-Z0-9가-힣\s]', '', input_string)

    # "각" 제거
    cleaned_string = cleaned_string.replace('각', '')

    # 정규 표현식 패턴: 단어 + 숫자 형식
    pattern = r'([가-힣]+)(\d*)'  # 숫자가 없는 단어도 처리

    # 패턴에 맞는 모든 매칭을 찾기
    matches = re.findall(pattern, cleaned_string)

    # '단어+숫자' 형식으로 결합한 문자열로 반환 (숫자가 없으면 1을 추가)
    result = [f'{word}{number if number else "1"}' for word, number in matches]

    # 리스트를 공백으로 구분하여 하나의 문자열로 결합
    return ' '.join(result)

# 주문 파싱 처리
def process_order_parsing(row):
    주문일자 = row['ordr_date']             # 주문일자
    사업자번호 = row['busi_r_no']            # 사업자번호
    업체코드 = row['ordr_busi_r_no']        # 업체코드
    업체명 = row['entprs_name']            # 업체명
    지역 = row['region']                  # 지역: 서울/경기/인천
    지역상세 = row['sigungu']               # 시/군/구
    업태 = row['business_category']          # 업태: business_category
    업종 = row['business_type']          # 업종: business_type
    업종상세 = row['business_detail']    # 업종상세: business_detail 고기,부폐,코드
    주소 = row['addr1']                   # 주소
    #
    원주문내용 = row['orderContent']  # 원주문내용에 저장
    #
    parsing_result = []
    #
    # 위스키 제품만 필터링함 => 위스키에 숫자가 들어있어 따로 처리해야함 ㅠ.ㅠ
    whiskey_order = filter_whiskey_orders(원주문내용)
    #print(whiskey_order)

    # 0. 전체 공백 제거
    주문내용 = re.sub(r'\s+', '', 원주문내용)
    parsing_result.append('\n원주문내용: ' + 원주문내용)

    # 1. 특정문자를 제거하는 로직
    주문내용 = remove_specific_words(주문내용, remove_keywords)
    parsing_result.append('전체공백및 특정문자제거: ' + 주문내용)
    #print('전체공백및 특정문자제거: ' + 주문내용)

    # 짝식,박스씩, 각+숫자+박스 처리로직 => '각' 뒤에 숫자와 '박스', '짝씩', '박스씩'이 나오는 패턴
    pattern = r'(각\d+박스|각\d+짝씩|\d+박스씩|\d+짝씩)'
    if re.search(pattern, 주문내용):
        주문내용 = clean_and_parse(원주문내용)
        parsing_result.append('전체pattern: ' + 주문내용)
        #print('전체pattern: ' + 주문내용)

    # 2. 맨처음 위치 품목찾아서 앞에 문자열 삭제함.
    주문내용 = first_item_find(주문내용, product_aliases)
    parsing_result.append('최초품목앞문자열삭제: ' + 주문내용)

    # 3. 한글 숫자 변환 및 단위 제거
    주문내용 = convert_korean_numbers(주문내용, korean_number_map)
    주문내용 = remove_units(주문내용)

    # 4. 한글+영문+숫자를 올바르게 매칭하는 정규식 (한글과 숫자 분리)
    matches = re.findall(r'([가-힣A-Za-z]+)(\d+)', 주문내용)
    matches = matches + whiskey_order   # 일반상품 + 위스키 필터링 상품
    print(matches)
    parsing_result.append('matches: ' + str(matches) + '\n')

    # 위도, 경도 가져오기 (0이면 None로 키에러외 기타등등)
    latitude, longitude = get_lat_lng(주소, api_key)
    #print(f"주소: {주소}, 위도: {latitude}, 경도: {longitude}")

    product_counts = []
    product_orders = []
    product_jsons = []

    for match in matches:
        product, count = match
        count = int(count)

        # 상품별명 목록을 확인하여 일치하는 상위 항목을 찾음
        possible_parents = find_parent_items(product, reverse_lookup)

        if possible_parents:
            # 첫 번째 매칭된 상위 항목을 기준으로 처리
            parent_code, parent_name, alcohol_type, product_price = possible_parents[0]
            #total_price = product_price * count  # 주문금액 계산
            total_price = int(str(product_price).replace(',', '')) * count
            total_price = f"{total_price:,}"
            product_counts.append(f"{parent_code}-{parent_name}-{alcohol_type}-{product_price}원-{count}개-{total_price}원")
            product_orders.append(f"{parent_code}-{parent_name}-{count}개")
            product_jsons.append({
                "product_code": parent_code,
                "product_name": parent_name,
                "alcohol_type": alcohol_type,
                "product_price": product_price,
                "quantity": count,
                "total_price": total_price
            })

    #print(f"\n처리 중인 업체: {주문일자}, {업체코드}, {사업자번호}, {업체명}, {지역}, {업종}")

    # 결과 형식으로 변환 set is 중복제거처리
    output = ", \n".join(set(product_counts))
    파싱주문내용 = ", ".join(set(product_orders))

    # 업체정보와 주문내용 분석 결과를 함께 출력
    result = (
        f"주문일자: {주문일자}, 업체코드: {업체코드}, 사업자번호: {사업자번호}, 업체명: {업체명}, 지역: {지역}, 업종: {업종}\n"
        f"원주문내용: {원주문내용}\n"
        f"=> 파싱내용: {주문내용}\n\n"
        f"주문내용 분석 결과:\n {output}\n"
    )
    parsing_result.append('처리결과: ' + result + '\n')

    # 개행 문자 적용하여 출력
    print("\n".join(parsing_result))  # ✅ 올바른 출력 방식

    # json 중복 제거 => Drop duplicates based on all columns
    df = pd.DataFrame(product_jsons)
    unique_product_jsons = df.drop_duplicates().to_dict(orient='records')

    return {
        "order_date": 주문일자,
        "company_code": 업체코드,
        "business_number": 사업자번호,
        "company_name": 업체명,
        "region": 지역,
        "region_detail": 지역상세,
        "business_category": 업태,
        "business_type": 업종,
        "business_detail": 업종상세,
        "orders": 원주문내용,
        "af_orders": 파싱주문내용,
        "address": 주소,
        "latitude": latitude,
        "longitude": longitude,
        "order_items": unique_product_jsons
    }, parsing_result


def process_orders_json_file():
    results = []
    with open(orders_file, mode='r', encoding='utf-8') as file:
        data = json.load(file)
        for row in data:
            # 0: 파싱DB처리목록, 1: parsing_result => 웹상출력할 목록
            result = process_order_parsing(row)
            results.append(result[0])
    return results


def process_orders_csv_file():
    results = []
    with open(orders_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # 0: 파싱DB처리목록, 1: parsing_result => 웹상출력할 목록
            result = process_order_parsing(row)
            results.append(result[0])
    return results

# 다바다 웹서비스 주문요청 프로세스
def process_orders_api_json():
    results = []

    # API 엔드포인트 URL
    url = "http://127.0.0.1:5001/davada_orders_list"

    # GET 요청 보내기
    response = requests.get(url)

    # 응답 상태 코드 확인
    if response.status_code == 200:
        # JSON 데이터 파싱
        loaded_data = response.json()

        # 각 주문 데이터 처리
        for row in loaded_data:
            # 0: 파싱DB처리목록, 1: parsing_result => 웹상출력할 목록
            result = process_order_parsing(row)
            results.append(result[0])
    else:
        print(f"Error: Unable to fetch data (Status Code: {response.status_code})")

    return results

# order parsing start
#results = process_orders_json_file()

# url json호출방식 처리
#results = process_orders_api_json()

# JSON 형식 출력
#print(json.dumps(results, ensure_ascii=False, indent=4))

# JSON 데이터를 SQLite3 데이터베이스에 저장
#save_to_db(results)