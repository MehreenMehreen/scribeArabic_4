import sys
sys.path.append('py3/')
sys.path.append('coords')
import test_hw_helper_routines as test_hw
import json
import os
import torch
#import matplotlib.pyplot as plt
import cv2
import sys
import pandas as pd
import numpy as np
import decode_one_image as decode
import post_process_routines as post
import points
import warp_routines as warp
from datetime import datetime, timezone
from utils import error_rates
import text_cleaning_routines as clean
import time
import argparse
import yaml
from utils.continuous_state import init_model


torch.multiprocessing.set_sharing_strategy('file_system')

HW_MODEL = None
LF = None
SOL = None

def add_meta(json_obj):

    # Get the current date and time in UTC
    now_utc = datetime.now(timezone.utc)
    # Format the date and time as a string
    formatted_date_utc = now_utc.strftime('%Y-%m-%dT%H:%M:%S')
    
    json_obj['timeStamps'] = {"created": formatted_date_utc,
                            "lastEdited": "",
                            "submitted": "",
                            "checked": ""
                          }
    
    json_obj["annotators"] =  {
                            "creator": "SFR",
                            "lastEditor": "",
                            "transcriber": "",
                            "transcription_QA": "",
                            "transcription_tagging": "",
                            "transcription_tagging_QA": "" }
    
    return json_obj

def reset_time(json_obj):
    json_obj["time"] = 0
    for line in json_obj:
        if line.startswith("line_"):
            json_obj[line]["transcribeTime"] = 0
            json_obj[line]["annotateTime"] = 0
            json_obj[line]["edited"] = "0"
    return json_obj

def get_hw(config_file, device="cuda"):
    global HW_MODEL, HW
    
    if HW_MODEL is not None:
        return HW_MODEL['HW'], HW_MODEL['idx_to_char']

    
    config = test_hw.get_config(config_file)    
    
    idx_to_char = test_hw.load_char_set(config['network']['hw']['char_set_path'])
    
    
    if 'pretraining' in config and 'hw_to_save' in config['pretraining'].keys():
        pt_file = config['pretraining']['hw_to_save']
    else:
        pt_file = 'hw.pt'
    pt_filename = os.path.join(config['snapshot_path'], pt_file)

    config["network"]["hw"]["num_of_outputs"] = len(idx_to_char) + 1
        
    print('...Using snapshot', pt_filename)    
    HW = test_hw.load_HW(config['network']['hw'], pt_filename)
    device = torch.device(device)
    HW.to(device)
    HW.eval()
    HW_MODEL = {'HW': HW, 'idx_to_char': idx_to_char}
    return HW, idx_to_char

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
    
    


# This will do bulk annotation in the whole dir            
def predict_annotations_for_directory(input_dir, config_file, annotator, model_mode="pretrain", 
                                      skip_if_json_exists=False, device="cuda"):
    print('skip_if_json_exists', skip_if_json_exists)
    files = os.listdir(input_dir)
    files.sort()
    done = 0
    for f in files:        
        if not f.lower().endswith('.jpg'):
            continue
        img_file = os.path.join(input_dir, f)
        image_arr = cv2.imread(img_file)
        #plt.imshow(image_arr)

        json_file = img_file[:-4] + '_annotate_' + annotator + '.json'
        if os.path.exists(json_file) and skip_if_json_exists:
            print('already done', json_file)
            continue
        print('doing', img_file)
        out = decode.network_output(config_file, img_file, flip=True, model_mode=model_mode, device=device)  
        out, predicted_text = decode.decode_one_img_with_info(config_file, out, flip=True, device=device) 
        
        poly_list = post.get_polygon_list_tuples(out)
        
        # Get rid of degenerate points
        to_del_ind = []
        for ind, p in enumerate(poly_list):
            if len(p) < 3:
                to_del_ind.append(ind)
            
        if len(to_del_ind) > 0:
            print('Deleting poly at index', to_del_ind)
            poly_list = [poly_list[i] for i in range(len(poly_list)) if i not in to_del_ind]
            predicted_text = [predicted_text[i] for i in range(len(predicted_text)) if i not in to_del_ind]
        
        del_list, poly_list = post.get_poly_no_overlap(img_file, poly_list, 0.7)
        
        if len(del_list) > 0:
            print('polygons deleted', len(del_list), del_list)
            print(len(poly_list))
        
        predicted_text = [predicted_text[i] for i in range(len(predicted_text)) if i not in del_list]
        poly_list = post.flip_polygon(img_file, poly_list)
        #post.draw_image_with_poly("", img_file, poly_list, convert=False)
        page_json = post.create_annotations_json(predicted_text, poly_list)
        
        with open(json_file, 'w') as fout:
            json.dump(page_json, fout)
        done += 1

    return done       


