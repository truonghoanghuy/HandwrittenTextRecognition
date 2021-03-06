import json
import os
import sys

import torch
import yaml
from torch import nn
from torch.utils.data import DataLoader
import time

from hw_vn import cnn_attention_lstm
from hw_vn import hw_dataset
from hw_vn import hw_loss_function
from hw_vn import module_trainer
from hw_vn.hw_dataset import HwDataset
from utils.dataset_parse import load_file_list
from utils.dataset_wrapper import DatasetWrapper

# noinspection DuplicatedCode
if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        config = yaml.load(f)
    hw_network_config = config['network']['hw']
    char_set_path = hw_network_config['char_set_path']
    with open(char_set_path, encoding='utf8') as f:
        char_set = json.load(f)
    idx_to_char = {int(k): v for k, v in char_set['idx_to_char'].items()}
    train_config = config['training']
    batches_per_epoch = int(train_config['hw']['images_per_epoch'] / train_config['hw']['batch_size'])
    checkpoint_file_path = os.path.join(train_config['snapshot']['best_validation'], 'hw_vn_checkpoint.pt')
    model_file_path = os.path.join(train_config['snapshot']['best_overall'], 'hw_vn.pt')

    train_set_list = load_file_list(train_config['training_set'])
    train_dataset = HwDataset(train_set_list, char_set['char_to_idx'], augment=True,
                              img_height=hw_network_config['input_height'])
    train_dataloader = DataLoader(train_dataset, batch_size=train_config['hw']['batch_size'], shuffle=False,
                                  num_workers=0, collate_fn=hw_dataset.collate)
    train_dataloader = DatasetWrapper(train_dataloader, batches_per_epoch)

    eval_set_list = load_file_list(train_config['validation_set'])
    eval_dataset = HwDataset(eval_set_list, char_set['char_to_idx'], img_height=hw_network_config['input_height'],
                             random_subset_size=train_config['hw']['validation_subset_size'])
    eval_dataloader = DataLoader(eval_dataset, batch_size=train_config['hw']['batch_size'], shuffle=False,
                                 num_workers=0, collate_fn=hw_dataset.collate)

    dtype = torch.float32
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    hw = cnn_attention_lstm.create_model(hw_network_config).to(device)
    optimizer = torch.optim.Adam(hw.parameters(), lr=train_config['hw']['learning_rate'])
    criterion = nn.CTCLoss(reduction='sum', zero_infinity=True)


    def calculate_hw_train_loss(hw_model, input):
        return hw_loss_function.calculate_hw_loss(hw_model, input, dtype, device, criterion, idx_to_char, train=True)


    def calculate_hw_evaluate_loss(hw_model, input):
        return hw_loss_function.calculate_hw_loss(hw_model, input, dtype, device, criterion, idx_to_char, train=False)


    trainer = module_trainer.ModuleTrainer(hw, optimizer, calculate_hw_train_loss, calculate_hw_evaluate_loss,
                                           train_dataloader, eval_dataloader, checkpoint_file_path, model_file_path)
    resume = 'resume' in sys.argv

    start_time = time.time()
    trainer.train(resume=resume)
    diff = (time.time() - start_time) / 60
    print('--------------------------------------------------------------------------------')
    print('Total time for training: {} minutes'.format(diff))
