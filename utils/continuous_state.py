import os

import torch

from hw import cnn_lstm
from lf.line_follower import LineFollower
from sol.start_of_line_finder import StartOfLineFinder
from utils import safe_load


def init_model(config, sol_dir='best_overall', lf_dir='best_overall', hw_dir='best_overall', only_load=None):
    base_0 = config['network']['sol']['base0']
    base_1 = config['network']['sol']['base1']

    sol = None
    lf = None
    hw = None
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    if only_load is None or only_load == 'sol' or 'sol' in only_load:
        sol = StartOfLineFinder(base_0, base_1)
        sol_state = safe_load.torch_state(os.path.join(config['training']['snapshot'][sol_dir], 'sol.pt'))
        sol.load_state_dict(sol_state)
        sol = sol.to(device)

    if only_load is None or only_load == 'lf' or 'lf' in only_load:
        lf = LineFollower(config['network']['hw']['input_height'])
        lf_state = safe_load.torch_state(os.path.join(config['training']['snapshot'][lf_dir], 'lf.pt'))
        lf.load_state_dict(lf_state)
        lf = lf.to(device)

    if only_load is None or only_load == 'hw' or 'hw' in only_load:
        hw = cnn_lstm.create_model(config['network']['hw'])
        hw_state = safe_load.torch_state(os.path.join(config['training']['snapshot'][hw_dir], 'hw.pt'))
        hw.load_state_dict(hw_state)
        hw = hw.to(device)

    return sol, lf, hw


def load_model_from_checkpoint(network_config, checkpoint_dir):
    base_0 = network_config['sol']['base0']
    base_1 = network_config['sol']['base1']
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    sol_path = os.path.join(checkpoint_dir, 'sol_checkpoint.pt')
    sol_checkpoint = safe_load.load_checkpoint(sol_path)
    sol = StartOfLineFinder(base_0, base_1)
    sol.load_state_dict(sol_checkpoint['model_state_dict'])
    sol = sol.to(device)
    sol.eval()

    lf_path = os.path.join(checkpoint_dir, 'lf_checkpoint.pt')
    lf_checkpoint = safe_load.load_checkpoint(lf_path)
    lf = LineFollower(network_config['hw']['input_height'])
    lf.load_state_dict(lf_checkpoint['model_state_dict'])
    lf = lf.to(device)
    lf.eval()

    hw_path = os.path.join(checkpoint_dir, 'hw_checkpoint.pt')
    hw_checkpoint = safe_load.load_checkpoint(hw_path)
    hw = cnn_lstm.create_model(network_config['hw'])
    hw.load_state_dict(hw_checkpoint['model_state_dict'])
    hw = hw.to(device)
    hw.eval()

    return sol, lf, hw
