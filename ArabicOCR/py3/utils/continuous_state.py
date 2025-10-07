
import torch
from torch.utils.data import DataLoader
from torch.autograd import Variable
from torch import nn

import sol
from sol.start_of_line_finder import StartOfLineFinder
from lf.line_follower import LineFollower
from hw import cnn_lstm

from utils import safe_load

import numpy as np
import cv2
import json
import sys
import os
import time
import random

def init_model(config, sol_dir='best_validation', lf_dir='best_validation', hw_dir='best_validation', 
               only_load=None, device="cuda"):
    
    
    
    dtype = torch.FloatTensor
    if 'cuda' in device:
        dtype = torch.cuda.FloatTensor
    
    
    base_0 = config['network']['sol']['base0']
    base_1 = config['network']['sol']['base1']

    sol = None
    lf = None
    hw = None

    if only_load is None or only_load == 'sol' or 'sol' in only_load:
        sol = StartOfLineFinder(base_0, base_1)
        sol_state = safe_load.torch_state(os.path.join(config['snapshot_path'], "sol.pt"))
        sol.load_state_dict(sol_state)
        sol.to(device)

    if only_load is None or only_load == 'lf' or 'lf' in only_load:
        # This field may not be present in config and maybe added by the calling module...so you won't see it in the config file
        pt_file = 'lf.pt'
        
        lf = LineFollower(config['network']['hw']['input_height'], dtype=dtype, device=device)
        lf_state = safe_load.torch_state(os.path.join(config['snapshot_path'], pt_file))
        

        # special case for backward support of
        # previous way to save the LF weights
        if 'cnn' in lf_state:
            new_state = {}
            for k, v in lf_state.items():
                print(k)                
                if k == 'cnn': 
                    for k2, v2 in v.items():                        
                        if "running" in k2:
                            AAA=1
                        else:
                            new_state[k+"."+k2]=v2
                if k == 'position_linear':
                    # print(k2, v2)
                    for k2, v2 in  v.state_dict().items():
                        new_state[k+"."+k2]=v2
                # if k == 'learned_window':
                #     print(k, v.data)
                #     new_state[k]=nn.Parameter(v.data)
            
            lf_state = new_state
            


        lf.load_state_dict(lf_state)
        
        lf.to(device)

    if only_load is None or only_load == 'hw' or 'hw' in only_load:
        hw = cnn_lstm.create_model(config['network']['hw'])
        hw_state = safe_load.torch_state(os.path.join(config['snapshot_path'], "hw.pt"))
        hw.load_state_dict(hw_state)
        hw.to(device)

    return sol, lf, hw
