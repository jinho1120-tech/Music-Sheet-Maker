import gradio as gr
import subprocess
import os
from basic_pitch.inference import predict_and_save
from faster_whisper import WhisperModel
from music21 import stream, note, harmony, meter, tempo

WORK_DIR = "./temp_workspace"

# -------------------------------------------------------------
# 악보 렌더링용 HTML/JS 생성 함수
# -------------------------------------------------------------
def generate_osmd_html(xml_content):
    # 자바스크립트 템플릿 리터럴에 들어가기 전 이스케이프 처리
    xml_safe = xml_content.replace('\\', '\\\\').replace('`', '\\`')
    
    # OSMD 라이브러리를 CDN에서 불러와 MusicXML을 렌더링하는 코드
    html_code = f"""
    <div style="background-color: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
        <script src="https://cdn.jsdelivr.net/npm/opensheetmusicdisplay@1.8.8/build/opensheetmusicdisplay.min.js"></script>
        <div id="osmd-container" style="width: 100%; height: auto;"></div>
        <script>
            // Gradio 컨테이너 렌더링 지연을 대비한 타임아웃
            setTimeout(function() {{
                var osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay("osmd-container");
                osmd.setOptions({{
                    drawTitle: true,
                    drawSubtitle: false,
                    drawLyricist: false,
                    drawingParameters: "compacttight" // 리드 시트에 맞는 촘촘한 간격
                }});
                
                var xmlData = `{xml_safe}`;
                osmd.load(xmlData).then(function() {{
                    osmd.render();
                }});
            }}, 500);
        </script>
    </div>
    """
    return html_code

def process_audio(audio_filepath, progress=gr.Progress()):
    if not os.path.exists(WORK_DIR):
        os.makedirs(WORK_DIR)
        
    # ... (이전 코드의 Step 1 ~ Step 4 로직 동일하게 수행) ...
    progress(0.1, desc="음원 분리 및 텍스트/음표 추출 중...")
    
    # [Step 5] 악보 조립 (music21)
    progress(0.9, desc="리드 시트(MusicXML) 조립 중...")
    
    score = stream.Score()
    part = stream.Part()
    part.append(meter.TimeSignature('4/4'))
    
    # 더미 데이터 삽입 (실제로는 추출 데이터 매핑)
    n1 = note.Note("G4", quarterLength=1.0)
    n1.lyric = "A"
    part.append(harmony.ChordSymbol("G"))
    part.append(n1)
    
    score.append(part)
    
    # XML 파일 저장
    output_xml = os.path.join(WORK_DIR, "output_leadsheet.musicxml")
    score.write('musicxml', fp=output_xml)
    
    progress(0.95, desc="미리보기 화면 생성 중...")
    # 저장된 MusicXML 파일을 텍스트로 읽어오기
    with open(output_xml, "r", encoding="utf-8") as f:
        xml_string = f.read()
        
    # HTML 코드 생성
    preview_html = generate_osmd_html(xml_string)
    
    progress(1.0, desc="완료!")
    
    # 파일 경로와 HTML 코드를 동시에 반환
    return output_xml, preview_html

# -------------------------------------------------------------
# Gradio 웹 UI 구성
# -------------------------------------------------------------
with gr.Blocks(title="AI 리드 시트 생성기", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎼 AI 찬양 리드 시트 메이커")
    gr.Markdown("WAV 파일을 업로드하면 멜로디, 가사, 코드가 포함된 MusicXML 악보를 만들어 줍니다.")
    
    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(type="filepath", label="보컬+반주 WAV 파일 업로드")
            run_btn = gr.Button("악보 생성하기", variant="primary")
            file_output = gr.File(label="완성된 악보 다운로드 (.musicxml)")
            
        with gr.Column(scale=2):
            # 악보가 그려질 HTML 영역
            preview_output = gr.HTML(label="악보 미리보기", value="<div style='text-align:center; padding:50px; color:#999;'>여기에 악보가 미리 표시됩니다.</div>")
            
    # 실행 버튼 이벤트 연결 (출력값 2개: 파일다운로드, HTML미리보기)
    run_btn.click(
        fn=process_audio, 
        inputs=audio_input, 
        outputs=[file_output, preview_output]
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
