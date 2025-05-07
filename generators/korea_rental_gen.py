"""
ERP 데이터 생성 모듈
"""
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime
from core import config as cfg


def generate_erp_data(df_filtered: pd.DataFrame, company_config: Dict[str, Any]) -> pd.DataFrame:
    """
    ERP 업로드용 데이터프레임 생성
    
    Args:
        df_filtered: 필터링된 데이터프레임
        company_config: 렌탈사 설정 정보
        
    Returns:
        ERP 업로드용 데이터프레임
    """
    print("ERP 업로드용 데이터프레임 생성 중...")
    current_date = datetime.now().strftime("%Y%m%d")
    document_number = f"FI{current_date[-8:]}{company_config.get('id_write', '00000')[-3:]}"
    
    # 1. 차변 데이터 생성 (각 팀별 계정별 비용)
    debit_data = {
        "ROW_ID": [document_number] * len(df_filtered), 
        "ROW_NO": [str(i) for i in range(1, len(df_filtered)+1)],
        "NO_TAX": ["*"] * len(df_filtered),
        "CD_PC": [company_config['cd_pc']] * len(df_filtered),
        "CD_WDEPT": [company_config['cd_wdept']] * len(df_filtered),
        "NO_DOCU": [document_number] * len(df_filtered), 
        "NO_DOLINE": [str(i) for i in range(1, len(df_filtered)+1)],
        "CD_COMPANY": [company_config['cd_company']] * len(df_filtered),
        "ID_WRITE": [company_config['id_write']] * len(df_filtered),
        "CD_DOCU": [cfg.ERP_DOCUMENT_TYPE] * len(df_filtered),
        "DT_ACCT": [current_date] * len(df_filtered),
        "ST_DOCU": [cfg.ERP_APPROVAL_STATUS] * len(df_filtered),
        "TP_DRCR": ["1"] * len(df_filtered),  # 차대구분 (1: 차변)
        "CD_ACCT": df_filtered["CD_ACCT"].tolist(),  # 각 팀별 계정 코드
        "AMT": df_filtered["금액"].apply(lambda x: str(int(x)) if pd.notnull(x) else "0").tolist(),
        "CD_PARTNER": [company_config['partner_code']] * len(df_filtered),
        "NM_NOTE": df_filtered["적요"].tolist(),
        "TP_DOCU": [cfg.ERP_PROCESS_STATUS] * len(df_filtered),
        "NO_ACCT": ["0"] * len(df_filtered),
        "TP_GUBUN": [cfg.ERP_DOCUMENT_GUBUN] * len(df_filtered),
    }
    
    # 2. 대변 데이터 생성 (미지급금으로 합계 금액)
    total_amount = df_filtered["금액"].sum()
    total_amount_str = str(total_amount)
    
    # 대변 데이터
    credit_data = {
        "ROW_ID": [document_number], 
        "ROW_NO": [str(len(df_filtered) + 1)],  # 마지막 번호 다음
        "NO_TAX": ["*"],
        "CD_PC": [company_config['cd_pc']],
        "CD_WDEPT": [company_config['cd_wdept']],
        "NO_DOCU": [document_number], 
        "NO_DOLINE": [str(len(df_filtered) + 1)],  # 마지막 라인 다음
        "CD_COMPANY": [company_config['cd_company']],
        "ID_WRITE": [company_config['id_write']],
        "CD_DOCU": [cfg.ERP_DOCUMENT_TYPE],
        "DT_ACCT": [current_date],
        "ST_DOCU": [cfg.ERP_APPROVAL_STATUS],
        "TP_DRCR": ["2"],  # 차대구분 (2: 대변)
        "CD_ACCT": [company_config['payable_acct']],  # 미지급금 계정코드
        "AMT": [total_amount_str],  # 전체 금액의 합계
        "CD_PARTNER": [company_config['partner_code']],
        "NM_NOTE": [f"{company_config['note_prefix']} 미지급금"],  # 적요
        "TP_DOCU": [cfg.ERP_PROCESS_STATUS],
        "NO_ACCT": ["0"],
        "TP_GUBUN": [cfg.ERP_DOCUMENT_GUBUN],
    }
    
    # 3. 차변과 대변 데이터프레임 생성
    debit_df = pd.DataFrame(debit_data)
    credit_df = pd.DataFrame(credit_data)
    
    # 4. 두 데이터프레임 합치기
    erp_df = pd.concat([debit_df, credit_df], ignore_index=True)
    
    # 금액 필드 확인
    print("\nAMT 필드 확인:")
    print("차변 금액 합계:", df_filtered["금액"].sum())
    print("대변 금액:", total_amount)
    print("차변 건수:", len(debit_df))
    print("대변 건수:", len(credit_df))
    
    return erp_df


