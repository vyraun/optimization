from __future__ import division

import numpy as np

#===# Logging constants #===#
summaries_dir = '/tmp/logs'
save_path = 'models/model.ckpt'
save_freq = 50
summary_freq = 5

#===# Opt net constants #===#
rnn_types = ['rnn','gru','lstm']
rnn_type = rnn_types[1]
rnn_size = 20
num_rnn_layers = 1

#===# SNF constants #===#
k = 10 # Number of hyperplanes
m = 30 # Number of dimensions
var_size = 0.2

#===# Training constants #===#
batch_size = 250
seq_length = 10
num_iterations = 400
num_SNFs = 1000
osc_control = 0.05 ### unused
replay_mem_start_size = 5000
replay_memory_max_size = 100000
episode_length = 100
net_sync_freq = 150

grad_scaling_methods = ['none','full']
grad_scaling_method = grad_scaling_methods[0]

# Random noise is added to the loss of the SNF during training of the opt net.
loss_noise = 0#0.75
