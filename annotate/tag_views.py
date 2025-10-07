import sys
from django.apps import apps
from django.shortcuts import redirect
from django.http import HttpResponse
from django.template.loader import get_template 
from .models import imageFiles, directories
from django.conf import settings
import json
import os
import shutil
import time
from datetime import datetime, date
from pytz import timezone
import yaml
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .user_model import ScribeUser
import markdown
from . import text_extractor

LOG_FILE = os.path.join(settings.DATASET_ROOT, 'LOG_TAGGING.txt')
APP_DISPALY_LABEL = "ScribeArabic 4.2"

if settings.USE_CELERY:
    from . import tasks


def manual_view(request):
    app_path = apps.get_app_config('annotate').path
    md_path = os.path.join(app_path, 'templates', 'manual.md')
    
    with open(md_path, 'r') as f:
        md_text = f.read()
    html = markdown.markdown(md_text, extensions=["toc", "attr_list"])
    return render(request, 'manual.html', {'content': html})    
    
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('tag', user_name=user)  # or any other URL name
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form, 'heading': APP_DISPALY_LABEL})        
    

def get_textbox_ht():
    config_file = os.path.join(settings.DATASET_ROOT, settings.CONFIG_FILE)
    if not os.path.exists(config_file):
        return 50
    with open(config_file) as fin:
        config = yaml.safe_load(fin)
    
    textbox_ht = 50
    if 'textbox_ht' in config:
        textbox_ht = config['textbox_ht']
    
    return textbox_ht
    

def get_tag_list():

    config_file = os.path.join(settings.DATASET_ROOT, settings.CONFIG_FILE)
    if not os.path.exists(config_file):
        return [{}]
    with open(config_file) as fin:
        config = yaml.safe_load(fin)
    
    user_list = []
    if 'tag_dictionary' in config:
        tag_dictionary = config['tag_dictionary']
    if len(tag_dictionary) == 0:
        tag_dictionary = {}
    return tag_dictionary


def get_user_list():    
    usernames = ScribeUser.objects.values_list('name', flat=True)
    user_fullnames = ScribeUser.objects.values_list('fullname', flat=True)
    return usernames, user_fullnames

def get_dataset_path(request):
    print('USER IS', request.user, request.user.is_staff)
    if not request.user.is_authenticated:
        return render(request, 'not_authorized.html', status=403)
    if request.user.is_public:
        return settings.PUBLIC_DATASET_PATH
    if request.user.is_staff:
        return settings.STAFF_DATASET_PATH    
    return settings.DATASET_PATH
    
def tag_home(request):
    if not request.user.is_authenticated:
        return render(request, 'not_authorized.html', status=403)
    
    if request.user.is_public:
        return redirect(upload_file)
    else:
        return redirect(show_directory)    

