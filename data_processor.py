"""
데이터 전처리 및 가공 모듈
"""
import pandas as pd
from typing import Dict, List, Any, Tuple
import mapping_utils


def load_and_preprocess_data(input_file: str, config: Dict[str, Any], mapping_dict: Dict[str, Dict[str, str]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    데이터 로드 및 전처리
    
    Args:
        input_file: 입력 파일 경로
        config: 렌탈사 설정 정보
        mapping_dict: 매핑 딕셔너리
        
    Returns:
        전처리된 데이터프레임, 필터링된 데이터프레임
    """
    # CSV 파일 로드
    print(f"'{input_file}' 파일 로딩 중...")
    rental_df = pd.read_csv(input_file, encoding='utf-8')
    print(f"로딩 완료: {len(rental_df)}개 행 발견")
    
    # 필요한 필드만 선택
    df = rental_df[["모델명", config['amount_field'], "영업분류", "관리부서", "거래처명", "관리지점"] + config['team_fields']].copy()
    
    # 금액 필드 변환 (정수 타입으로)
    df["금액"] = df[config['amount_field']].replace(",", "", regex=True).astype(float).astype(int)
    
    # 팀명 처리 (우선순위에 따라)
    df["원본팀명"] = df[config['team_fields'][0]].copy()
    for field in config['team_fields'][1:]:
        df["원본팀명"] = df["원본팀명"].combine_first(df[field])
    
    # 매핑 적용
    df["매핑정보"] = df["원본팀명"].apply(lambda x: mapping_utils.apply_mapping(x, mapping_dict))
    
    # 매핑 정보에서 필드 추출
    df["팀명"] = df["매핑정보"].apply(lambda x: x["present"])
    df["CD_ACCT"] = df["매핑정보"].apply(lambda x: x["CD_ACCT"])
    df["CD_PJT"] = df["매핑정보"].apply(lambda x: x["CD_PJT"])
    
    # 적요 생성
    df["적요"] = f"{config['note_prefix']}(" + df["팀명"] + ")"
    
    # MNG 코드 설정
    df["CD_MNG1"] = config['cost_center']  # 코스트센터
    df["CD_MNG3"] = config['partner_code']  # 거래처 코드
    
    # 매핑된 항목만 선택 (CD_ACCT와 CD_PJT가 있는 항목만)
    df_filtered = df[(df["CD_ACCT"] != "") & (df["CD_PJT"] != "")].copy()
    print(f"매핑된 항목: {len(df_filtered)}개 / 전체 {len(df)}개")
    
    return df, df_filtered


def summarize_data(df_filtered: pd.DataFrame, mapping_dict: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """
    데이터 요약 정보 생성
    
    Args:
        df_filtered: 필터링된 데이터프레임
        mapping_dict: 매핑 딕셔너리
        
    Returns:
        데이터 요약 정보
    """
    total_amount = df_filtered["금액"].sum()
    
    # 매핑 결과 요약
    mapping_summary = mapping_utils.get_mapping_summary(df_filtered, mapping_dict)
    
    # 계정 사용 현황
    account_counts = df_filtered['CD_ACCT'].value_counts().to_dict()
    
    return {
        'total_count': len(df_filtered),
        'total_amount': total_amount,
        'account_counts': account_counts,
        'mapping_summary': mapping_summary
    }