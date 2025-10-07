import gradio as gr
import sys
import json
import gradio as gr
from PIL import Image, ImageDraw
import os
import io

sys.path.append('arabic')
sys.path.append('coord')
import page_htr

TEMP_DIR = "temp/"

os.environ["GRADIO_TEMP_DIR"] = TEMP_DIR


img_file = "../../datasets/MoiseK/datasets_sfr/pretrain_images/MG1_045_01.JPG"
config_file = "model/trial_31_A/set0/config_3100.yaml"



def annotate_image(image, page_json):
    text = []
    for line_key, line_obj in page_json.items():
        if not line_key.startswith('line_'):
            continue
        if not 'coord' in line_obj:
            continue
        text += [line_obj['text']]
        poly = line_obj['coord']
        poly = [(x, y) for x,y in zip(poly[::2], poly[1::2])]
        draw = ImageDraw.Draw(image)
        draw.polygon(poly, fill=None, outline="red", width=2)
        
    return image, '\n'.join(text)

def save_text(text, image_file):
    filename = os.path.splitext(os.path.split(image_file)[1])[0]
    filename += '.txt'
    return gr.File.update(value=text.encode('utf-8'), file_name=filename)

def get_text_file():
    download_file = gr.DownloadButton(label=f"Download text", visible=False)    
    return download_file


def process_textfile(image_path, text):
    directory, filename = os.path.split(image_path)
    image_id, image_ext = os.path.splitext(filename)
    filename = image_id + '.txt'
    filepath = os.path.join(directory, filename)
    content = text if text else ""
    
    with open(filepath, 'w') as fout:
        fout.write(content)
    return filepath, filename

def show_image(image_path):
    if image_path is None:
        return gr.Image(type="pil", label="Image"), ' ', gr.DownloadButton("Download text", visible=False), gr.File(label="Upload JPG Image", file_types=[".jpg"])
    
    page_json = page_htr.page_htr_one_file(image_path, config_file, device="cpu")
    
    image, text = annotate_image(Image.open(image_path), page_json)
    filepath, text_filename = process_textfile(image_path, text)
    
    download_button = gr.DownloadButton(label=f"Download {text_filename}", value=filepath, visible=True)
       
    upload_image = gr.File(label="Upload JPG Image", file_types=[".jpg"])    
        
    return image, text, download_button, upload_image

if not os.path.exists(TEMP_DIR):
    os.mkdir(TEMP_DIR)

 

with gr.Blocks() as demo:
    gr.HTML("<h2 style='color: red;'>📜🖋️ Arabic handwriting reader powered by Muharaf 📝</h2>")
    gr.HTML("<h3 style='color: black;'>This is a demo app. Due to limited resources, upload a page image with 8 or less lines of text. Check out the sample_images directory.</h3>")
    gr.HTML('<a href="https://github.com/MehreenMehreen/start_follow_read_arabic" style="color: blue; text-decoration: underline;">Visit our GitHub page</a>')
    with gr.Row():
        
        image_text = gr.Textbox(label="Text from HTR Model", lines=15)    
        image_output = gr.Image(type="pil", label="Image")
        
    with gr.Row():
        upload_image = gr.File(label="Upload JPG Image", file_types=[".jpg"])
        
        #download_btn = gr.Button("Download Text")
        download_file = gr.DownloadButton("Download text", visible=False)
        
        

    upload_image.change(fn=show_image, inputs=upload_image, outputs=[image_output, image_text, download_file, upload_image])
    

demo.launch()