def show_directory(request):    
    if not request.user.is_authenticated or request.user.is_public:
        return render(request, 'not_authorized.html', status=403)
    
    config = get_config()
    USER_LIST =  [request.user.name]  
    TAG_TASKS = ["tag"]
    TAG_TASKS_DESCRIPTION = ["Tag images"]
    IMAGES = imageFiles()
    # DEfaults    
    task = "tag"
    post_response = "1"
    dir = directories()
    user_dataset_path = get_dataset_path(request)
    directory = os.path.join(settings.DATASET_ROOT, user_dataset_path)
    print('directory1', directory)
    dir_obj = dir.load_directories(directory, task="tag", user=request.user.name, include_submitted=True)
    print('dir_obj', dir_obj)
    dir_json = json.dumps(dir_obj)
    # IS this a QA session ...
    checking_flag = request.session.get('checkingMenu', 0)

    template = get_template('tagHomePage.html')
    context = {
           "users": USER_LIST,         
           "directoryList": dir_json,
           "totalFiles": dir.total_files,
           "allTasks": TAG_TASKS,
           "allTasksDescription": TAG_TASKS_DESCRIPTION, 
           "userInd": 0, 
           "taskInd": 0,
           "error": [""],
           "heading": APP_DISPALY_LABEL,
           "tag_dictionary": get_tag_list(),
           "checking": checking_flag,
           } 
    admin = request.session.get('adminTag', None)
    if admin is not None:
        context["userInd"] = admin["userInd"]
        context["taskInd"] = admin["taskInd"]
        if 'error' in admin.keys():
            context["error"] = [admin["error"]]
        
        dir_obj = dir.load_directories(directory, task="tag", user=request.user.name, 
                                       include_submitted=True)
        dir_json = json.dumps(dir_obj)

        
    
    
    context["directoryList"] = dir_json
    context["totalFiles"] = dir.total_files

    if request.method == 'POST':
        post_response = request.POST
        #print('post_response', post_response)
        if "userForm" in request.POST:
            post_response = json.loads(request.POST["userForm"])
            context["userInd"] = post_response["userInd"]
            context["taskInd"] = post_response["taskInd"]
            user_name = request.user.name
            task = TAG_TASKS[context["taskInd"]].lower()
            
            if task == "viewTag":
                dir_obj = dir.load_directories(task="viewTag")
                dir_json = json.dumps(dir_obj)    
                    
                
            elif task == "tag":

                directory = os.path.join(settings.DATASET_ROOT, user_dataset_path)
                path_to_add = user_dataset_path

                print('directory is', directory)
                dir_obj = dir.load_directories(directory, task="tag", user=user_name,
                                                            include_submitted=True)
                dir_json = json.dumps(dir_obj)

            context["directoryList"] = dir_json
            context["toverifyList"] = dir_json
            context["totalFiles"] = dir.total_files
            context["error"] = [""]

            if "start" in post_response and post_response["start"] == 1:
                context["dir"] = post_response["dir"]
                context["filesList"] = post_response["filesList"]

                directory = os.path.join(settings.DATASET_ROOT, user_dataset_path, context["dir"])
                path_to_add = os.path.join(user_dataset_path, context["dir"])    
                
                # Username is irrelevant here
                IMAGES.load_files_for_user(directory, user_name, task, 
                                   path_to_add=path_to_add, 
                                   select_files=context["filesList"])
                request.session['images'] = IMAGES.get_json_string_for_client()
                user_fullname = user_name
                
                request.session['adminTag'] = {'user': user_name, 
                                 'task': task, 
                                 'userInd': context["userInd"], 
                                 'taskInd': context["taskInd"], 'error':"", 'heading': APP_DISPALY_LABEL,
                                 'to_check_user':user_name,
                                  'toCheckUserInd':context["userInd"],
                                  'tagDictionary': context["tag_dictionary"],
                                  'user_fullname': user_fullname,
                                 'textbox_ht': get_textbox_ht()}


                #print('context', context)
                if task == "view":
                    add_tag_log(request.session['adminTag'], IMAGES, 'serve_home/view')
                    return redirect(view_files)    
                
                if task == "tag":
                    add_tag_log(request.session['adminTag'], IMAGES, 'serve_home/tagBlock')
                    return redirect(tag_image)
                
    
    
    # Update admin_dict only
    user_ind = context["userInd"]
    task_ind = context["taskInd"] 
    user_fullname = request.user.fullname
    
    request.session['adminTag'] = {  'user': request.user.name, 
                                     'task': TAG_TASKS[task_ind ].lower(), 
                                     'userInd': 0, 
                                     'taskInd': task_ind, 'error':"", 'heading': APP_DISPALY_LABEL,
                                     'to_check_user':request.user.name,
                                     'toCheckUserInd':0,
                                     'user_fullname': user_fullname, 
                                     'textbox_ht': get_textbox_ht()}

    request.session['images'] = IMAGES.get_json_string_for_client()

    #print('IMAGES.get_json_string_for_client()', IMAGES.get_json_string_for_client())
    return HttpResponse(template.render(context, request))






