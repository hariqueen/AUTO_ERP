from typing import Dict, Any
import pandas as pd


def print_data_summary(summary: Dict[str, Any], company_config: Dict[str, Any]) -> None:
    """
    데이터 처리 결과 요약 출력
    
    Args:
        summary: 데이터 요약 정보
        company_config: 렌탈사 설정 정보
        
    Returns:
        None
    """
    total_count = summary['total_count']
    total_amount = summary['total_amount']
    account_counts = summary['account_counts']
    mapping_summary = summary['mapping_summary']
    
    print(f"\n총 처리 건수: {total_count + 1}건 (차변 {total_count}건, 대변 1건)")
    print(f"총 금액: {total_amount:,.0f}원")
    print(f"차변 계정: {len(account_counts)}개 계정 사용")
    print(f"대변 계정: {company_config['payable_acct']} (미지급금) 1개 계정 사용")
    
    # 관리항목 설정 내용 출력
    print("\n관리항목 설정 정보:")
    print(f"- CD_CC (코스트센터): {company_config['cost_center']} (고정)")
    print(f"- CD_PARTNER (거래처코드): {company_config['partner_code']} (고정)")
    print(f"- CD_PJT (프로젝트코드): 각 팀별 매핑된 코드 사용")
    
    # 매핑 정보 요약
    print("\n매핑 성공 팀명:")
    mapped_teams = mapping_summary['mapped_teams']
    for idx, team in enumerate(mapped_teams[:10]):
        if len(mapped_teams) > 10 and idx == 9:
            print(f"- {team['original']} ... 외 {len(mapped_teams)-10}개")
        else:
            print(f"- {team['original']} -> {team['mapped']} (ACCT: {team['acct']}, PJT: {team['pjt']})")


def generate_report_file(summary: Dict[str, Any], erp_df: pd.DataFrame, report_file: str) -> None:
    """
    처리 결과 보고서 파일 생성
    
    Args:
        summary: 데이터 요약 정보
        erp_df: ERP 데이터프레임
        report_file: 보고서 파일 경로
        
    Returns:
        None
    """
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# ERP 전표 생성 결과 보고서\n\n")
        
        # 기본 정보
        f.write("## 1. 기본 정보\n")
        f.write(f"- 생성 일시: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- 처리 건수: 차변 {summary['total_count']}건, 대변 1건\n")
        f.write(f"- 총 금액: {summary['total_amount']:,.0f}원\n\n")
        
        # 계정 분포
        f.write("## 2. 계정 코드별 사용 현황\n")
        for acct, count in summary['account_counts'].items():
            f.write(f"- {acct}: {count}건\n")
        f.write("\n")
        
        # 팀별 분포
        f.write("## 3. 팀별 매핑 정보\n")
        for team in summary['mapping_summary']['mapped_teams']:
            f.write(f"- {team['original']} -> {team['mapped']} (계정: {team['acct']}, 프로젝트: {team['pjt']})\n")
        
        f.write("\n## 4. 전표 주요 정보\n")
        # 차변 행 정보
        debit_rows = erp_df[erp_df["TP_DRCR"] == "1"]
        f.write(f"- 차변 건수: {len(debit_rows)}건\n")
        f.write(f"- 차변 계정: {len(debit_rows['CD_ACCT'].unique())}개 계정 사용\n")
        
        # 대변 행 정보
        credit_rows = erp_df[erp_df["TP_DRCR"] == "2"]
        f.write(f"- 대변 건수: {len(credit_rows)}건\n")
        f.write(f"- 대변 계정: {credit_rows['CD_ACCT'].iloc[0]} (미지급금)\n")
        
        # 전표 번호 정보
        f.write(f"- 전표 번호: {erp_df['NO_DOCU'].iloc[0]}\n")
        
    print(f"\n처리 결과 보고서가 '{report_file}'에 저장되었습니다.")