import re


def filter_whiskey_orders(order_text):
    whiskey_aliases = {"화요25", "임페17", "윈17", "윈저시그니처12", "시그니처12"}  # 양주 관련 제품 목록

    # 특수문자 제거: 알파벳, 숫자, 한글, 공백만 남기기
    order_text = re.sub(r'[^a-zA-Z0-9가-힣\s]', '', order_text)

    whiskey_orders = []

    # whiskey_aliases에 해당하는 문자열 뒤에 숫자가 있으면 공백 추가
    for alias in whiskey_aliases:

        # 해당 품목 뒤에 공백이 있고, 그 뒤에 숫자가 있는 경우 찾기
        matches = re.findall(fr'({alias})\s*(\d+)', order_text)
        for match in matches:
            print(f"품목명: {match[0]}, 숫자: {match[1]}")
            whiskey_orders.append((match[0], match[1]))

    return whiskey_orders

# 샘플 테스트
test_order = "안녕하세요 임페17 5화요25 3개 테라3이슬2 켈리1윈17-3박스,윈17 5박스윈저시그니처12 10상자 수복1,처음1"
result = filter_whiskey_orders(test_order)
print("결과:", result)