def tag_image(request):
    if not request.user.is_authenticated:
        return render(request, 'not_authorized.html', status=403)

    config = get_config()
    
    if 'HTR' in config and 'use_celery' in config['HTR'] and config['HTR']['use_celery']:
        from . import tasks
    HTR = {'task_id': -1, 'htr_done': 0, 'type': 'none', 'status': 'none', 'models': 'None'}
    show_HTR = 0
    if 'HTR' in config and config['HTR']['show_HTR']:
        show_HTR = 1
        HTR['models'] = list(config['HTR']['models'].keys())
     
    # scroll position only important when saving. Client screen will jump to 
    # the saved scroll position
    scroll_position = {"x": 0, "y": 0}
    options = {"radius": 2, "lineWidth": 1, "zoomFactor": 1.0, "colWidth": 6, "show_HTR": show_HTR, 
               "show_tags": 0, "show_regions": 0, "HTR_model_ind": 0, "is_public_user": 1 if request.user.is_public else 0,
               "htr_in_progress": 0, "downloadText": 0}
    col_width = 6
    checking_flag = request.session.get('checkingMenu', 0)    
    
    images_json = request.session.get('images', None)
    admin = request.session.get('adminTag', None)
    
    if images_json is None or admin is None:
        
        IMAGES = imageFiles()
        add_tag_log(admin, IMAGES, 'tagBlock/serve_homepage/empty')
        return redirect(tag_home)

    IMAGES = imageFiles()
    IMAGES.load_from_json_string(images_json)
    add_tag_log(admin, IMAGES, "At start of tag_image") 

    template = get_template('tagBlock.html')
    if request.method == 'POST':
        #print('Request posted', request.POST)
        
        # For all these requests don't save file if HTR is in progress. As the old file might get saved
        # 'AFTER' the HTR is run....json is saved in tasks.py also

            
        
        if 'previous' in request.POST:
            IMAGES, admin, page_json, options = load_from_transcribe_block_response(request, 'previous')
            json_file = json.loads(request.POST['previous'])['json_file'];
            if options["htr_in_progress"] == 0:
                save_tag_json(page_json, IMAGES.get_current(), json_file)
            add_tag_log(admin, IMAGES, 'tagBlock/previous')
            filename = IMAGES.get_previous()
        elif 'next' in request.POST:
            IMAGES, admin, page_json, options = load_from_transcribe_block_response(request, 'next')
            json_file = json.loads(request.POST['next'])['json_file']
            if options["htr_in_progress"] == 0:
                save_tag_json(page_json, IMAGES.get_current(), json_file)
            add_tag_log(admin, IMAGES, 'tagBlock/next')
            filename = IMAGES.get_next()
        elif 'save' in request.POST:
            IMAGES, admin, page_json, options = load_from_transcribe_block_response(request, 'save')      
            json_file = json.loads(request.POST['save'])['json_file']
            if options["htr_in_progress"] == 0:
                save_tag_json(page_json, IMAGES.get_current(), json_file)
            add_tag_log(admin, IMAGES, 'tagBlock/save')
            json_obj = json.loads(request.POST['save'])
            scroll_position = json_obj['scroll_position']               
        elif 'end' in request.POST:
            IMAGES, admin, page_json, options = load_from_transcribe_block_response(request, 'end')      
            json_file = json.loads(request.POST['end'])['json_file']
            #print('json_file', json_file)
            if options["htr_in_progress"] == 0:
                save_tag_json(page_json, IMAGES.get_current(), json_file)
            add_tag_log(admin, IMAGES, 'tagBlock/end')
            return redirect(tag_home)
        elif 'submitForm' in request.POST:
            IMAGES, admin, page_json, options = load_from_transcribe_block_response(request, 'submitForm')      
            json_file = json.loads(request.POST['submitForm'])['json_file']
            save_tag_json(page_json, IMAGES.get_current(), json_file)
            submit_done, return_error = submit_tagged_file(page_json, IMAGES.get_current(), admin, json_file)
            if not submit_done:
                admin['error'] = 'Error submitting: ' + return_error
                request.session['adminTag'] = admin
                request.session['images'] = IMAGES.get_json_string_for_client()
                add_tag_log(admin, IMAGES, 'tagBlock/submit/{}'.format(return_error))
                return redirect(tag_home)
            else:
                IMAGES.remove_current()
                add_tag_log(admin, IMAGES, 'tagBlock/submit'+return_error)
        elif 'checked' in request.POST:
            
            IMAGES, admin, page_json, options = load_from_transcribe_block_response(request, 'checked')      
            json_file = json.loads(request.POST['checked'])['json_file'];
            save_tag_json(page_json, IMAGES.get_current(), json_file)
            check_done, return_error = submit_tagged_file(page_json, IMAGES.get_current(), 
                                                          admin, json_file, suffix="checked")
            if not check_done:
                admin['error'] = 'Error submitting checked file: ' + return_error
                request.session['adminTag'] = admin
                request.session['images'] = IMAGES.get_json_string_for_client()
                add_tag_log(admin, IMAGES, 'tagBlock/check/{}'.format(return_error))
                return redirect(tag_home)
            else:
                IMAGES.remove_current()
                add_tag_log(admin, IMAGES, 'tagBlock/check')                
        elif 'pageHTR' in request.POST:
            HTR['type'] = 'page' 
            
            IMAGES, admin, page_json, options = load_from_transcribe_block_response(request, 'pageHTR')      
            json_file = json.loads(request.POST['pageHTR'])['json_file']
            #save_tag_json(page_json, IMAGES.get_current(), json_file)
            add_tag_log(admin, IMAGES, 'tagBlock/pageHTR')
            json_obj = json.loads(request.POST['pageHTR'])
            scroll_position = json_obj['scroll_position']
            HTR['task_id'] = json_obj['task_id']
            
            img_file = IMAGES.get_current()
            # Will only modify the line keys...the rest of json obj will remain unchanged
            # ANd will also add htr info
            if HTR['task_id'] == -1:
                add_tag_log(admin, IMAGES, "starting page HTR")
                htr_models = HTR['models']
                htr_model_ind = min(options['HTR_model_ind'], len(htr_models)-1)
                
                htr_return = page_HTR(img_file, page_json, htr_models[htr_model_ind], json_file)
                HTR['task_id'] = htr_return['task_id']
                HTR['htr_done'] = 1 if htr_return['htr_done'] else 0
                add_tag_log(admin, IMAGES, "task id " + str(HTR['task_id']))
                if htr_return['htr_done']:
                    add_tag_log(admin, IMAGES, "page HTR done in first call " + str(htr_return['task_id']))
                    json_from_htr = htr_return['json']    
                    save_tag_json(json_from_htr, IMAGES.get_current(), json_file)
                
                    
            else:
                add_tag_log(admin, IMAGES, "checking status task id" + str(HTR['task_id']))
                status = tasks.check_task_status(HTR['task_id'])
                print('......TASK STATUS', status)
                HTR['status'] = status['status']
                add_tag_log(admin, IMAGES, 'status' + str(HTR))
                if status['done']:
                    add_tag_log(admin, IMAGES, "page HTR done for task id" + str(HTR['task_id']))
                    HTR['htr_done'] = 1
                    json_from_htr = status['result']    
                    save_tag_json(json_from_htr, IMAGES.get_current(), json_file)
                    HTR['task_id'] = -1
                    
                elif status['status'] == 'FAILURE':
                    HTR['task_id'] = -1
  
        elif 'lineHTR' in request.POST:    
            HTR['type'] = 'line' 
            IMAGES, admin, page_json, options = load_from_transcribe_block_response(request, 'lineHTR')      
            json_file = json.loads(request.POST['lineHTR'])['json_file']
            #save_tag_json(page_json, IMAGES.get_current(), json_file)
            add_tag_log(admin, IMAGES, 'tagBlock/lineHTR')
            json_obj = json.loads(request.POST['lineHTR'])
            scroll_position = json_obj['scroll_position']
            HTR['task_id'] = json_obj['task_id']
            
            
            img_file = IMAGES.get_current()
            # Will only modify the line keys...the rest of json obj will remain unchanged
            # ANd will also add htr info
            selected_line_index = -1
            if "selectedLineIndex" in options:
                selected_line_index = options["selectedLineIndex"]
            if HTR['task_id'] == -1:
                add_tag_log(admin, IMAGES, "starting line HTR")
                htr_models = HTR['models']
                htr_model_ind = min(options['HTR_model_ind'], len(htr_models)-1)
                htr_return = line_HTR(img_file, page_json, 
                                      selected_line_index, htr_models[htr_model_ind], json_file)
                HTR['task_id'] = htr_return['task_id']
                HTR['htr_done'] = 1 if htr_return['htr_done'] else 0
                add_tag_log(admin, IMAGES, "task id " + str(HTR['task_id']))
                if htr_return['htr_done']:
                    add_tag_log(admin, IMAGES, "line HTR done in first call " + str(htr_return['task_id']))
                    json_from_htr = htr_return['json']    
                    save_tag_json(json_from_htr, IMAGES.get_current(), json_file)
                
            else:
                add_tag_log(admin, IMAGES, "checking status task id" + str(HTR['task_id']))
                status = tasks.check_task_status(HTR['task_id'])
                HTR['status'] = status['status']
                add_tag_log(admin, IMAGES, 'status' + str(HTR))
                if status['done']:
                    add_tag_log(admin, IMAGES, "line HTR done for task id" + str(HTR['task_id']))
                    HTR['htr_done'] = 1
                    json_from_htr = status['result']  
                    # This also done in tasks.py
                    save_tag_json(json_from_htr, IMAGES.get_current(), json_file)
                    HTR['task_id'] = -1
                elif status['status'] == 'FAILURE':
                    HTR['task_id'] = -1
            
        elif 'getSortedJson' in request.POST:
            add_tag_log(admin, IMAGES, "getting sorted json")
            IMAGES, admin, page_json, options = load_from_transcribe_block_response(request, 'getSortedJson')    
            extractor = text_extractor.ScribeArabicTextExtractor(image_json=page_json)
            text = extractor.get_text()
            page_json['text'] = text
            json_file = json.loads(request.POST['getSortedJson'])['json_file']
            if options["htr_in_progress"] == 0: 
                save_tag_json(page_json, IMAGES.get_current(), json_file)
            
            json_obj = json.loads(request.POST['getSortedJson'])
            scroll_position = json_obj['scroll_position']    
            options["downloadText"] = 1
            
            

    if IMAGES.empty_files() == 1:
        admin['error'] = 'Reached the end. Thank you!'
        request.session['adminTag'] = admin
        request.session['images'] = IMAGES.get_json_string_for_client()
        add_tag_log(admin, IMAGES, 'tagBlock/submit/done')
        return redirect(tag_home)        


    img_file = IMAGES.get_current()


    json_dict = get_json_files_for_tagging(img_file, admin)
        
    context = {
               "img_file": img_file,
               "jsonList": json_dict,
               "admin": admin,
               "images_obj": IMAGES.get_json_string_for_client(),
               "scroll_position": scroll_position,
               "options": options, 
               "heading": APP_DISPALY_LABEL,
               "tagDictionary": get_tag_list(),
               "checking": request.session.get('checkingMenu', 0),
               "HTR": HTR
              }
    add_tag_log(admin, IMAGES, 'tagBlock/tagBlock')
    
    request.session['adminTag'] = admin
    request.session['images'] = IMAGES.get_json_string_for_client()
    
    # If an htr in progress for this session
    #check_htr_status(request)
    
    return HttpResponse(template.render(context, request))


        

