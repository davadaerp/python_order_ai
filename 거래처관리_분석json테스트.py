import json

# 업태업종.json 파일 읽기 (예시: 업태업종.json 경로로 변경 필요)
with open('업태업종.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 전국시군구.json 파일 읽기 (예시: 전국시군구.json 경로로 변경 필요)
with open('전국시군구.json', 'r', encoding='utf-8') as file:
    regions = json.load(file)

# 거래처명과 주소 목록 (예시: 거래처명과 주소를 추가)
businesses = [
    {"거래처명": "놀부부대찌게", "주소": "경기도 김포시 운양동 반도유보라 6차"},
    {"거래처명": "마라탕", "주소": "서울특별시 강서구 운양동 반도유보라 6차"}
]

# 업태를 찾기 위한 함수
def find_business_type(business_name):
    for category in data["업종"]:
        for subcategory in category["세부 별명"]:
            if subcategory["별명"] in business_name:  # 별명이 거래처명에 포함되면
                return category["이름"]  # 업종 이름을 반환
    return "업종 없음"  # 해당 업종이 없으면 "업종 없음" 반환


# 업태 찾기 함수 (업종을 기반으로 업태를 찾는다)
def find_category_for_business(business_type):
    for category in data["업태"]:
        for subcategory in category["세부 별명"]:
            if subcategory["별명"] == business_type:  # 업종 이름이 업태의 세부 별명에 포함되면
                return category["이름"]  # 업태 이름을 반환
    return "업태 없음"  # 해당 업태가 없으면 "업태 없음" 반환


# 시도 이름을 찾기 위한 함수
def find_sido_from_address(address):
    for region in regions:
        if region.get("시도 이름") in address:  # 시도 이름이 주소에 포함되면
            return region["시도 이름"], region["시군구"]
    return "시도 없음", []  # 해당 시도 이름이 없으면 "시도 없음" 반환


# 시군구 찾기 함수
def find_sigu_from_address(address, sido_name, sigungu_list):
    # 시군구 목록이 딕셔너리로 되어 있을 경우, "시군구 이름"만 리스트로 추출하여 검색
    sigungu_names = [sigungu["시군구 이름"] for sigungu in sigungu_list]

    for sigungu in sigungu_names:
        if sigungu in address:
            return sigungu
    return "시군구 없음"


# 업종상세를 찾기 위한 함수
def find_business_detail(business_name):
    for category in data["업종상세"]:
        for subcategory in category["세부 별명"]:
            if subcategory["별명"] in business_name:  # 업종상세의 세부 별명이 거래처명에 포함되면
                return category["이름"]  # 업종상세 이름을 반환
    return "업종상세 없음"  # 해당 업종상세가 없으면 "업종상세 없음" 반환


# 거래처명과 업종 출력
for business in businesses:
    business_name = business["거래처명"]
    address = business["주소"]

    # 업종과 업태 찾기
    business_type = find_business_type(business_name)
    # 업태는 업종을 먼저 찾고서 해당 업종을 넘겨준다.
    business_category = find_category_for_business(business_type)
    # 업종상세 찾기
    business_detail = find_business_detail(business_name)
    #
    print(f"거래처명: {business_name}, 업종: {business_type}, 업태: {business_category}, 업종상세: {business_detail}")

    # 시도 이름과 시군구 찾기
    sido_name, sigungu_list = find_sido_from_address(address)
    sigungu_name = find_sigu_from_address(address, sido_name, sigungu_list)

    print(f"주소: {address}, 시도: {sido_name}, 시군구: {sigungu_name}\n")
