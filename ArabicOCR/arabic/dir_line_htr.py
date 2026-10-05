import sys
import os
import page_htr
import json
import text_extractor
import argparse

def line_htr_directory(input_dir, config_flile, annotators=['sfr']):
    img_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.jpg')]
    img_files.sort()

    done = 0
    for f in img_files:        
        json_files = [os.path.join(input_dir, f[:-4]) + f'_annotate_{annotator}.json'
                     for annotator in annotators]
        json_files = [j for j in json_files if os.path.exists(j)]
        
        if len(json_files) > 1:
            print('More than one json file, taking the first one', json_files)
        if len(json_files) == 0:
            continue
        
        json_file = json_files[0]
        img_file = os.path.join(input_dir, f)
        with open(json_file) as fin:
            json_obj = json.load(fin)
        
        print('About to Line HTR', img_file)
        page_json = page_htr.hw_one_file(img_file, config_file, json_obj)

        
        extractor = text_extractor.ScribeArabicTextExtractor(image_json=page_json)
    
        
        sorted_json = extractor.get_sorted_json()
        
        
        print('Writing to', json_file)
        
        with open(json_file, 'w') as fout:
            json.dump(sorted_json, fout, indent=2, ensure_ascii=False)
    
    
if __name__ == "__main__":        
    
    
    
    
    
    
    parser = argparse.ArgumentParser(description="Run only Line-HTR on entire directory. No line detection.")
        
    
    parser.add_argument("--input_path", type=str, required=True, help="Input path")
    parser.add_argument("--config_file", type=str, help="SFR_Arabic config file",
                        default="model/trial_44_A/set0/config_4440.yaml")
    
    

    args = parser.parse_args()
    input_dir = args.input_path
    config_file = args.config_file
    line_htr_directory(input_dir, config_file)
    print('Done')