# img_file name needed for directory
def save_tag_json(json_obj, img_file, json_filename):
    directory = os.path.split(img_file)[0]
    json_file = os.path.join(settings.DATASET_ROOT, directory, json_filename)
    #print('json_file', json_file)        
    # Take backup of existing json
    if os.path.exists(json_file):
        backupname = json_file[:-4] + str(time.time()) + '.json'
        shutil.copyfile(json_file, backupname)

    
    with open(json_file, 'w') as fout:
        json_dumps_str = json.dumps(json_obj, indent=2)
        print(json_dumps_str, file=fout) 


def submit_tagged_file(page_json, jpg_filename, admin, json_filename, suffix="submitted"):
    user = admin['user']
    xml_written = "notDoneXML"
    
    path, filename = os.path.split(jpg_filename)
    basename, ext = os.path.splitext(filename)
    # Get full json and jpg filenames
    full_json_path = os.path.join(settings.DATASET_ROOT, path, json_filename)                 
    full_jpg_path = os.path.join(settings.DATASET_ROOT, jpg_filename)

    # Get target path and create if it does not exist
    # GEt enclosing folder name
    parent_dir, _ = os.path.split(full_jpg_path)

    if suffix == 'checked' and parent_dir.endswith('_submitted'):
        parent_dir = parent_dir.replace("_submitted", "")

    full_target_path = os.path.join(settings.DATASET_ROOT, parent_dir + f'_{suffix}/')
    if not os.path.exists(full_target_path):
        os.mkdir(full_target_path)

    try:
        # Take backup of existing json
        #print('fulljson', full_json_path)
        backupname = full_json_path[:-4] + str(time.time()) + f'.json.{suffix}'
        shutil.move(full_json_path, backupname)
        
        # Save json
        target_json = os.path.join(full_target_path, json_filename)
        with open(target_json, 'w') as fout:
            json_dumps_str = json.dumps(page_json, indent=2)
            print(json_dumps_str, file=fout) 
        
        
        target_jpg = os.path.join(full_target_path, filename)
        

        # Generate the xml for the submitted file and write it
        
        #xml_written = write_xml(target_jpg, target_json)

        # Move  jpg file to submitted folder
        shutil.move(full_jpg_path, target_jpg)
        
        
        return True, xml_written + " done "
        
    except Exception as e:
        return True, xml_written + str(e)

