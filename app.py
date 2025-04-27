import gradio as gr
import main  # main.py에 작성된 전처리 로직 호출
import os
import pandas as pd

def process_file(file_path, voucher_number):
    if file_path is None:
        return None

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

    # 메인 전처리 함수 호출 (전표번호 넘겨주기)
    output_path = main.process_rental_company_with_voucher(input_path, voucher_number)

    return output_path

# Gradio 인터페이스 구성
with gr.Blocks() as demo:
    gr.Markdown("# ERP 자동 전표 변환기\n\n업로드할 파일과 전표번호를 입력하세요.")

    with gr.Row():
        file_input = gr.File(
            label="렌탈료 파일 업로드 (CSV 또는 Excel)",
            file_types=[".csv", ".xlsx"],
            type="filepath"   # ⭐ 여기가 중요!
        )
        voucher_input = gr.Textbox(
            label="전표번호 입력",
            placeholder="예: 20250427001"
        )

    with gr.Row():
        submit_btn = gr.Button("제출")
        clear_btn = gr.Button("지우기")

    output_file = gr.File(label="전처리 완료 파일 다운로드")

    # 버튼 클릭 이벤트 연결
    submit_btn.click(
        fn=process_file,
        inputs=[file_input, voucher_input],
        outputs=output_file
    )

    clear_btn.click(
        fn=lambda: (None, ""),
        inputs=[],
        outputs=[file_input, voucher_input]
    )

demo.launch()
