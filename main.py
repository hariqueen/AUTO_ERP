"""
ERP 자동 전표 생성 메인 실행 파일
"""
import os
import argparse
from datetime import datetime
import config as cfg
import mapping_utils
import data_processor
import erp_generator
import file_handler
import reporter
import pandas as pd


def process_rental_company(company_name: str):
    """
    특정 렌탈사의 데이터 처리 (기존 CLI 실행용)
    
    Args:
        company_name: 처리할 렌탈사 이름
    """
    if company_name not in cfg.RENTAL_COMPANIES:
        print(f"오류: '{company_name}' 렌탈사 설정을 찾을 수 없습니다.")
        return
    
    company_config = cfg.RENTAL_COMPANIES[company_name]
    print(f"'{company_name}' 렌탈사 데이터 처리 시작...")
    
    input_file = company_config['input_file']
    mapping_file = company_config['mapping_file']
    erp_form_file = company_config['erp_form_file']
    output_csv = company_config['output_csv']
    output_excel = company_config['output_excel']
    report_file = os.path.join(cfg.OUTPUT_DIR, f'보고서_{company_name}_{datetime.now().strftime("%Y%m%d")}.txt')
    
    mapping_dict = mapping_utils.load_mapping_file(mapping_file)
    df, df_filtered = data_processor.load_and_preprocess_data(input_file, company_config, mapping_dict)
    summary = data_processor.summarize_data(df_filtered, mapping_dict)
    erp_df = erp_generator.generate_erp_data(df_filtered, company_config)
    erp_df = erp_generator.prepare_erp_columns(erp_df)
    erp_df = erp_generator.set_management_items(erp_df, df_filtered, company_config)
    
    erp_form = file_handler.load_erp_form_template(erp_form_file)
    result_df = file_handler.prepare_file_with_template(erp_df, erp_form)
    
    file_handler.save_to_files(result_df, output_csv, output_excel, len(erp_df))
    reporter.print_data_summary(summary, company_config)
    # reporter.generate_report_file(summary, erp_df, report_file)
    
    print(f"\n'{company_name}' 렌탈사 데이터 처리 완료.")


def process_uploaded_file(file_obj):
    """
    사용자가 업로드한 파일 직접 처리 (Gradio용)
    
    Args:
        file_obj: 업로드된 파일 객체
    Returns:
        생성된 CSV 파일 경로
    """
    company_config = cfg.RENTAL_COMPANIES['한국렌탈']
    mapping_dict = mapping_utils.load_mapping_file(company_config['mapping_file'])
    
    # 직접 file_obj를 Pandas로 읽어옴
    df, df_filtered = data_processor.load_and_preprocess_data(file_obj, company_config, mapping_dict)
    summary = data_processor.summarize_data(df_filtered, mapping_dict)
    erp_df = erp_generator.generate_erp_data(df_filtered, company_config)
    erp_df = erp_generator.prepare_erp_columns(erp_df)
    erp_df = erp_generator.set_management_items(erp_df, df_filtered, company_config)
    
    erp_form = file_handler.load_erp_form_template(company_config['erp_form_file'])
    result_df = file_handler.prepare_file_with_template(erp_df, erp_form)
    
    # output 경로 세팅
    output_csv = os.path.join(cfg.OUTPUT_DIR, f'자동전표_업로드파일_{cfg.CURRENT_DATE}.csv')
    output_excel = os.path.join(cfg.OUTPUT_DIR, f'자동전표_업로드파일_{cfg.CURRENT_DATE}.xlsx')
    report_file = os.path.join(cfg.OUTPUT_DIR, f'보고서_업로드파일_{cfg.CURRENT_DATE}.txt')
    
    file_handler.save_to_files(result_df, output_csv, output_excel, len(erp_df))
    reporter.generate_report_file(summary, erp_df, report_file)

    return output_csv

def process_rental_company_with_voucher(uploaded_file_path, voucher_number):
    """
    사용자가 업로드한 파일과 전표번호를 받아 ERP 자동 전표파일을 생성하는 함수

    Args:
        uploaded_file_path (str): 업로드된 파일 경로 (CSV 변환된 경로)
        voucher_number (str): 사용자 입력 전표번호

    Returns:
        output_path (str): 최종 저장된 파일 경로 (xlsx)
    """
    # 한국렌탈 기준으로 설정 (혹시 다르면 추후 확장 가능)
    company_name = "한국렌탈"
    company_config = cfg.RENTAL_COMPANIES[company_name]

    # 매핑 정보 로드
    mapping_file = company_config['mapping_file']
    mapping_dict = mapping_utils.load_mapping_file(mapping_file)

    # 데이터 로드 및 전처리
    df, df_filtered = data_processor.load_and_preprocess_data(uploaded_file_path, company_config, mapping_dict)

    # 데이터 요약 생성
    summary = data_processor.summarize_data(df_filtered, mapping_dict)

    # ERP 데이터 생성
    erp_df = erp_generator.generate_erp_data(df_filtered, company_config)

    # ERP 표준 컬럼 구조로 준비
    erp_df = erp_generator.prepare_erp_columns(erp_df)

    # 관리항목 설정
    erp_df = erp_generator.set_management_items(erp_df, df_filtered, company_config)

    # **여기서 전표번호 채워넣기**
    if 'ROW_ID' in erp_df.columns:
        erp_df['ROW_ID'] = voucher_number
    if 'NO_DOCU' in erp_df.columns:
        erp_df['NO_DOCU'] = voucher_number

    # 저장 경로 설정
    output_filename = f"자동전표_완성파일_{datetime.now().strftime('%Y%m%d')}.xlsx"
    output_path = os.path.join(cfg.OUTPUT_DIR, output_filename)

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    # 엑셀로 저장
    erp_df.to_excel(output_path, index=False)

    return output_path


def main():
    """
    메인 실행 함수 (CLI 실행)
    """
    parser = argparse.ArgumentParser(description='ERP 자동 전표 생성 프로그램')
    parser.add_argument('-c', '--company', type=str, help='처리할 렌탈사 이름')
    parser.add_argument('-a', '--all', action='store_true', help='모든 렌탈사 처리')
    
    args = parser.parse_args()
    
    if args.all:
        for company_name in cfg.RENTAL_COMPANIES.keys():
            process_rental_company(company_name)
            print('-' * 80)
    elif args.company:
        process_rental_company(args.company)
    else:
        process_rental_company('한국렌탈')


if __name__ == "__main__":
    main()