# This is within a try catch block
def write_xml(jpg_file, json_file):
    try:
        
        output_xml = os.path.join(jpg_file[:-3]+'xml')
        json_page = xml.TranscriptionPage(filename=json_file, 
                                          imagefile=jpg_file)
        
        xml_obj = xml.PageXML(json_page, output_xml)   
        xml_obj.write_xml()
        return "donexml"
    except Exception as e:
        return str(e)
        

def get_json_files_with_annotator(directory, base_file):
    json_files = []
    annotators = []
    files = os.listdir(os.path.join(settings.DATASET_ROOT, directory))
    
    for f in files:
        prefix = base_file + '_annotate_'
        #print('prefix', prefix)
        if f.startswith(prefix):
            # Check if its a timestamp in filename
            partial_string = f[len(prefix):]
            ind1 = partial_string.rfind('.')
            ind2 = partial_string.find('.')
            # Possible that no annotator
            annotator = partial_string[:ind1]
            
            if (ind1 == ind2):
                json_files.append(f)
                annotators.append(annotator)

    return json_files, annotators

def get_json(json_path):
    full_path = os.path.join(settings.DATASET_ROOT, json_path)
    line_obj = {}
    if os.path.exists(full_path):
        with open(full_path, 'r') as myfile:
            data=myfile.read()

            # parse file
            line_obj = json.loads(data)
            return line_obj
    return {}

