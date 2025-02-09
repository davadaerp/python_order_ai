import re
import csv
import json

import requests

from 통계분석_db_utils import save_to_db  # 외부 파일에서 save_to_db 함수 임포트

api_key = "AIzaSyAH_84wbHYlDMygF4uiok4k1EVQsShqnT8"  # 본인의 API 키를 입력하세요

# 한글 숫자 매핑
korean_number_map = {
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
    '아흔아홉': '99', '백': '100'
}

# 단위(개, 짝, 병 등) 제거하는 함수 (숫자 뒤의 단위 제거)
def remove_units(text):
    text = re.sub(r'\s*(병|생)(\d)', r'\1\2', text)  # '병 2'와 같이 공백을 없앰
    text = re.sub(r'(\d)(개|짝|병|통|세트|박스|팩)', r'\1', text)  # 숫자 뒤 단위 제거
    return text

# 한글 숫자를 숫자로 변환
def convert_korean_numbers(text, korean_number_map):
    for kor_num, digit in korean_number_map.items():
        text = text.replace(kor_num, digit)
    text = re.sub(r'\s*(\d)', r'\1', text)  # 숫자 앞에 공백 제거
    return text

# CSV 파일 읽기 및 역방향 조회 테이블 생성
def read_csv_and_create_reverse_lookup(csv_file):
    reverse_lookup = {}
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            product_code = row['상품코드']
            product_name = row['상품명']
            alcoholic_beverage = row['주종']
            product_aliases = row['상품별명'].split(',')
            for alias in product_aliases:
                if alias not in reverse_lookup:
                    reverse_lookup[alias] = []
                reverse_lookup[alias].append((product_code, product_name, alcoholic_beverage, int(row['상품단가'])))
    return reverse_lookup

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
        return None, None


# 하위 항목을 통해 상위 항목을 찾는 함수
def find_parent_items(item, reverse_lookup):
    return reverse_lookup.get(item, [])

# 파일 경로
csv_file = 'products.csv'
orders_file = 'orders.csv'

# 역방향 조회 테이블 생성
reverse_lookup = read_csv_and_create_reverse_lookup(csv_file)

# 결과 목록을 저장할 리스트
results = []

# 주문 처리
with open(orders_file, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    for row in reader:
        주문일자 = row['주문일자']
        업체코드 = row['업체코드']
        사업자번호 = row['사업자번호']
        업체명 = row['업체명']
        지역 = row['지역']
        업종 = row['업종']
        주소 = row['주소']
        주문내용 = row['주문내용']
        원주문내용 = row['주문내용']

        #print(f"\n처리 중인 업체: {주문일자}, {업체코드}, {사업자번호}, {업체명}, {지역}, {업종}")

        # 위도, 경도 가져오기
        latitude, longitude = get_lat_lng(주소, api_key)

        if latitude is not None and longitude is not None:
            print(f"주소: {주소}, 위도: {latitude}, 경도: {longitude}")
        else:
            latitude, longitude = 0, 0
            print(f"주소: {주소}, 위도/경도 정보 없음")

        # 한글 숫자 변환 및 단위 제거
        주문내용 = convert_korean_numbers(주문내용, korean_number_map)
        주문내용 = remove_units(주문내용)

        # 숫자와 결합된 텍스트를 추출하고 매핑
        matches = re.findall(r'([가-힣]+)(\d+)', 주문내용)
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
                parent_code, parent_name, alcoholic_beverage, price = possible_parents[0]
                total_price = price * count  # 주문금액 계산
                product_counts.append(f"{parent_code}-{parent_name}-{alcoholic_beverage}-{price}원-{count}개-{total_price}원")
                product_orders.append(f"{parent_code}-{parent_name}-{count}개")
                product_jsons.append({
                    "product_code": parent_code,
                    "product_name": parent_name,
                    "alcoholic_beverage": alcoholic_beverage,
                    "unit_price": price,
                    "quantity": count,
                    "total_price": total_price
                })

        # 결과 형식으로 변환
        output = ", ".join(product_counts)
        파싱주문내용 = ", ".join(product_orders)

        # 업체정보와 주문내용 분석 결과를 함께 출력
        result = (
            f"주문일자: {주문일자}, 업체코드: {업체코드}, 사업자번호: {사업자번호}, 업체명: {업체명}, 지역: {지역}, 업종: {업종}\n"
            f"주문내용: {원주문내용}, 변경내용: {주문내용}\n"
            f"주문내용 분석 결과: {output}\n"
        )
        print(result)

        results.append({
            "order_date": 주문일자,
            "company_code": 업체코드,
            "business_number": 사업자번호,
            "company_name": 업체명,
            "region": 지역,
            "business_type": 업종,
            "orders": 원주문내용,
            "af_orders": 파싱주문내용,
            "address": 주소,
            "latitude": latitude,
            "longitude": longitude,
            "order_items": product_jsons
        })

# JSON 형식 출력
#print(json.dumps(results, ensure_ascii=False, indent=4))

# JSON 데이터를 SQLite3 데이터베이스에 저장
save_to_db(results)