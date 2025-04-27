import gradio as gr
import main  # 기존 전처리 함수들을 main.py에서 가져온다고 가정할게
import os
import pandas as pd

def process_file(file, voucher_number):
    if file is None:
        return None
    
    # 업로드된 파일 저장
    input_path = f"temp_upload/{file.name}"
    os.makedirs("temp_upload", exist_ok=True)
    file.save(input_path)

    # 파일 확장자 확인
    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".xlsx":
        # 엑셀 파일 읽어서 CSV로 변환
        df = pd.read_excel(input_path)
        csv_path = input_path.replace(".xlsx", ".csv")
        df.to_csv(csv_path, index=False)
        input_path = csv_path

    # 메인 전처리 함수 호출 (수정 예정)
    output_path = main.process_rental_company_with_voucher(input_path, voucher_number)

    return output_path

# Gradio 인터페이스 구성
with gr.Blocks() as demo:
    gr.Markdown("# ERP 자동 전표 변환기\nCSV 또는 엑셀 파일을 업로드하고 전표번호를 입력하세요.")

    with gr.Row():
        file_input = gr.File(label="렌탈료 파일 업로드 (CSV 또는 Excel)", file_types=[".csv", ".xlsx"])
        voucher_input = gr.Textbox(label="전표번호 입력", placeholder="예: 20250427001")

    with gr.Row():
        submit_btn = gr.Button("제출")
        clear_btn = gr.Button("지우기")

    output_file = gr.File(label="전처리 완료 파일 다운로드")

    submit_btn.click(
        process_file,
        inputs=[file_input, voucher_input],
        outputs=output_file
    )

    clear_btn.click(
        lambda: (None, ""),
        inputs=[],
        outputs=[file_input, voucher_input]
    )

demo.launch()