def get_json_files_for_tagging(img_file, admin):
    directory, file = os.path.split(img_file)
    base_file, ext = os.path.splitext(file)

    json_file_list, annotators = get_json_files_with_annotator(directory, base_file)
    json_file_list.sort()
    #print('annotators', annotators, 'json_file_list', json_file_list)
    json_dict = {"fileList":json_file_list}
    
    for ind, f in enumerate(json_file_list):
        json_obj = get_json(os.path.join(directory, f))

        json_dict[f] = {'json': json_obj, 'annotator': annotators[ind]}
    # Make empty json if no json is present    
    if len(json_file_list) == 0:
        json_filename = base_file + '_annotate_' + admin['user'] + '.json'
        json_dict = {'fileList': [json_filename], json_filename: {'json': {}, 'annotator': admin['user']}}
    return json_dict


def tag(request, user_name):
    if not request.user.is_authenticated or user_name.lower() != request.user.name:
        return render(request, 'not_authorized.html', status=403)
    
    
    
    config = get_config()
    user_fullname = request.user.fullname
    
    
    request.session['checkingMenu'] = 0
    user = request.user.name
    task = "tag"     
    user_dataset_path = get_dataset_path(request)
    directory = os.path.join(settings.DATASET_ROOT, user_dataset_path, user+'/')
    IMAGES = imageFiles()
 
    
    
    IMAGES.load_files_for_user(directory, user=user, task=task, 
                                path_to_add=user_dataset_path + user + '/')    

    admin = {'user':user, 'task':"tag", 'to_check_user':user,
         'userInd': -1, 'toCheckUserInd':-1,  # Indices no longer needed
         'taskInd': 0, 'error':"", 'user_fullname': user_fullname, 
         'textbox_ht': get_textbox_ht()}    
    request.session['adminTag'] = admin
    request.session['images'] = IMAGES.get_json_string_for_client()
    request.session['checkingMenu'] = 0
    
    if IMAGES.empty_files():    
        # No images to transcribe
        admin['task'] = "tag"
        admin['taskInd'] = 0
        admin['error'] = "No images to tag"
        request.session['admin'] = admin
        add_tag_log(admin, IMAGES, 'tag/homepage...no images')
        return redirect(tag_home)
        
                                     
    add_tag_log(admin, IMAGES, 'tag/tag')                                 
    return redirect(tag_image)       

def check_tags(request):
    request.session['checkingMenu'] = 1

    add_tag_log(None, None, "In check_tags URL")
    return redirect(tag_home)


def add_tag_log(admin, images_obj, comment=""):

    # Log eastern time ... https://pynative.com/python-timezone/
    tz = timezone('EST')
    date_time = datetime.now(tz) 
    time_str = date_time.strftime('%Y-%m-%d %H:%M:%S')
    strToWrite = time_str + ' ' + 'comment: ' + comment + '\n'
    if admin is not None:
        strToWrite += '\t' + admin.get('user', 'none') + ' ' + str(admin.get('userInd', -1)) + ' ' + admin.get('task', "none") + ' ' + str(admin.get('taskInd', -1))
    else:
        strToWrite += "Admin none"
    if images_obj is not None:
        strToWrite += '\t' + str(images_obj.index) + ' ' + images_obj.get_current() + '\n'
    else:
        strToWrite += '\t images None'
    with open(LOG_FILE, 'a') as fout:
        fout.write(strToWrite)
        
def HATFormer(image_path, original_json, line_key=''):
    config = get_config()
    py_file_path = 'do_ocr.py'
    hatformer_path = '/work/mehreen/source/HATFormer'
    if 'path' in config['HTR']['models']['HATFormer']:
        hatformer_path = config['HTR']['models']['HATFormer']['path']
    command = ['python3', py_file_path,  
              '--img_path', image_path, 
              '--original_json', json.dumps(original_json), 
              '--line_key', line_key]
    import subprocess
    result = subprocess.run(command, capture_output=True, text=True,
                            cwd=hatformer_path)
    page_json = original_json
    try:
        if result.returncode == 0:
            print('HATFormer return status is zero (success)')
            data = result.stdout
            result_ind = data.find('BEGIN_OUT') + len('BEGIN_OUT')
            data = data[result_ind:]
            page_json = json.loads(data)
        else:
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"HATFormer failed with return code {e.returncode}")    
    return {'json': page_json, 'task_id': -1, 'htr_done': True}
        

        
    
        
