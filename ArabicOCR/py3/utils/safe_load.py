import torch
import time
import json
import os

def torch_state(path):
    for i in range(10):
        try:
            print('Current working dir', os.getcwd())
            if not os.path.exists(path):
                print('Warning: Model not found')
            else:
                #print('Good: Model is found')
                #print('Path permissions', os.access(path, os.R_OK))
                device = torch.device("cuda") if torch.cuda.is_available() else "cpu"

                state = torch.load(path, map_location=device) #, weights_only=True, map_location=device)
                return state
        except Exception as e:
            print("Failed to load",i,path, str(e))
            #time.sleep(i)
            pass

    print("Failed to load state of model")
    return

def json_state(path):
    for i in range(10):
        try:
            with open(path) as f:
                state = json.load(f)
            return state
        except:
            print("Failed to load",i,path)
            time.sleep(i)
            pass

    print("Failed to load state")
    return None
