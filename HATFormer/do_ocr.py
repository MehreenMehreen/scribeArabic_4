import sys
#sys.path.append('src/')
sys.path.append('ArabicOCR/arabic')
sys.path.append('ArabicOCR/coords')
sys.path.append('../ArabicOCR/arabic')
sys.path.append('../ArabicOCR/coords')
import pandas as pd
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel, PreTrainedTokenizerFast, logging
import numpy as np
from PIL import Image
import cv2
import json
import argparse
import warp_routines as warp 
import text_cleaning_routines as clean
import points
import os

MODEL, TOKENIZER, PROCESSOR= (None, None, None)



torch.multiprocessing.set_sharing_strategy('file_system')

# Can pass PIL image for inference....if not none, image_path would be ignored
# If None, img would be read from image_path
def create_visual_tokens(image_path, img, processor):

    to_close = False
    if img is None:
        to_close = True
        img = Image.open(image_path).convert("RGB")

 
    # Get original dimensions
    original_width, original_height = img.size

    # Calculate new dimensions
    new_height = 64
    aspect_ratio = original_width / original_height
    new_width = int(new_height * aspect_ratio)

    # Resize the image
    resized_img = img.resize((new_width, new_height))
    resized_img_original = resized_img.copy()

    flipped_img = resized_img_original.transpose(Image.FLIP_LEFT_RIGHT)

    resized_img = flipped_img

    # Create a new image with black background (384x384)
    final_width, final_height = 384, 384
    new_img = Image.new("RGB", (final_width, final_height), (0,0,0))

    # Check if resizing was needed
    if resized_img.width <= final_width:
        # If the image width is less than or equal to 384, just paste it at the top-left
        new_img.paste(resized_img, (0, 0))
    else:
        # Otherwise, split the image into segments of 384 width
        segment_width = final_width
        num_segments = (resized_img.width + segment_width - 1) // segment_width  # ceil division

        # Paste each segment into the new image
        for i in range(num_segments):
            left = i * segment_width
            right = min(left + segment_width, resized_img.width)
            segment = resized_img.crop((left, 0, right, new_height))
            new_img.paste(segment, (0, i * new_height))

    pixel_values = processor(new_img, return_tensors="pt").pixel_values[0]
    if to_close:
        img.close()
    return pixel_values

# if img is not none, img_path would be ignored
# If img is None, img would be read from image_path
@torch.no_grad()
def predict_for_image(img_path, img, model, tokenizer, processor, max_new_tokens=450):

    
    model.half().cuda().eval()

    pixel_values = create_visual_tokens(img_path, img, processor).unsqueeze(0)


    
        
    output = model.generate(pixel_values.half().cuda(),
                            num_beams=3,
                            length_penalty = 0,
                            max_new_tokens=max_new_tokens)


    pred_str = tokenizer.batch_decode(output.tolist(), skip_special_tokens=True)        

    return pred_str[0]

    
def get_model_specs(model_path):
    logging.set_verbosity_error() 
    model = VisionEncoderDecoderModel.from_pretrained(model_path)
    directory, _ = os.path.split(model_path)
    tokenizer_file = os.path.join(directory, "arabic_tokenizer_clean/tokenizer.json")
    tokenizer = PreTrainedTokenizerFast(tokenizer_file=tokenizer_file)
    tokenizer.add_special_tokens({
        'pad_token': '<pad>',
        'eos_token': '</s>',
        'cls_token': '<s>',
        'bos_token': '<s>',
    })
    #processor = TrOCRProcessor.from_pretrained('./trocr/')
    #processor.save_pretrained(model_path)c
    processor = TrOCRProcessor.from_pretrained(model_path)
    

    return model, tokenizer, processor


def hw_one_file(img_file, json_obj, model_path, line_key='', max_new_tokens=450, do_sort=True):
    global MODEL, TOKENIZER, PROCESSOR
    
    if MODEL is None:
        MODEL, TOKENIZER, PROCESSOR = get_model_specs(model_path)
    
    img = cv2.imread(img_file)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    
    for line, values in json_obj.items():
        if not line.startswith('line_'):
            continue
        # IF line_key is specified then modify only that line
        if line_key is not None and len(line_key) > 0. and line != line_key:
            continue

        
        line_img = warp.get_line_image(values['coord'], img)
        
        pil_img = Image.fromarray(line_img)
        
        line_text = predict_for_image(None, pil_img, MODEL, TOKENIZER, PROCESSOR, max_new_tokens=max_new_tokens)
        
        
        #print('line_text', line_text)
        line_text_logical_order = clean.get_clean_visual_order(line_text)
        #print('line_text_logical_order', line_text_logical_order)
        json_obj[line]['text'] = line_text_logical_order       

    if do_sort:
        json_obj = sort_lines(json_obj)
    torch.cuda.empty_cache()
    return json_obj    

def sort_lines(json_obj, copy_lines_with_text_only=False):
    top_left = []
    keys = []
    for k, v in json_obj.items():
        if k.startswith('line_'):
            keys.append(k)
            poly = np.array(points.list_to_xy(v['coord']))
            top_left.append([np.max(poly, 0)[0], np.min(poly, 0)[1]])
    sorted_indices = sorted(range(len(top_left)), 
                            key=lambda i: (top_left[i][1], -top_left[i][0]))
    
    sorted_json = dict()
    # Copy all non-line keys
    for k, v in json_obj.items():
        if not k.startswith('line_'):
            sorted_json[k] = v
    # Copy all lines 
    for i, ind in enumerate(sorted_indices):
        if copy_lines_with_text_only and len(json_obj[keys[ind]]['text']) == 0:
            continue
        sorted_json[f'line_{i + 1}'] = json_obj[keys[ind]]
    
    return sorted_json



if __name__ == "__main__":   

    parser = argparse.ArgumentParser(description="Run HATFormer")
    parser.add_argument("--img_path", type=str, required=True, help="Image path")
    parser.add_argument("--model_path", type=str, help="HAT Former model path", default='trial_31_A_set0/')
    parser.add_argument("--original_json", type=str, required=True, help="Original JSON")
    parser.add_argument("--line_key", type=str, required=True, help="line key")    
    parser.add_argument("--sort_lines", type=int, help="Sort lines on basis of baselines", default=1) 
    
    args = parser.parse_args()
    json_obj = {}
    json_obj = json.loads(args.original_json)
    do_sort = args.sort_lines == 1
    max_text_length = 450
    json_obj = hw_one_file(args.img_path, json_obj, args.model_path, line_key=args.line_key, do_sort=do_sort)    
    
    print('BEGIN_OUT')
    print(json.dumps(json_obj))    