def page_HTR(img_file, original_json, htr_model, json_file):
    
    config = get_config()
    if 'HTR' in config:
        config_file = config['HTR']['config_file']
    else:
        return {'json': original_json, 'task_id': -1, 'htr_done': True}
    
    py_file_path = 'arabic/page_htr.py'
    sfr_path = config['HTR']['models']['SFR-Arabic'].get('path', '/work/mehreen/source/htr_sfr_arabic/')

    directory, image_name = os.path.split(img_file)
    image_path = os.path.join(settings.DATASET_ROOT, directory, image_name)
    
    if 'use_celery' in config['HTR'] and config['HTR']['use_celery']:
        from annotate import tasks
        if htr_model == 'HATFormer':
            hat_path = config['HTR']['models']['HATFormer'].get('path', 'HATFormer/')
            # Line key empty for page HTR
            task = tasks.htr_HATFormer.delay(image_path, original_json, hat_path, '', json_file)
        else:
            task = tasks.page_HTR.delay(image_path, original_json, sfr_path, json_file)
        return {'json': None, 'task_id': task.id, 'htr_done': False}
        
    if htr_model == 'HATFormer':
        return HATFormer(image_path, original_json)
    
        
    # Run the process
    
    command = ['python', py_file_path, '--line_htr', '0', 
               '--img_path', image_path, '--config_file', config_file, 
               '--original_json', json.dumps(original_json), '--line_key', '-1']
    
    import subprocess
    result = subprocess.run(command, capture_output=True, text=True,
                            cwd=sfr_path)
    
    page_json = original_json
    add_tag_log(None, None, str(result.stdout))
    add_tag_log(None, None, str(result.stderr)) 
    print('process return code', result.returncode, 'sfr_path', sfr_path)
    try:
        if result.returncode == 0:
            print('SFR return status is zero (success)')
            data = result.stdout
            result_ind = data.find('BEGIN_OUT') + len('BEGIN_OUT')
            data = data[result_ind:]
            page_json = json.loads(data)
        else:
            add_tag_log(None, None, str(result.stderr))
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        add_tag_log(None, None, str(e))
        print(f"Command failed with return code {e.returncode}")


    
    return {'json': page_json, 'task_id': -1, 'htr_done': True}

    

    
    
def line_HTR(img_file, original_json, selected_line_index, htr_model, json_file):    
    
    
    config = get_config()
    if 'HTR' in config:
        config_file = config['HTR']['config_file']
    else:
        return {'json': original_json, 'task_id': -1, 'htr_done': True}
    
    py_file_path = 'arabic/page_htr.py'
    sfr_path = config['HTR']['models']['SFR-Arabic'].get('path', '/work/mehreen/source/htr_sfr_arabic/')

    directory, image_name = os.path.split(img_file)
    image_path = os.path.join(settings.DATASET_ROOT, directory, image_name)
    
    line_key = ''
    if f'line_{selected_line_index+1}' in original_json:
        line_key = f'line_{selected_line_index+1}'
    
    if 'use_celery' in config['HTR'] and config['HTR']['use_celery']:
        from . import tasks
        if htr_model == 'HATFormer':
            # Line key empty for page HTR
            hat_path = config['HTR']['models']['HATFormer'].get('path', 'HATFormer/')
            task = tasks.htr_HATFormer.delay(image_path, original_json, hat_path, line_key, json_file)
        else:
            task = tasks.line_HTR.delay(image_path, original_json, selected_line_index, sfr_path, json_file)
        return {'json': None, 'task_id': task.id, 'htr_done': False}
                
    if htr_model == 'HATFormer':
        return HATFormer(image_path, original_json, line_key)
    
    # Run the process

    if 'sfr_path' in config['HTR']:
        sfr_path = config['HTR']['sfr_path']
    else:
        sfr_path = 'ArabicOCR/'
    
    command = ['python', py_file_path, '--line_htr', '1', 
               '--img_path', image_path, '--config_file', config_file, 
               '--original_json', json.dumps(original_json), '--line_key', line_key]
    
    import subprocess
    result = subprocess.run(command, capture_output=True, text=True,
                            cwd=sfr_path)
    
    page_json = original_json
    if result.returncode == 0:
        data = result.stdout
        
        result_ind = data.find('BEGIN_OUT') + len('BEGIN_OUT')
        data = data[result_ind:]
        page_json = json.loads(data)
        print('Done Line HTR')

    else:
        add_tag_log(None, None, str(result.stderr))
        print('Could not do line HTR', result.stderr)
    
    return {'json': page_json, 'task_id': -1, 'htr_done': True}
    
    
    

    
def get_session_object_for_upload(job, request, file_list, user="uploader", 
                                  user_fullname="uploader", user_ind=-1):
    IMAGES = imageFiles()
    config = get_config()
   
    
    if 'textbox_ht' in config:
        textbox_ht = config['textbox_ht']

    admin_tag = {'user': user, 
                'task': "tag_after_upload", 
                'userInd': user_ind, 
                'taskInd': -1, 
                'error':"", 
                'heading': APP_DISPALY_LABEL,
                'to_check_user': user,
                'toCheckUserInd':user_ind,
                'user_fullname': user_fullname, 
                'textbox_ht': textbox_ht}

    user_dataset_path = get_dataset_path(request)
    directory = os.path.join(settings.DATASET_ROOT, user_dataset_path, job+'/')
    images = {'file_list': [os.path.join(user_dataset_path, job+'/', f) for f in file_list], 
              'index': 0, 
              'path': os.path.join(settings.DATASET_ROOT, user_dataset_path, job+'/')}
    print('......', images)
    return admin_tag, images
    


    
