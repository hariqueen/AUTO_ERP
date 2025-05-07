"""
ERP 양식 및 템플릿 관련 유틸리티
"""
import pandas as pd
from typing import Dict, Any, Optional
from core import config as cfg

def load_erp_form_template(erp_form_file: str) -> Optional[pd.DataFrame]:
    """
    ERP 양식 파일 로드
    
    Args:
        erp_form_file: ERP 양식 파일 경로
        
    Returns:
        ERP 양식 데이터프레임 또는 None
    """
    try:
        erp_form = pd.read_csv(erp_form_file, encoding=cfg.DEFAULT_ENCODING)
        print(f"ERP 양식 파일 '{erp_form_file}'을 성공적으로 로드했습니다.")
        return erp_form
    except Exception as e:
        print(f"ERP 양식 파일 로드 실패: {e}")
        print("기본 양식 없이 진행합니다.")
        return None

def prepare_file_with_template(erp_df: pd.DataFrame, erp_form: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    ERP 양식을 적용하여 파일 준비
    
    Args:
        erp_df: ERP 데이터프레임
        erp_form: ERP 양식 데이터프레임
        
    Returns:
        결과 데이터프레임
    """
    if erp_form is not None:
        # 양식 파일의 컬럼 순서 사용
        form_columns = erp_form.columns.tolist()
        
        # 결과 데이터프레임을 양식 컬럼 순서에 맞게 재정렬
        for col in form_columns:
            if col not in erp_df.columns:
                erp_df[col] = ""
        
        erp_df = erp_df[form_columns]
        
        # erp_form 복사 (양식 파일의 처음 n행만 사용)
        result_df = erp_form.copy()
        
        # 양식 파일이 지정된 시작행보다 많으면 필요한 만큼만 유지
        if len(result_df) > cfg.ERP_DATA_ROW_START - 1:
            result_df = result_df.iloc[:(cfg.ERP_DATA_ROW_START - 1)]
        
        # 빈 행 추가 (필요한 경우)
        current_rows = len(result_df)
        target_rows = cfg.ERP_DATA_ROW_START - 1  # 시작행 - 1 (인덱스는 0부터 시작하므로)
        
        # 현재 행 수가 타겟 행 수보다 적으면 빈 행 추가
        if current_rows < target_rows:
            empty_rows_needed = target_rows - current_rows
            empty_df = pd.DataFrame([[""] * len(form_columns) for _ in range(empty_rows_needed)], columns=form_columns)
            result_df = pd.concat([result_df, empty_df], ignore_index=True)
        
        # 처리된 데이터 추가 (ERP_DATA_ROW_START행부터 시작)
        result_df = pd.concat([result_df, erp_df], ignore_index=True)
        return result_df
    else:
        # 양식 파일이 없는 경우 빈 데이터프레임 생성 후 데이터 추가
        # 필요한 빈 행 생성 (ERP_DATA_ROW_START-1개의 빈 행)
        empty_rows = cfg.ERP_DATA_ROW_START - 1
        empty_df = pd.DataFrame([[""] * len(erp_df.columns) for _ in range(empty_rows)], columns=erp_df.columns)
        result_df = pd.concat([empty_df, erp_df], ignore_index=True)
        return result_df