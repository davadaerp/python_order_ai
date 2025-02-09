# 오라클 다운로드 라이브러리
# https://www.oracle.com/ng/database/technologies/instant-client/macos-intel-x86-downloads.html
# library 설치 : 오라클 arm버전이 안나옴 ㅠ.ㅠ

import oracledb

# Oracle DB 접속 정보
DB_DSN = "222.239.76.48:1521/ora11g"
DB_USER = "davada"
DB_PASSWORD = "davada#$0"

# Oracle Client 초기화(Thick모드, Thin모드(밑에 init없이 사용하는 11.2버전부터 지원함 ㅠ.ㅠ)
#oracledb.init_oracle_client(config_dir=None)  # No client required

def get_connection():
    """오라클 DB 연결을 반환하는 함수"""
    return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)

def list_retailshop(busi_r_no):
    """ordr_mang_entprs 목록을 조회하여 출력하는 함수"""
    QUERY = """
        SELECT  ORDR_BUSI_R_NO,
                ENTPRS_NAME_HANGUL,
                REPRS_NAME,
                HD_OFFC_TEL_NO,
                CHRG_NAME,
                HD_OFFC_ADDR1
                FROM ordr_mang_entprs
        WHERE busi_r_no = :busi_r_no
    """
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(QUERY, busi_r_no=busi_r_no)
                rows = cursor.fetchall()

                print("=== Order Management Enterprises ===")
                for row in rows:
                    print({"route_rule": "retailshop", "data": row})
    except oracledb.DatabaseError as e:
        print("Database error:", e)

# 함수 실행
busi_r_no = '119-13-89653'
list_retailshop(busi_r_no)