def get_random_job_name():
    date_time = datetime.now() 
    random_str = date_time.strftime('job_%Y-%m-%d_%H-%M-%S_') + str(time.time())[-3:]
    return random_str

def get_total_created_files_today(folder):

    if not os.path.exists(folder):
        return 0
    
    today = date.today()
    
    
    count = 0

    for f in os.listdir(folder):
        if f.lower().endswith(".jpg"):
            full_path = os.path.join(folder, f)
            ctime = datetime.fromtimestamp(os.path.getctime(full_path))
            ctime_date = datetime.date(ctime)  
            if ctime_date == today:
                count += 1

    return count
    
def upload_file(request):
    
    config = get_config()
    
    if not request.user.is_authenticated:
        return render(request, 'not_authorized.html', status=403)
    
    
    template = get_template('uploadFiles.html')
    
    user = request.user.name
    user_fullname = request.user.fullname
    #job = get_random_job_name()
    job = request.user.name
    user_dataset_path = get_dataset_path(request)
    directory = os.path.join(settings.DATASET_ROOT, user_dataset_path, job+'/')
    submitted_directory = os.path.join(settings.DATASET_ROOT, user_dataset_path, f'{job}_submitted')
    total_created_files = get_total_created_files_today(directory) + get_total_created_files_today(submitted_directory)
    file_limit = max(0, config.get('upload_file_limit_per_day', 5) - total_created_files)
    
    file_max_size = config.get('file_max_size', 1000000)
    admin = dict()
    
    context = {"users": [user],     # REmove this in new version    
               "error": [""],
               "not_done": [],
               "done": [],
               "user_selected": request.user.name,
               "heading": APP_DISPALY_LABEL,
               "job_folder": [job],
               "file_limit": file_limit,
               "file_max_size": file_max_size,
               "user": user,
               "total_user_files": total_created_files, 
               "total_files_to_annotate": get_total_created_files_today(directory)
              }  

    if request.method == 'POST':
        #print('FILES.....', request.FILES)

        uploaded_files = request.FILES.getlist('files')    
        directory = os.path.join(settings.DATASET_ROOT, user_dataset_path, job+'/')
        if not os.path.exists(directory):
            os.mkdir(directory)
        notdone_list = []
        done_list = []

        for file_item in uploaded_files:
            target_filename = os.path.join(directory, file_item.name)
            # File already exists
            if os.path.exists(target_filename):
                notdone_list.append({"filename":file_item.name, "error":"File exists"})
            else:
                try:
                    with open(target_filename, 'wb+') as destination:
                        for chunk in file_item.chunks():
                            destination.write(chunk)
                    done_list.append(file_item.name)
                except Exception as e:
                    notdone_list.append({"filename": file_item.name, "error": e})
            
        add_tag_log(admin, None, "After upload") 
        context['user_selected'] = user
        context['not_done'] = notdone_list
        context['done'] = done_list
        context['job_folder'] = [user]
        
        if len(notdone_list) > 0:
            return HttpResponse(template.render(context, request))        
        
        if 'formInput' in request.POST and 'annotate' in request.POST['formInput']: 
            
            post_response = json.loads(request.POST['formInput'])
            #    if post_response['annotate'] == 1:
            job = post_response['job']                
            file_list = post_response['fileList']

            if len(file_list) == 0:
                add_tag_log(admin, None, "Redirect tag for annotate from upload")    
                return redirect(tag, user)

            admin, images = get_session_object_for_upload(job, request, file_list, user, user_fullname)
            request.session['images'] = images
            request.session['adminTag'] = admin


            add_tag_log(admin, None, "Redirect tag_image from upload")            
            return redirect(tag_image)            
            
        
    return HttpResponse(template.render(context, request))
    
def load_from_transcribe_block_response(request, name):
    json_obj = json.loads(request.POST[name])

    images_json = json_obj['images_obj']
    images = imageFiles()
    images.load_from_json_string(images_json)
    admin = json_obj['admin']
    page_json = json.loads(json_obj['page_json'])
    options = json_obj['options']

    return images, admin, page_json, options    
    

def get_config(key=None):
    config_file = os.path.join(settings.DATASET_ROOT, settings.CONFIG_FILE)
    if not os.path.exists(config_file):
        return {}
    with open(config_file) as fin:
        config = yaml.safe_load(fin)
        
    return config
    

    