def prepare_erp_columns(erp_df: pd.DataFrame) -> pd.DataFrame:
    """
    ERP 표준 컬럼 구조로 데이터프레임 준비
    
    Args:
        erp_df: ERP 데이터프레임
        
    Returns:
        표준 컬럼 구조를 가진 ERP 데이터프레임
    """
    # 필드 순서 지정 - ERP 양식에 맞게 정확한 순서로 컬럼 정렬
    erp_columns = [
        "ROW_ID", "ROW_NO", "NO_TAX", "CD_PC", "CD_WDEPT", "NO_DOCU", "NO_DOLINE", 
        "CD_COMPANY", "ID_WRITE", "CD_DOCU", "DT_ACCT", "ST_DOCU", "TP_DRCR", 
        "CD_ACCT", "AMT", "CD_PARTNER", "DT_START", "DT_END", "AM_TAXSTD", 
        "AM_ADDTAX", "TP_TAX", "NO_COMPANY", "NM_NOTE", "CD_BIZAREA", "CD_DEPT", 
        "CD_CC", "CD_PJT", "CD_FUND", "CD_BUDGET", "NO_CASH", "ST_MUTUAL", 
        "CD_CARD", "NO_DEPOSIT", "CD_BANK", "UCD_MNG1", "UCD_MNG2", "UCD_MNG3", 
        "UCD_MNG4", "UCD_MNG5", "CD_EMPLOY", "CD_MNG", "NO_BDOCU", "NO_BDOLINE", 
        "TP_DOCU", "NO_ACCT", "TP_TRADE", "NO_CHECK3", "NO_CHECK4", "CD_EXCH", 
        "RT_EXCH", "CD_TRADE", "AM_EX", "TP_EXPORT", "NO_TO", "DT_SHIPPING", 
        "TP_GUBUN", "NO_INVOICE", "NO_ITEM", "MD_TAX1", "NM_ITEM1", "NM_SIZE1", 
        "QT_TAX1", "AM_PRC1", "AM_SUPPLY1", "AM_TAX1", "NM_NOTE1", "CD_BIZPLAN", 
        "CD_BGACCT", "CD_MNGD1", "NM_MNGD1", "CD_MNGD2", "NM_MNGD2", "CD_MNGD3", 
        "NM_MNGD3", "CD_MNGD4", "NM_MNGD4", "CD_MNGD5", "NM_MNGD5", "CD_MNGD6", 
        "NM_MNGD6", "CD_MNGD7", "NM_MNGD7", "CD_MNGD8", "NM_MNGD8", "YN_ISS", 
        "FINAL_STATUS", "NO_BILL", "NM_BIGO", "TP_BILL", "TP_RECORD", "TP_ETCACCT", 
        "ST_GWARE", "SELL_DAM_NM", "SELL_DAM_EMAIL", "SELL_DAM_MOBIL", "SELL_DAM_TEL", 
        "NM_PUMM", "JEONJASEND15_YN", "DT_WRITE", "ST_TAX", "MD_TAX2", "NM_ITEM2", 
        "NM_SIZE2", "QT_TAX2", "AM_PRC2", "AM_SUPPLY2", "AM_TAX2", "NM_NOTE2", 
        "MD_TAX3", "NM_ITEM3", "NM_SIZE3", "QT_TAX3", "AM_PRC3", "AM_SUPPLY3", 
        "AM_TAX3", "NM_NOTE3", "MD_TAX4", "NM_ITEM4", "NM_SIZE4", "QT_TAX4", 
        "AM_PRC4", "AM_SUPPLY4", "AM_TAX4", "NM_NOTE4", "NM_PTR", "EX_HP", 
        "EX_EMIL", "NO_BIZTAX", "NO_ASSET", "TP_EVIDENCE", "NO_CAR", "NO_CARBODY", 
        "CD_BIZCAR", "NM_PARTNER", "YN_IMPORT", "YN_FIXASSET"
    ]
    
    # 나머지 열 추가 (빈 문자열로)
    for col in erp_columns:
        if col not in erp_df.columns:
            erp_df[col] = [""] * len(erp_df)
    
    return erp_df[erp_columns]


def set_management_items(erp_df: pd.DataFrame, df_filtered: pd.DataFrame, company_config: Dict[str, Any]) -> pd.DataFrame:
    """
    관리항목 설정
    
    Args:
        erp_df: ERP 데이터프레임
        df_filtered: 필터링된 데이터프레임
        company_config: 렌탈사 설정 정보
        
    Returns:
        관리항목이 설정된 ERP 데이터프레임
    """
    # 차변 행 설정
    debit_rows = erp_df["TP_DRCR"] == "1"
    erp_df.loc[debit_rows, "CD_CC"] = company_config['cost_center']  # 코스트센터
    
    # 부서코드 설정 (관리항목2) - 필수 항목으로 보임
    if 'cd_wdept' in company_config:
        erp_df.loc[debit_rows, "CD_DEPT"] = company_config['cd_wdept']  # 부서코드
    
    # CD_PJT를 정수형으로 확실하게 설정
    pjt_codes = df_filtered["CD_PJT"].astype(int).tolist()
    erp_df.loc[debit_rows, "CD_PJT"] = pjt_codes  # 프로젝트 코드
    
    # 대변 행 설정
    credit_rows = erp_df["TP_DRCR"] == "2"
    erp_df.loc[credit_rows, "CD_CC"] = company_config['cost_center']  # 코스트센터
    
    # 대변에도 부서코드 설정 필요
    if 'cd_wdept' in company_config:
        erp_df.loc[credit_rows, "CD_DEPT"] = company_config['cd_wdept']  # 부서코드
    
    return erp_df