def page_htr_one_file(img_file, config_file, model_mode="pretrain", device="cuda"):
    
    # For testing
   # img = cv2.imread(img_file)
   # state = torch.load('ArabicOCR/model/trial_31_A/set0/pretrain/sol.pt')
   # state1 = torch.load('ArabicOCR/model/trial_31_A/set0/pretrain/hw.pt')
   # state2 = torch.load('ArabicOCR/model/trial_31_A/set0/pretrain/lf.pt')
   # return {}
    
    # End for testing
    
    global SOL, HW, LF
    with open(config_file) as f:
        config = yaml.load(f, Loader=yaml.Loader)    
        
    if SOL is None:
        SOL, LF, HW = init_model(config, sol_dir=model_mode, lf_dir=model_mode, hw_dir=model_mode, 
                                 device=device)
    
    image_arr = cv2.imread(img_file)
    print('read image file')
    out = decode.network_output(config_file, img_file, SOL, LF, HW, flip=True, model_mode=model_mode, device=device)  
    print('Got network output')
    out, predicted_text = decode.decode_one_img_with_info(config_file, out, flip=True, device=device) 
    print('Img decoded')
    poly_list = post.get_polygon_list_tuples(out)

    # Get rid of degenerate points
    to_del_ind = []
    for ind, p in enumerate(poly_list):
        if len(p) < 3:
            to_del_ind.append(ind)

    if len(to_del_ind) > 0:
        #print('Deleting poly at index', to_del_ind)
        poly_list = [poly_list[i] for i in range(len(poly_list)) if i not in to_del_ind]
        predicted_text = [predicted_text[i] for i in range(len(predicted_text)) if i not in to_del_ind]

        
    del_list, poly_list = post.get_poly_no_overlap(img_file, poly_list, 0.7)
    predicted_text = [predicted_text[i] for i in range(len(predicted_text)) if i not in del_list]
    predicted_text = [clean.get_clean_visual_order(txt) for txt in predicted_text]
    poly_list = post.flip_polygon(img_file, poly_list)
    #post.draw_image_with_poly("", img_file, poly_list, convert=False)
    page_json = post.create_annotations_json(predicted_text, poly_list)

    torch.cuda.empty_cache()
    return page_json

def check_tags(line_data):
    upside_down = False
    bottom_up = False
    
    if not "tags" in line_data:
        return upside_down, bottom_up
    
    # Check if its upside down or bottom up
    if line_data["tags"].get("Orient_upside_down", 0) == 1:
        upside_down = True
    if line_data["tags"].get("Orient_bottom_top", 0) == 1:
        bottom_up = True 
        
    return upside_down, bottom_up

def is_region(line_data):
    if not "tags" in line_data:
        return False
    is_region = False
    for key, flag in line_data["tags"].items():
        if key.startswith("Region_") and flag == 1:
            is_region = True
            break
    
    return is_region 

def hw_one_file(img_file, config_file, json_obj, model_mode="pretrain", line_key=None, device="cuda"):
    

    HW, idx_to_char = get_hw(config_file)

    img = cv2.imread(img_file)
    if not 'image_size' in json_obj:
        ht, width = img.shape[:2]
        json_obj['image_size'] = {'width': width, 'height': ht}
    for line, values in json_obj.items():
        if not line.startswith('line_'):
            continue
        # IF line_key is specified then modify only that line
        if line_key is not None and len(line_key) > 0 and line != line_key:
            continue
            
        # don't do regions
        if is_region(values):
            continue

        upside_down, bottom_up = check_tags(values)    
        # For debugging
        with open("temp.text", 'w') as fout:
            fout.write(f"upside_down, bottom_up = ({upside_down} + {bottom_up})")
        
        line_img = warp.get_line_image(values['coord'], img, upside_down=upside_down, top_down=not bottom_up)
        line_text = test_hw.get_predicted_str(HW, None, idx_to_char, flip=True, 
                                              img=line_img, read_image=False, device=device)
        
 
        line_text_logical_order = clean.get_clean_visual_order(line_text)
        json_obj[line]['text'] = line_text_logical_order       
        
    json_obj = sort_lines(json_obj)
    torch.cuda.empty_cache()
    return json_obj

   
        
if __name__ == "__main__":   


    parser = argparse.ArgumentParser(description="Run HTR module")
        
    parser.add_argument("--line_htr", type=int, required=True, help="If 1, do line_htr else do page_htr")
    parser.add_argument("--img_path", type=str, required=True, help="Image path")
    parser.add_argument("--config_file", type=str, required=True, help="SFR_Arabic config file")
    parser.add_argument("--original_json", type=str, required=True, help="Original JSON")
    parser.add_argument("--line_key", type=str, required=True, help="line key")
    

    args = parser.parse_args()
    json_obj = {}
    device = "cuda" if torch.cuda.is_available() else "cpu"    
    print('Using device', device)
    if args.line_htr == 1:
        json_obj = json.loads(args.original_json)
        json_obj = hw_one_file(args.img_path, args.config_file, json_obj, 
                    model_mode="pretrain", line_key=args.line_key, device=device)
    else:
        json_obj = json.loads(args.original_json)            
        json_obj = page_htr_one_file(args.img_path, args.config_file, device=device)
        
    print('BEGIN_OUT')
    print(json.dumps(json_obj))
    
# python3 arabic/page_htr.py --line_htr 0 --img_path ../../datasets/kclds/KEllis/bk_on_server/bk/KEllis2018-150a.jpg --config_file model/trial_26_A/set0/config_2600.yaml --original_json {} --line_key 0
