import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_ag_grid as dag  # Dash에서 ag-Grid 컴포넌트를 사용
import random

app = dash.Dash(__name__)

# 샘플 데이터 생성
def fetch_data(year_filter=None):
    sample_data = [
        {
            "country": random.choice(["서울", "부산", "경기", "인천", "광주"]),
            "sigungu": random.choice(["김포시", "수원시", "하남시", "남양주시", "강서구", "강남구"]),
            "year": random.choice([2016, 2012, 2008, 2004]),
            "month": random.choice(["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]),
            "business_category": random.choice(["숙박업", "음식업", "주점"]),
            "business_type": random.choice(["호텔", "모텔", "한식", "중식", "양식", "일식"]),
            "business_detail": random.choice(["횟집", "고기", "짜장", "수산", "꼬치", "주점"]),
            "qty": random.randint(0, 24),
            "price": random.randint(0, 100),
            "total": random.randint(0, 15),
        }
        for i in range(24)
    ]

    # 특정 년도 필터링
    if year_filter and year_filter != "전체":
        sample_data = [row for row in sample_data if row["year"] == int(year_filter)]

    return sample_data

# 컬럼 정의
column_defs = [
    {"headerName": "지역", "field": "country", "rowGroup": True, "cellStyle": {"textAlign": "center"}, "cellRendererParams": {"groupCellRenderer": "customGroupRenderer"} },
    {"headerName": "시군구", "field": "sigungu", "rowGroup": True, "cellStyle": {"textAlign": "center"},"cellRendererParams": {"groupCellRenderer": "customGroupRenderer"} },
    {"headerName": "년", "field": "year", "rowGroup": False, "cellClass": "group-cell"},
    {"headerName": "월", "field": "month", "rowGroup": False, "cellClass": "group-cell"},
    {"headerName": "업태", "field": "business_category"},
    {"headerName": "업종", "field": "business_type"},
    {"headerName": "업종상세", "field": "business_detail"},
    {
        "headerName": "수량",
        "field": "qty",
        "aggFunc": "sum",
        "cellStyle": {
            "color": "blue",
        }
    },
    {
        "headerName": "금액",
        "field": "price",
        "aggFunc": "sum",
        "cellStyle": {
            "color": "blue",
        }
    },
    {
        "headerName": "Total",
        "field": "total",
        "aggFunc": "sum",
        "cellStyle": {
            "color": "red",
            "fontWeight": "bold",
        }
    },
]

# 기본 컬럼 설정
default_col_def = {
    "sortable": True,
    "filter": True,
    "resizable": True,
    "enablePivot": True,
    "enableRowGroup": True,
    "enableValue": True,
    "headerClass": "grid-header-centered",  # 헤더 정렬용 CSS 클래스
  #  "headerStyle": {"textAlign": "center"},  # 헤더 중앙 정렬
}

# AG Grid 옵션 (그룹화 및 피벗 설정)
grid_options = {
    "pagination": False,
    "paginationAutoPageSize": False,
    "headerHeight": 37,
    "rowHeight": 32,
    "localeText": {"noRowsToShow": "데이터가 없습니다."},
    "suppressContextMenu": True,
    "wrapHeaderText": True,
    "rowDragManaged": True,
    "suppressAggFuncInHeader": True,
    "autoGroupColumnDef": {
        "minWidth": 50,
        "cellRendererParams": {
            "footerValueGetter": "params => params.node.level === -1 ? '총계' : `소계(${params.value})`"
        },
    },
    "groupDefaultExpanded": 1,
    "groupDisplayType": "singleColumn",
    "animateRows": True,
    "showOpenedGroup": True,
    "rowGroupPanelShow": "always",
    "pinnedBottomRowData": [],  # Empty initially, will be updated with totals
    "columnDefs": column_defs,
    "defaultColDef": default_col_def,
}

def grid_layout(row_data):
    # 합계를 계산하여 pinnedRowData로 설정
    total_qty = sum([row['qty'] for row in row_data])
    total_price = sum([row['price'] for row in row_data])
    total = total_qty + total_price

    # Footer row 데이터
    pinned_bottom_row_data = [
        {"business_detail": "합계", "qty": total_qty, "price": total_price, "total": total}]

    html_ag_grid = html.Div([
        html.Link(
            rel='stylesheet',
            href='/assets/styles.css'  # assets 폴더 내 스타일 시트 파일
        ),
        html.H2("🏆통계분석그리드"),
        html.Div([
            html.Label("년 선택:"),
            dcc.Dropdown(
                id="year-dropdown",
                options=[{"label": str(year), "value": str(year)} for year in ["전체", 2016, 2012, 2008, 2004]],
                value="전체",
                clearable=False,
                style={"width": "80px"}  # width 크기 설정
            ),
            html.Button("검색", id="search-btn", n_clicks=0),
            html.Button("엑셀로 내보내기", id="export-btn", n_clicks=0),  # 엑셀 내보내기 버튼 추가
           #  html.Script('''
           #     // 엑셀 내보내기 함수
           #     function exportToExcel() {
           #              var gridOptions = window.dash_clientside.callback_context.outputs['data-grid.rowData'].value;
           #              var excelExportParams = {
           #                  fileName: "data_export.xlsx",
           #                  columnKeys: ["country", "sigungu", "year", "month", "business_category", "business_type", "business_detail", "qty", "price", "total"],
           #                  skipHeader: false,  // 헤더 포함
           #              };
           #              var grid = document.getElementById("data-grid");
           #              grid.api.exportDataAsExcel(excelExportParams);
           #          }
           #
           #      // 엑셀 버튼 클릭 시 exportToExcel 함수 호출
           #      document.getElementById('export-btn').addEventListener('click', function() {
           #          alert('xxx');
           #          exportToExcel();
           #      });
           # ''')
        ], style={"display": "flex", "gap": "10px", "marginBottom": "10px"}),
        dag.AgGrid(  # AgGrid를 사용하여 그리드 생성
            id="data-grid",
            enableEnterpriseModules=True,
            licenseKey="CompanyName=MiraeWeb Inc._on_behalf_of_Davada Co., Ltd.,LicensedApplication=Text order management team,LicenseType=SingleApplication,LicensedConcurrentDeveloperCount=1,LicensedProductionInstancesCount=0,AssetReference=AG-035008,SupportServicesEnd=18_November_2023_[v2]_MTcwMDI2NTYwMDAwMA==acbe92b70e8f8af7bb2df844bc6cc28a",
            columnDefs=column_defs,
            rowData=row_data,
            defaultColDef=default_col_def,
            dashGridOptions={**grid_options,
                             "pinnedBottomRowData": pinned_bottom_row_data},  # Footer row 설정
            className="ag-theme-balham custom-grid",
            columnSize="sizeToFit",
            style={"height": "500px", "width": "90%",  "textAlign": "center"},
            dangerously_allow_code=True,  # JavaScript 코드 실행 허용
        ),
        #html.Button("🔄 Refresh Data", id="refresh-btn"),
        html.Button("🧹 Reset Data", id="reset-btn"),  # 새로운 초기화 버튼 추가
        html.Script('''
            //
            function customGroupRenderer(params) {
                // Apply blue background to group rows
                if (params.node.group) {
                    var eGroupCell = params.eGridCell;
                    eGroupCell.style.backgroundColor = "blue";  // Set the background color to blue
                    eGroupCell.style.color = "white";  // Set the text color to white
                }
                return params.value;
            }
            function handleColumnMoved(params) {
                const movedColumn = params.column;
                const allColumns = params.columnApi.getAllColumns();
                const isGroupColumn = movedColumn.getColId().includes('group');

                if (isGroupColumn) {
                    // 그룹 컬럼을 드래그로 제거
                    params.columnApi.getColumnsVisible().forEach((col) => {
                        if (col === movedColumn) {
                            params.columnApi.getAllColumns().forEach(function(col) {
                                params.columnApi.getColumnState().forEach(function(state){
                                    if(state.colId === movedColumn) {
                                        params.columnApi.setColumnState([]);
                                    }
                                });
                            });
                        }
                    });
                }
            }
        ''')
    ])
    return html_ag_grid


def generate_layout():
    return grid_layout(fetch_data())

# Dash 컴포넌트 구성
app.layout = generate_layout()

# 버튼 클릭 시 데이터 갱신
@app.callback(
    Output("data-grid", "rowData"),
    Output("data-grid", "dashGridOptions"),
    Input("search-btn", "n_clicks"),
    Input("reset-btn", "n_clicks"),  # 새로운 버튼 클릭 이벤트 추가
    #Input("export-btn", "n_clicks"),  # 엑셀 버튼 클릭 이벤트 추가
    State("year-dropdown", "value"),
    prevent_initial_call=True
)

def update_data(n_clicks_search, n_clicks_reset, selected_year):

    # 어떤 버튼이 눌렸는지 확인
    triggered_id = ctx.triggered_id  # Dash 2.x 이상에서는 ctx.triggered_id 사용
    print(f"Triggered by: {triggered_id}")

    if triggered_id == "reset-btn":
        # 리셋 버튼 클릭 시 빈 데이터 반환
        return [], {**grid_options, "pinnedBottomRowData": []}

    # if triggered_id == "export-btn":
    #      return [], {} # 엑셀 다운로드 트리거는 JavaScript에서 처리

    # 리프레시 버튼 클릭 시 새 데이터로 갱신
    row_data = fetch_data(selected_year)

    total_qty = sum([row['qty'] for row in row_data])
    total_price = sum([row['price'] for row in row_data])
    total = total_qty + total_price

    # Footer row 데이터
    pinned_bottom_row_data = [
        {"business_detail": "합계", "qty": total_qty, "price": total_price, "total": total}]

    return row_data, {**grid_options, "pinnedBottomRowData": pinned_bottom_row_data}


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
