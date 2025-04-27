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
    특정 렌탈사의 데이터 처리 (CLI 실행용)
    
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


def process_rental_company_with_voucher(uploaded_file_path, voucher_number):
    company_name = "한국렌탈"
    company_config = cfg.RENTAL_COMPANIES[company_name]

    mapping_file = company_config['mapping_file']
    mapping_dict = mapping_utils.load_mapping_file(mapping_file)

    df, df_filtered = data_processor.load_and_preprocess_data(uploaded_file_path, company_config, mapping_dict)
    summary = data_processor.summarize_data(df_filtered, mapping_dict)
    erp_df = erp_generator.generate_erp_data(df_filtered, company_config)
    erp_df = erp_generator.prepare_erp_columns(erp_df)
    erp_df = erp_generator.set_management_items(erp_df, df_filtered, company_config)

    # 전표번호 채워넣기
    if 'ROW_ID' in erp_df.columns:
        erp_df['ROW_ID'] = voucher_number
    if 'NO_DOCU' in erp_df.columns:
        erp_df['NO_DOCU'] = voucher_number

    # ERP 양식 로드
    erp_form = file_handler.load_erp_form_template(company_config['erp_form_file'])

    # ERP 양식에 맞춰서 데이터 준비
    result_df = file_handler.prepare_file_with_template(erp_df, erp_form)

    # 저장
    output_filename = f"자동전표_완성파일_{datetime.now().strftime('%Y%m%d')}.xlsx"
    output_path = os.path.join(cfg.OUTPUT_DIR, output_filename)

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    # 이제 준비된 result_df를 저장
    result_df.to_excel(output_path, index=False, engine='openpyxl')

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
