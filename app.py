import gradio as gr
import main  # main.py에 작성된 전처리 로직 호출
import os
import pandas as pd
import traceback
import sys
import re
from io import StringIO

def process_file(file_path, voucher_number, employee_number):
    # 상태 메시지와 결과를 함께 반환하기 위한 변수 초기화
    status_message = ""
    output_file_path = None
    
    # 로그를 캡처하기 위한 StringIO 객체
    log_capture = StringIO()
    
    # 입력값 검증
    if file_path is None:
        return None, "파일을 업로드해주세요."
    
    if not voucher_number or not voucher_number.strip():
        return None, "전표번호를 입력해주세요."
        
    if not employee_number or not employee_number.strip():
        return None, "사원번호를 입력해주세요. 사원번호는 필수 입력값입니다."

    try:
        # 표준 출력을 캡처
        original_stdout = sys.stdout
        sys.stdout = log_capture
        
        # 파일 확장자 확인
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".xlsx":
            # 엑셀 파일을 CSV로 변환
            df = pd.read_excel(file_path)
            csv_path = file_path.replace(".xlsx", ".csv")
            df.to_csv(csv_path, index=False)
            input_path = csv_path
        else:
            # 이미 CSV 파일이면 그대로 사용
            input_path = file_path

        # 메인 전처리 함수 호출 (전표번호와 사원번호 넘겨주기)
        output_path = main.process_rental_company_with_voucher(input_path, voucher_number, employee_number)
        output_file_path = output_path
        
        # 성공 메시지 작성
        status_message = "✅ 파일 변환 성공! 위 버튼을 클릭하여 다운로드하세요."
        
    except Exception as e:
        # 오류 발생 시 간단한 오류 메시지
        status_message = f"❌ 오류 발생: {str(e)}"
    
    finally:
        # 캡처된 로그 가져오기
        log_output = log_capture.getvalue()
        sys.stdout = original_stdout  # 원래 표준 출력으로 복구
        
        # 주요 정보 추출 (오류 발생 여부와 상관없이)
        important_info = []
        
        # 금액 필드 정보 추출
        amount_field_match = re.search(r"사용할 금액 필드: '([^']*)'", log_output)
        if amount_field_match:
            important_info.append(f"사용할 금액 필드: '{amount_field_match.group(1)}'")
        
        # 팀 필드 정보 추출
        team_field_match = re.search(r"팀 필드로 '([^']*)'를 자동 인식했습니다", log_output)
        if team_field_match:
            important_info.append(f"팀 필드로 '{team_field_match.group(1)}'를 자동 인식했습니다.")
        
        # 제외된 항목 정보 추출
        excluded_rows_match = re.search(r"금액이 없는 행\(반납 항목\) (\d+)개를 제외합니다", log_output)
        if excluded_rows_match:
            important_info.append(f"금액이 없는 행(반납 항목) {excluded_rows_match.group(1)}개를 제외합니다.")
        
        # 금액 정보 추출
        amt_info = []
        debit_sum_match = re.search(r"차변 금액 합계: (\d+)", log_output)
        credit_sum_match = re.search(r"대변 금액: (\d+)", log_output)
        debit_count_match = re.search(r"차변 건수: (\d+)", log_output)
        credit_count_match = re.search(r"대변 건수: (\d+)", log_output)
        
        if debit_sum_match:
            amt_info.append(f"차변 금액 합계: {int(debit_sum_match.group(1)):,}")
        if credit_sum_match:
            amt_info.append(f"대변 금액: {int(credit_sum_match.group(1)):,}")
        if debit_count_match:
            amt_info.append(f"차변 건수: {debit_count_match.group(1)}")
        if credit_count_match:
            amt_info.append(f"대변 건수: {credit_count_match.group(1)}")
        
        if amt_info:
            important_info.append("AMT 필드 확인:")
            important_info.extend(amt_info)
        
        # 매핑 오류 정보 추출 (오류가 있을 경우에만)
        if not output_file_path and "매핑되지 않은 팀명" in log_output:  # 오류 발생 시에만 매핑 정보 표시
            unmapped_section = re.search(r"매핑되지 않은 팀명 (\d+)개:(.*?)(?=\n\n|\Z)", log_output, re.DOTALL)
            if unmapped_section:
                unmapped_count = unmapped_section.group(1)
                unmapped_teams = re.findall(r"- '([^']*)'", unmapped_section.group(2))
                important_info.append(f"매핑되지 않은 팀명 {unmapped_count}개:")
                for team in unmapped_teams:
                    important_info.append(f"- '{team}'")
        
        # 주요 정보를 상태 메시지에 추가 (항상)
        if important_info:
            status_message += "\n\n" + "\n".join(important_info)
    
    return output_file_path, status_message

# Gradio 인터페이스 구성
with gr.Blocks() as demo:
    gr.Markdown("# ERP 자동 전표 변환기\n\n업로드할 파일과 전표번호, 사원번호를 입력하세요.")

    with gr.Row():
        file_input = gr.File(
            label="렌탈료 파일 업로드 (CSV 또는 Excel)",
            file_types=[".csv", ".xlsx"],
            type="filepath"
        )
        
    with gr.Row():
        voucher_input = gr.Textbox(
            label="전표번호 입력 (필수)",
            placeholder="예: 20250427001"
        )
        
        employee_input = gr.Textbox(
            label="사원번호 입력 (필수)",
            placeholder="예: 00616"
        )

    with gr.Row():
        submit_btn = gr.Button("제출", variant="primary")
        clear_btn = gr.Button("지우기")
    
    output_file = gr.File(label="전처리 완료 파일 다운로드")
    
    # 상태 메시지를 파일 다운로드 영역 아래로 이동
    status_output = gr.Textbox(
        label="처리 상태",
        placeholder="파일을 제출하면 처리 상태가 여기에 표시됩니다.",
        lines=10
    )

    # 버튼 클릭 이벤트 연결
    submit_btn.click(
        fn=process_file,
        inputs=[file_input, voucher_input, employee_input],
        outputs=[output_file, status_output]
    )

    clear_btn.click(
        fn=lambda: (None, "", "", ""),
        inputs=[],
        outputs=[file_input, voucher_input, employee_input, status_output]
    )

# 시작 메시지 표시
print("ERP 자동 전표 변환기가 시작되었습니다.")
demo.launch()