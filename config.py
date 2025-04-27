"""
설정 파일 및 경로 관리 모듈
"""
import os
from datetime import datetime

# 기본 파일 경로 설정
INPUT_DIR = os.path.join(os.getcwd(), 'input')
OUTPUT_DIR = os.path.join(os.getcwd(), 'output')
MAPPING_DIR = os.path.join(os.getcwd(), 'mapping')
TEMPLATE_DIR = os.path.join(os.getcwd(), 'templates')

# 디렉토리가 없으면 생성
for directory in [INPUT_DIR, OUTPUT_DIR, MAPPING_DIR, TEMPLATE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# 현재 날짜 정보
CURRENT_DATE = datetime.now().strftime("%Y%m%d")

# 렌탈사 설정 (추후 다른 렌탈사가 추가될 수 있음)
RENTAL_COMPANIES = {
    '한국렌탈': {
        'input_file': os.path.join(INPUT_DIR, '한국렌탈_렌탈료.csv'),
        'mapping_file': os.path.join(MAPPING_DIR, 'test.json'),
        'erp_form_file': os.path.join(TEMPLATE_DIR, 'erp_form.csv'),
        'output_csv': os.path.join(OUTPUT_DIR, f'자동전표_한국렌탈_{CURRENT_DATE}.csv'),
        'output_excel': os.path.join(OUTPUT_DIR, f'자동전표_한국렌탈_{CURRENT_DATE}.xlsx'),
        'partner_code': '101388',  # 거래처 코드 (한국렌탈: 101388)
        'cost_center': '5020',     # 코스트센터(운영2)
        'expense_acct': '53000',   # 기본 비용 계정
        'payable_acct': '25300',   # 미지급금 계정
        'id_write': '00616',       # 사원번호 (김하리)
        'cd_company': '1200',      # 회사 코드
        'cd_pc': '1200',           # 회계단위
        'cd_wdept': '1010',        # 작성부서
        'amount_field': '3월렌탈료',  # 금액 필드명
        'team_fields': ['3월 변경PJT', '2월 PJT'],  # 팀 정보 필드명 (우선순위 순)
        'note_prefix': '테스트 한국렌탈㈜_PC 렌탈료',  # 적요 접두어
    }
}

# 기본 설정값
DEFAULT_ENCODING = 'utf-8'
CSV_OUTPUT_ENCODING = 'utf-8-sig'  # Excel에서 한글이 깨지지 않도록 BOM 포함

# ERP 관련 설정
ERP_DATA_ROW_START = 4  # 데이터 시작 행 (5행)
ERP_DOCUMENT_TYPE = '11'  # 전표유형 (11: 일반)
ERP_APPROVAL_STATUS = '1'  # 승인여부 (1: 미결/임시)
ERP_PROCESS_STATUS = 'N'  # 전표처리결과 (N: 미처리/임시)
ERP_DOCUMENT_GUBUN = '3'  # 전표구분 (3: 대체전표)