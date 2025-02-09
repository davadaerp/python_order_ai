import requests

# API 엔드포인트 URL
url = "http://127.0.0.1:5000/davada_orders_list"

# GET 요청 보내기
response = requests.get(url)

# 응답 상태 코드 확인
if response.status_code == 200:
    # JSON 데이터 파싱
    loaded_data = response.json()

    # 읽은 데이터를 출력
    for order in loaded_data:
        print(f"업체명: {order['entprs_name']}, 주문일자: {order['ordr_date']}, 주문내용: {order['orderContent']}")
else:
    print(f"Error: Unable to fetch data (Status Code: {response.status_code})")