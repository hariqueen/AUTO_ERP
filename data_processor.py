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
    
    # 컬럼명 양쪽 공백 제거 (더 엄격한 처리)
    original_columns = rental_df.columns.tolist()
    print("원본 컬럼명:")
    for col in original_columns:
        print(f"- '{col}'")

    # 컬럼명에서 공백 제거 및 처리
    rental_df.columns = [col.strip() for col in rental_df.columns]

    # 처리된 컬럼명 출력
    processed_columns = rental_df.columns.tolist()
    print("처리 후 컬럼명:")
    for i, col in enumerate(processed_columns):
        orig = original_columns[i] if i < len(original_columns) else "?"
        print(f"- '{orig}' -> '{col}'")

    # 컬럼명 중복 체크 및 처리
    if len(set(rental_df.columns)) != len(rental_df.columns):
        print("경고: 공백 제거 후 중복된 컬럼명이 있습니다.")
        duplicate_count = {}
        new_columns = []
        
        for col in rental_df.columns:
            if col in duplicate_count:
                duplicate_count[col] += 1
                new_col = f"{col}_{duplicate_count[col]}"
                new_columns.append(new_col)
                print(f"  중복 컬럼 처리: '{col}' -> '{new_col}'")
            else:
                duplicate_count[col] = 0
                new_columns.append(col)
        
        rental_df.columns = new_columns
    
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
    
    # 1. 먼저 config에 설정된 필드 시도 (앞뒤 공백 제거 후 비교)
    clean_amount_field = config['amount_field'].strip()
    for col in rental_df.columns:
        if col.strip() == clean_amount_field:
            amount_field = col
            print(f"금액 필드로 '{amount_field}'를 설정값에서 찾았습니다.")
            break
    
    if not amount_field:
        # 2. 'N월렌탈료' 패턴 찾기 - 공백 고려
        import re
        month_pattern = re.compile(r'^\s*(?:[0-9]{1,2})월렌탈료\s*$')
        
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
        # 4. 컬럼명에 '원'이나 '￦' 또는 '₩'가 포함된 것을 amount_field로 사용
        for col in rental_df.columns:
            if '원' in col or '￦' in col or '₩' in col:
                amount_field = col
                print(f"금액 필드로 '{amount_field}'를 사용합니다.")
                break
    
    # 금액 필드를 찾을 수 없으면 오류 발생
    if not amount_field:
        raise ValueError("금액 필드를 찾을 수 없습니다. 파일 형식을 확인해주세요.")
    
    # 금액 필드 확인 출력
    print(f"사용할 금액 필드: '{amount_field}'")
    print(f"금액 필드 샘플 값: {rental_df[amount_field].head().tolist()}")
    
    # 팀 필드 찾기 - 월별 자동 인식 패턴
    team_fields = []
    
    # 1. 먼저 config에 설정된 필드 시도
    configured_team_fields = config.get('team_fields', [])
    if isinstance(configured_team_fields, str):
        configured_team_fields = [configured_team_fields]
    
    for field in configured_team_fields:
        clean_field = field.strip()
        for col in rental_df.columns:
            if col.strip() == clean_field:
                team_fields.append(col)
                print(f"팀 필드로 '{col}'를 설정값에서 찾았습니다.")
                break
    
    if not team_fields:
        # 2. '[0-9]월 변경PJT' 패턴만 찾기 - 공백 허용
        import re
        # 공백 허용하고 '변경PJT'만 찾는 패턴
        month_pjt_pattern = re.compile(r'^\s*(?:[0-9]{1,2})월\s*변경PJT\s*$')
        
        for col in rental_df.columns:
            if month_pjt_pattern.match(col):
                team_fields.append(col)
                print(f"팀 필드로 '{col}'를 자동 인식했습니다 (변경PJT 패턴).")
    
    # 팀 필드를 찾을 수 없음 - 오류 발생
    if not team_fields:
        raise ValueError("팀 정보 필드를 찾을 수 없습니다. 파일 형식을 확인해주세요.")
    
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
    
    # 금액 필드 처리 - 간단한 방법으로 숫자만 추출
    print(f"금액 필드 '{amount_field}' 데이터 처리 중...")
    
    # 숫자로 변환 가능한 값만 유효한 것으로 간주 (한 줄로 처리)
    valid_amount_mask = pd.to_numeric(df[amount_field], errors='coerce').notna()
    
    # 유효하지 않은 행 수 출력
    invalid_rows = (~valid_amount_mask).sum()
    if invalid_rows > 0:
        print(f"금액이 없거나 숫자가 아닌 행(반납 항목) {invalid_rows}개를 제외합니다.")
    
    # 유효한 행만 선택
    df = df[valid_amount_mask].copy()
    
    # 금액 변환 - 단순화된 방법
    df["금액"] = pd.to_numeric(df[amount_field], errors='coerce')
    df["금액"] = df["금액"].astype(int)
    print(f"금액 변환 성공: 샘플 값 = {df['금액'].head().tolist()}")
    
    # 팀명 처리 (우선순위에 따라)
    if team_fields:
        df["원본팀명"] = df[team_fields[0]].copy()
        for field in team_fields[1:]:
            df["원본팀명"] = df["원본팀명"].combine_first(df[field])
    
    # 매핑 적용
    df["매핑정보"] = df["원본팀명"].apply(lambda x: mapping_utils.apply_mapping(x, mapping_dict))
    
    # 매핑 정보에서 필드 추출
    df["팀명"] = df["매핑정보"].apply(lambda x: x["present"])
    df["CD_ACCT"] = df["매핑정보"].apply(lambda x: x["CD_ACCT"])
    
    # CD_PJT를 정수형으로 변환하는 부분
    df["CD_PJT"] = df["매핑정보"].apply(lambda x: x["CD_PJT"])
    # 문자열이나 NaN 값 처리 후 정수형으로 변환
    df["CD_PJT"] = pd.to_numeric(df["CD_PJT"], errors='coerce').fillna(1000).astype(int)
    
    # 적요 생성
    df["적요"] = f"{config['note_prefix']}(" + df["팀명"] + ")"
    
    # MNG 코드 설정
    df["CD_MNG1"] = config['cost_center']  # 코스트센터
    df["CD_MNG3"] = config['partner_code']  # 거래처 코드
    
    # 매핑된 항목만 선택 (CD_ACCT와 CD_PJT가 있는 항목만)
    df_filtered = df[(df["CD_ACCT"] != "") & (df["CD_PJT"] != "")].copy()
    
    # 매핑되지 않은 팀명 정보 출력
    if len(df_filtered) < len(df):
        unmapped_teams = df[~df.index.isin(df_filtered.index)]["원본팀명"].unique()
        print(f"매핑되지 않은 팀명 {len(unmapped_teams)}개:")
        for team in unmapped_teams:
            print(f"- '{team}'")
        
        # 매핑되지 않은 항목이 있으면 경고 (전체 다 매핑 안 되는 경우만 오류)
        if len(df_filtered) == 0:
            raise ValueError("모든 팀명이 매핑되지 않았습니다. 매핑 파일을 확인해주세요.")
    
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