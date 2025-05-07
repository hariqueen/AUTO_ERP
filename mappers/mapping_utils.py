"""
팀명 매핑 관련 유틸리티 모듈
"""
import json
import pandas as pd
from typing import Dict, List, Any


def load_mapping_file(mapping_file: str) -> Dict[str, Dict[str, str]]:
    """
    매핑 파일을 로드하여 딕셔너리 형태로 반환
    
    Args:
        mapping_file: 매핑 파일 경로
        
    Returns:
        매핑 딕셔너리: {팀명: {present: 현재팀명, CD_ACCT: 계정코드, CD_PJT: 프로젝트코드}}
    """
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping_list = json.load(f)
        
        # 매핑 딕셔너리 생성
        mapping_dict = {}
        for item in mapping_list:
            mapping_dict[item['past']] = {
                'present': item['present'],
                'CD_ACCT': item['CD_ACCT'],
                'CD_PJT': item['CD_PJT']
            }
        
        print(f"매핑 정보 로드 완료: {len(mapping_dict)}개 항목")
        return mapping_dict
    
    except Exception as e:
        print(f"매핑 파일 로드 중 오류 발생: {e}")
        return {}


def apply_mapping(team_name: str, mapping_dict: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """
    팀명에 매핑 정보 적용
    
    Args:
        team_name: 원본 팀명
        mapping_dict: 매핑 딕셔너리
        
    Returns:
        매핑된 정보: {present: 현재팀명, CD_ACCT: 계정코드, CD_PJT: 프로젝트코드}
    """
    if pd.isna(team_name) or team_name == "":
        return {"present": "", "CD_ACCT": "", "CD_PJT": ""}
    
    if team_name in mapping_dict:
        return mapping_dict[team_name]
    
    # 없는 경우 빈 값 반환
    return {"present": team_name, "CD_ACCT": "", "CD_PJT": ""}


def get_unmapped_teams(df: pd.DataFrame) -> List[str]:
    """
    매핑되지 않은 팀명 목록 추출
    
    Args:
        df: 데이터프레임
        
    Returns:
        매핑되지 않은 팀명 목록
    """
    unmapped_df = df[(df["CD_ACCT"] == "") | (df["CD_PJT"] == "")]
    return unmapped_df["원본팀명"].unique().tolist()


def get_mapping_summary(df_filtered: pd.DataFrame, mapping_dict: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """
    매핑 결과 요약 정보 생성
    
    Args:
        df_filtered: 필터링된 데이터프레임
        mapping_dict: 매핑 딕셔너리
        
    Returns:
        매핑 요약 정보: {mapped_teams: 매핑된 팀명 목록, unmapped_teams: 매핑되지 않은 팀명 목록}
    """
    mapped_teams = []
    for team in df_filtered["원본팀명"].unique():
        mapped_info = mapping_dict.get(team, {})
        mapped_teams.append({
            'original': team,
            'mapped': mapped_info.get('present', team),
            'acct': mapped_info.get('CD_ACCT', ''),
            'pjt': mapped_info.get('CD_PJT', '')
        })
    
    return {
        'mapped_teams': mapped_teams,
        'mapped_count': len(mapped_teams)
    }