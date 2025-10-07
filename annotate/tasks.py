from celery import shared_task, Task

import torch
from django.conf import settings
from celery.result import AsyncResult
import sys
import os
import yaml
from . import tag_views


        
    

def get_config(key=None):
    config_file = os.path.join(settings.DATASET_ROOT, settings.CONFIG_FILE)
    if not os.path.exists(config_file):
        return {}
    with open(config_file) as fin:
        config = yaml.safe_load(fin)
        
    return config
    


@shared_task
def line_HTR(img_file, original_json, selected_line_index, sfr_path, json_file):

    sys.path.append(os.path.join(sfr_path, 'py3/'))
    sys.path.append(os.path.join(sfr_path, 'coords/'))
    sys.path.append(os.path.join(sfr_path, 'arabic/'))
    
    import page_htr
    import copy
    temp_json = copy.deepcopy(original_json)
    
    config = get_config()
    if 'HTR' in config:
        config_file = config['HTR']['config_file']
    else:
        return original_json
    
    line_key = None
    if f'line_{selected_line_index+1}' in original_json:
        line_key = f'line_{selected_line_index+1}'
    
    page_json = page_htr.hw_one_file(img_file, config_file, temp_json, line_key=line_key)
    
    tag_views.save_tag_json(page_json, img_file, json_file)
    return page_json
    
@shared_task
def page_HTR(img_file, original_json, sfr_path, json_file):

    sys.path.append(os.path.join(sfr_path, 'py3/'))
    sys.path.append(os.path.join(sfr_path, 'coords/'))
    sys.path.append(os.path.join(sfr_path, 'arabic/'))
    
    import page_htr
    config = get_config()
    if 'HTR' in config:
        config_file = config['HTR']['config_file']
    else:
        return original_json
    page_json = page_htr.page_htr_one_file(img_file, config_file)
    tag_views.save_tag_json(page_json, img_file, json_file)

    return page_json



    
def add_sfr_log(status):

    LOG_FILE = os.path.join(settings.DATASET_ROOT, 'LOG_SFR.txt')
    with open(LOG_FILE, 'a') as fout:
        fout.write(str(status))
        
        
def check_task_status(task_id):
    done = False	
    task = AsyncResult(task_id)
    if task.state == 'SUCCESS':
        done = True
    return {"task_id": task_id, "status": task.status, "result": task.result, 
             "done": done}


@shared_task
def htr_HATFormer(img_file, original_json, hat_path, line_key, json_file):

    sys.path.append(os.path.join(hat_path))
    
    import do_ocr
    config = get_config()
    if 'HTR' in config:
        model_path = config['HTR']['models']['HATFormer']['model_path']
    else:
        return original_json
       
    page_json = do_ocr.hw_one_file(img_file, original_json, model_path, line_key=line_key)

    tag_views.save_tag_json(page_json, img_file, json_file)
    return page_json
        
        
# celery -A scribeArabic worker --loglevel=info --concurrency=1 --max-tasks-per-child=2
        
