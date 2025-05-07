"""
Excel 파일 처리 유틸리티
"""
import os
import pandas as pd
from typing import Dict, Any
from core import config as cfg
from pyexcel_xls import save_data
from collections import OrderedDict

def save_to_csv(df: pd.DataFrame, output_path: str, data_count: int = 0) -> bool:
    try:
        df.to_csv(output_path, index=False, encoding=cfg.CSV_OUTPUT_ENCODING)
        print(f"처리 완료: {data_count}개 행이 '{output_path}'에 저장됨 ({cfg.CSV_OUTPUT_ENCODING} 인코딩)")
        print(f"데이터는 {cfg.ERP_DATA_ROW_START}행부터 시작합니다.")
        return True
    except Exception as e:
        print(f"CSV 파일 저장 중 오류 발생: {e}")
        return False

def save_to_excel(df: pd.DataFrame, output_path: str, data_count: int = 0) -> bool:
    try:
        # Excel 97-2003 형식(.xls)으로 저장
        xls_path = output_path.replace('.xlsx', '.xls')
        
        # 데이터프레임을 리스트로 변환
        headers = df.columns.tolist()
        data = [headers]  # 헤더를 첫 번째 행으로 추가
        
        # 데이터프레임의 각 행을 리스트로 변환하여 data에 추가
        for _, row in df.iterrows():
            data.append(row.tolist())
        
        # OrderedDict 생성 (Sheet1이라는 이름의 시트에 데이터 저장)
        data_dict = OrderedDict()
        data_dict["Sheet1"] = data
        
        # xls 파일로 저장
        save_data(xls_path, data_dict)
        
        print(f"처리 완료: {data_count}개 행이 '{xls_path}'에 저장됨")
        print(f"엑셀 파일이 성공적으로 생성되었습니다: {os.path.abspath(xls_path)}")
        return True
    except Exception as e:
        print(f"엑셀 파일 저장 중 오류 발생: {e}")
        
        # 대체 저장 시도 (일반 Excel 형식)
        try:
            backup_path = output_path
            df.to_excel(backup_path, index=False, engine='openpyxl')
            print(f"대체 형식(.xlsx)으로 파일 저장 완료: {backup_path}")
            return True
        except Exception as ex:
            print(f"대체 저장도 실패: {ex}")
            return False

def save_to_files(result_df: pd.DataFrame, output_csv: str, output_excel: str, erp_data_count: int) -> None:
    # CSV 파일 저장
    print(f"'{output_csv}'로 CSV 저장 중...")
    csv_saved = save_to_csv(result_df, output_csv, erp_data_count)
    
    # Excel 파일 저장
    print(f"\n'{output_excel}'로 엑셀 파일 저장 중...")
    excel_saved = save_to_excel(result_df, output_excel, erp_data_count)
    
    if csv_saved and not excel_saved:
        print("CSV 파일은 정상적으로 저장되었습니다.")
        print("CSV 파일을 열 때는 Excel의 '데이터' 탭에서 '텍스트/CSV에서' 기능을 사용하시기 바랍니다.")