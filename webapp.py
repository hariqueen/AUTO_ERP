import gradio as gr
from main import process_uploaded_file

def run_preprocessing(uploaded_file):
    output_csv_path = process_uploaded_file(uploaded_file)
    return output_csv_path

iface = gr.Interface(
    fn=run_preprocessing,
    inputs=gr.File(label="렌탈료 파일 업로드 (CSV)"),
    outputs=gr.File(label="전처리 완료 파일 다운로드"),
    title="ERP 자동 전표 변환기",
    description="CSV 파일을 업로드하면 자동으로 ERP 업로드용 파일로 변환해줍니다."
)

if __name__ == "__main__":
    iface.launch()
