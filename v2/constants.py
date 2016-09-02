from __future__ import division

import numpy as np

#===# Logging constants #===#
summaries_dir = '/tmp/logs'
save_path = 'models/model.ckpt'

log_file = 'tmp/a3c_log'
summary_freq = 500

#===# A3C constants #===#
num_threads = 8
local_t_max = 5 # repeat step size
entropy_beta = 0#1e-4 # entropy regularization constant 0.0001
max_time_steps = 1e7
discount_rate = 0.99

#===# RMSProp constants #===#
rmsp_alpha = 0.99 #0.99# decay parameter for the historical gradient
rmsp_epsilon = 1e-10 #0.1
### Learning rate should be a function of the loss/reward?
lr_high = 0.0001 # upper limit for learning rate
lr_low = 0.0001 # lower limit for learning rate
grad_norm_clip = 1.0
rmsp_momentum = 0.9

#===# Opt net constants #===#
use_rnn = True # Uses a feed-forward network if false
rnn_types = ['rnn','gru','lstm']
rnn_type = rnn_types[0]
rnn_size = 2
num_rnn_layers = 1 # unused

#===# SNF constants #===#
m = 10 # Number of dimensions
var_size = 0.2

grad_scaling_methods = ['none','scalar','full']
grad_scaling_method = grad_scaling_methods[0]
grad_scaling_factor = 0.1
p = 10.0

termination_prob = 0.003 # Can be used to control the trade-off between speed and the final loss.

# Random noise is computed each time the point is processed while training the opt net
grad_noise = 0.5 # Determines the size of the standard deviation. The mean is zero.