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
from pyexcel_xls import save_data
from collections import OrderedDict


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


def process_rental_company_with_voucher(uploaded_file_path, voucher_number, employee_number):
    """
    특정 렌탈사의 데이터 처리 (웹 인터페이스용)
    
    Args:
        uploaded_file_path: 업로드된 파일 경로
        voucher_number: 전표번호
        employee_number: 사원번호 (필수)
        
    Returns:
        출력 파일 경로
    """
    # 사원번호 필수 검증
    if not employee_number or not employee_number.strip():
        raise ValueError("사원번호를 입력해주세요. 사원번호는 필수 입력값입니다.")
    
    company_name = "한국렌탈"
    company_config = cfg.RENTAL_COMPANIES[company_name].copy()  # 설정을 복사해서 사용
    
    # 사원번호 설정 - 입력된 값 사용
    company_config['id_write'] = employee_number.strip()
    
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
    output_filename = f"자동전표_완성파일_{datetime.now().strftime('%Y%m%d')}.xls"
    output_path = os.path.join(cfg.OUTPUT_DIR, output_filename)

    os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

    try:
        # pyexcel_xls와 OrderedDict 모듈 임포트
        from pyexcel_xls import save_data
        from collections import OrderedDict
        
        # 데이터프레임을 리스트로 변환
        headers = result_df.columns.tolist()
        data = [headers]  # 헤더를 첫 번째 행으로 추가
        
        # 데이터프레임의 각 행을 리스트로 변환하여 data에 추가
        for _, row in result_df.iterrows():
            data.append(row.tolist())
        
        # OrderedDict 생성 (Sheet1이라는 이름의 시트에 데이터 저장)
        data_dict = OrderedDict()
        data_dict["Sheet1"] = data
        
        # xls 파일로 저장
        save_data(output_path, data_dict)
        
        print(f"Excel 97-2003 형식(.xls)으로 파일 저장 완료: {output_path}")
    except Exception as e:
        print(f"Excel 97-2003 형식 저장 중 오류 발생: {e}")
        # 오류 발생 시 기존 방식으로 저장
        backup_path = output_path.replace('.xls', '.xlsx')
        result_df.to_excel(backup_path, index=False, engine='openpyxl')
        output_path = backup_path
        print(f"대체 형식(.xlsx)으로 파일 저장 완료: {output_path}")

    return output_path


def main():
    """
    메인 실행 함수 (CLI 실행)
    """
    parser = argparse.ArgumentParser(description='ERP 자동 전표 생성 프로그램')
    parser.add_argument('-c', '--company', type=str, help='처리할 렌탈사 이름')
    parser.add_argument('-a', '--all', action='store_true', help='모든 렌탈사 처리')
    parser.add_argument('-e', '--employee', type=str, default='00616', help='사원번호 (기본값: 00616)')
    
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