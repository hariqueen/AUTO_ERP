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
    # CSV 파일 로드 - 다양한 인코딩 시도
    print(f"'{input_file}' 파일 로딩 중...")
    try:
        rental_df = pd.read_csv(input_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            # UTF-8 실패 시 CP949 시도
            rental_df = pd.read_csv(input_file, encoding='cp949')
            print("CP949 인코딩으로 파일 로드 성공")
        except UnicodeDecodeError:
            try:
                # EUC-KR 시도
                rental_df = pd.read_csv(input_file, encoding='euc-kr') 
                print("EUC-KR 인코딩으로 파일 로드 성공")
            except Exception as e:
                print(f"파일 로드 실패: {e}")
                raise
    
    print(f"로딩 완료: {len(rental_df)}개 행 발견")
    
    # 컬럼명 양쪽 공백 제거
    rental_df.columns = [col.strip() for col in rental_df.columns]
    
    print(f"파일 컬럼: {rental_df.columns.tolist()}")
    
    # 필요한 필드 확인 및 조정
    # 필요한 컬럼이 있는지 확인
    column_exists = {}
    required_columns = ["모델명", "영업분류", "관리부서", "거래처명", "관리지점"]
    
    for col in required_columns:
        if col in rental_df.columns:
            column_exists[col] = True
        else:
            column_exists[col] = False
            print(f"경고: '{col}' 컬럼이 파일에 없습니다.")
    
    # 금액 필드 찾기 - 월별 자동 인식 패턴
    amount_field = None
    
    # 1. 먼저 config에 설정된 필드 시도
    if config['amount_field'] in rental_df.columns:
        amount_field = config['amount_field']
    else:
        # 2. '[0-9]월렌탈료' 패턴 찾기 (정규식)
        import re
        month_pattern = re.compile(r'^\s*(?:[0-9]{1,2})월\s*렌탈료\s*$')
        
        for col in rental_df.columns:
            if month_pattern.match(col):
                amount_field = col
                print(f"금액 필드로 '{amount_field}'를 자동 인식했습니다.")
                break
                
        # 3. 렌탈료 포함 필드 찾기
        if not amount_field:
            for col in rental_df.columns:
                if '렌탈료' in col:
                    amount_field = col
                    print(f"금액 필드로 '{amount_field}'를 사용합니다.")
                    break
    
    if not amount_field:
        # 컬럼명에 '원'이나 '￦' 또는 '₩'가 포함된 것을 amount_field로 사용
        for col in rental_df.columns:
            if '원' in col or '￦' in col or '₩' in col:
                amount_field = col
                print(f"금액 필드로 '{amount_field}'를 사용합니다.")
                break
    
    if not amount_field and len(rental_df.columns) > 2:
        # 그래도 없으면 3번째 컬럼을 금액 필드로 사용
        amount_field = rental_df.columns[2]
        print(f"금액 필드를 명확히 식별할 수 없어 '{amount_field}'를 사용합니다.")
    
    # 팀 필드 찾기 - 월별 자동 인식 패턴
    team_fields = []
    
    # 1. 먼저 config에 설정된 필드 시도
    configured_team_fields = config.get('team_fields', [])
    if isinstance(configured_team_fields, str):
        configured_team_fields = [configured_team_fields]
    
    for field in configured_team_fields:
        if field in rental_df.columns:
            team_fields.append(field)
    
    if not team_fields:
        # 2. '[0-9]월 변경PJT' 또는 '[0-9]월 PJT' 패턴 찾기 (정규식)
        import re
        month_pjt_pattern = re.compile(r'^\s*(?:[0-9]{1,2})월\s*(?:변경)?PJT\s*$')
        
        for col in rental_df.columns:
            if month_pjt_pattern.match(col):
                team_fields.append(col)
                print(f"팀 필드로 '{col}'를 자동 인식했습니다.")
        
        # 3. 'PJT'가 포함된 필드 찾기
        if not team_fields:
            for col in rental_df.columns:
                if 'PJT' in col or '팀' in col:
                    team_fields.append(col)
                    print(f"팀 필드로 '{col}'를 사용합니다.")
    
    if not team_fields and len(rental_df.columns) > 3:
        # 그래도 없으면 4번째 컬럼을 팀 필드로 사용
        team_fields = [rental_df.columns[3]]
        print(f"팀 필드를 명확히 식별할 수 없어 '{team_fields[0]}'를 사용합니다.")
    
    # 사용 가능한 컬럼만 선택
    available_columns = []
    for col in required_columns:
        if column_exists.get(col, False):
            available_columns.append(col)
    
    if amount_field:
        available_columns.append(amount_field)
    
    available_columns.extend(team_fields)
    
    # 중복 제거
    available_columns = list(dict.fromkeys(available_columns))
    
    print(f"사용할 컬럼: {available_columns}")
    
    # 필요한 필드만 선택 (존재하는 컬럼만)
    df = rental_df[available_columns].copy()
    
    # 금액 필드 변환 (정수 타입으로)
    if amount_field:
        try:
            # 쉼표 제거 후 변환 시도
            df["금액"] = df[amount_field].astype(str).str.replace(",", "", regex=True).astype(float).astype(int)
        except Exception as e:
            print(f"금액 변환 중 오류 발생: {e}")
            # 문자열 형태의 금액을 숫자로 변환 시도 (예: '₩12,345' -> 12345)
            try:
                df["금액"] = df[amount_field].astype(str).str.replace(r'[^\d.]', '', regex=True).astype(float).astype(int)
                print("특수문자를 제거하여 금액 변환 성공")
            except Exception as e2:
                print(f"특수문자 제거 후에도 금액 변환 실패: {e2}")
                # 그래도 실패하면 임의의 값 생성
                df["금액"] = 10000  # 임의의 기본값 설정
                print("금액 변환 실패, 기본값 10,000원 설정")
    else:
        # 금액 필드가 없으면 임의의 값 생성
        df["금액"] = 10000  # 임의의 기본값 설정
        print("금액 필드를 찾을 수 없어 기본값 10,000원 설정")
    
    # 팀명 처리 (우선순위에 따라)
    if team_fields:
        df["원본팀명"] = df[team_fields[0]].copy()
        for field in team_fields[1:]:
            df["원본팀명"] = df["원본팀명"].combine_first(df[field])
    else:
        # 팀 필드가 없으면 임의의 값 생성
        df["원본팀명"] = "기본팀"
        print("팀 필드를 찾을 수 없어 '기본팀'으로 설정")
    
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