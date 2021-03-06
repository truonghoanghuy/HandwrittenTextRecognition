import json
import os
import sys

import cv2
import numpy as np
import torch
import yaml

from e2e import e2e_postprocessing
from e2e.e2e_model import E2EModel
from utils.printer import ProgressBarPrinter


def process(image_path_directory_, config_path_, out_directory_, mode):
    image_path_directory = image_path_directory_

    image_paths = []
    for root, folder, files in os.walk(image_path_directory):
        for f in files:
            if f.lower().endswith('.jpg') or f.lower().endswith('.png') or f.lower().endswith('.jpeg'):
                image_paths.append(os.path.join(root, f))

    with open(config_path_) as f:
        config = yaml.load(f)

    output_directory = out_directory_
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    char_set_path = config['network']['hw']['char_set_path']
    with open(char_set_path, encoding='utf8') as f:
        char_set = json.load(f)
    idx_to_char = {int(k): v for k, v in char_set['idx_to_char'].items()}
    char_to_idx = char_set['char_to_idx']

    model_mode = 'best_overall'
    sol, lf, hw = init_model(config, sol_dir=model_mode, lf_dir=model_mode, hw_dir=model_mode)

    e2e = E2EModel(sol, lf, hw)
    e2e.eval()

    progress_bar = ProgressBarPrinter(len(image_paths))
    progress_bar.start()
    for image_path in sorted(image_paths):
        org_img = cv2.imread(image_path)
        # print(image_path, org_img.shape if isinstance(org_img, np.ndarray) else None)

        txt_path = image_path.split('.')[0] + '.txt'
        label = open(txt_path, encoding='utf8').read()
        len_label = torch.tensor([len(label)])

        target_dim1 = 512
        s = target_dim1 / float(org_img.shape[1])

        pad_amount = 128
        org_img = np.pad(org_img, ((pad_amount, pad_amount), (pad_amount, pad_amount), (0, 0)), 'constant',
                         constant_values=255)

        target_dim0 = int(org_img.shape[0] * s)
        target_dim1 = int(org_img.shape[1] * s)

        full_img = org_img.astype(np.float32)
        full_img = full_img.transpose([2, 1, 0])[None, ...]
        full_img = torch.from_numpy(full_img)
        full_img = full_img / 128 - 1

        img = cv2.resize(org_img, (target_dim1, target_dim0), interpolation=cv2.INTER_CUBIC)
        img = img.astype(np.float32)
        img = img.transpose([2, 1, 0])[None, ...]
        img = torch.from_numpy(img)
        img = img / 128 - 1

        e2e_input = {
            'resized_img': img,
            'full_img': full_img,
            'resize_scale': 1.0 / s,
            'len_label': len_label,
        }
        try:
            with torch.no_grad():
                out = e2e.forward(e2e_input, mode=mode)
        except RuntimeError as e:
            if 'CUDA out of memory' in str(e):
                e2e.to_cpu()
                with torch.no_grad():
                    out = e2e.forward(e2e_input, lf_batch_size=100, mode=mode)
                e2e.to_cuda()
            else:
                raise e
        out = e2e_postprocessing.results_to_numpy(out)

        if out is None:
            print('No Results')
            continue

        # take into account the padding
        out['sol'][:, :2] = out['sol'][:, :2] - pad_amount
        for line in out['lf']:
            line[:, :2, :2] = line[:, :2, :2] - pad_amount

        out['image_path'] = image_path

        out_name = os.path.basename(image_path)
        fill_out_name = os.path.join(output_directory, out_name)
        np.savez_compressed(fill_out_name + '.npz', **out)

        del img, full_img, out
        torch.cuda.empty_cache()
        progress_bar.step()


if __name__ == '__main__':
    if len(sys.argv) > 4 and sys.argv[4] == 'hw':
        from utils.continuous_state import init_model
        process(sys.argv[1], sys.argv[2], sys.argv[3], 'hw')
    else:
        from hw_vn.continuous_state import init_model
        process(sys.argv[1], sys.argv[2], sys.argv[3], 'hw_vn')
