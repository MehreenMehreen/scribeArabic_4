from celery import shared_task
import subprocess
import settings

@shared_task
def run_page_htr(img_file, original_json, config_file):
    
    py_file_path = 'arabic/page_htr.py'
    
    directory, image_name = os.path.split(img_file)
    image_path = os.path.join(settings.DATASET_ROOT, directory, image_name)
    
    line_key = ''
    
    command = ['python', py_file_path, '--line_htr', '0', 
               '--img_path', image_path, '--config_file', config_file, 
               '--original_json', json.dumps(original_json), '--line_key', line_key]
    
    result = subprocess.run(command, capture_output=True, text=True,
                            cwd='/work/mehreen/source/htr_sfr_arabic/')
    
    page_json = original_json
    if result.returncode == 0:        
        data = result.stdout
        result_ind = data.find('BEGIN_OUT') + len('BEGIN_OUT')
        data = data[result_ind:]
        page_json = json.loads(data)

    return page_json    