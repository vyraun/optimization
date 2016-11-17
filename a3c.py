from __future__ import division

import tensorflow as tf
import numpy as np

import threading
import signal
import argparse

from ac_network import A3CRNN
from a3c_training_thread import A3CTrainingthread
from rmsprop_applier import RMSPropApplier
from snf import SNF

from constants import num_threads, max_time_steps, \
	rmsp_epsilon, rmsp_momentum, rmsp_alpha, grad_norm_clip, \
	summary_freq, save_path

"""
rm nohup.out; nohup python -u a3c.py -s &
kill -INT 10160
"""
	
parser = argparse.ArgumentParser()
parser.add_argument('--save', '-s', dest='save_model', action='store_true')
parser.set_defaults(save=False)
args = parser.parse_args()

if args.save_model:
	print "Model will be saved"
else:
	print "Model will not be saved"
	
print "Change\t\t Signed change\t\t Global time step"
	
# Globals
stop_requested = False	
global_t = 0
num_trainable_vars = [None]
graph = tf.Graph()

	
# Stops memory leaks from unterminated threads
# along with signal.pause() and signal.signal(...)
def signal_handler(signal, frame): ### signal and frame seem to be unused
	global stop_requested
	print 'Requesting stop'
	stop_requested = True
	
	
def train_function(parallel_index):
	global global_t
	global graph
	train_thread_class = train_thread_classes[parallel_index]
	snf_loss_changes = []
	signed_snf_loss_changes = []
	count = 0 # Unlike global_t, count is thread-specific

	while True:
		count += 1
		if stop_requested:
			break
		
		if global_t > max_time_steps:
			print "thread %d reached max steps" % parallel_index
			return
		
		diff_global_t, loss_change, _ = train_thread_class.thread(sess, global_t)
		snf_loss_changes.append(loss_change) # Average over local_t_max steps
		signed_snf_loss_changes.append(np.sign(loss_change))
		global_t += diff_global_t
		
		# Printing for each thread separately allows synchronization and 
		# divergence between the threads to be detected
		if count % summary_freq == 0:
			print "{:>10.3}{:>10.4}{:>15}{:>5}".format(np.mean(snf_loss_changes), np.mean(signed_snf_loss_changes), global_t, parallel_index)
			snf_loss_changes = []
			signed_snf_loss_changes = []
			
			
with graph.as_default(), tf.Session() as sess:
	
	global_network = A3CRNN(num_trainable_vars)		
	learning_rate_input = tf.placeholder("float")

	grad_applier = RMSPropApplier(learning_rate = learning_rate_input,
									decay = rmsp_alpha,
									momentum = rmsp_momentum,
									epsilon = rmsp_epsilon,
									clip_norm = grad_norm_clip)
				
	train_threads = []
	train_thread_classes = []	
	snf = SNF()

	for i in range(num_threads):
		train_thread_class = A3CTrainingthread(i, global_network,
											learning_rate_input, grad_applier, num_trainable_vars, snf, sess)							
		train_thread_classes.append(train_thread_class)
		train_threads.append(threading.Thread(target=train_function, args=(i,)))
		
	init = tf.initialize_all_variables()
	sess.run(init)

	signal.signal(signal.SIGINT, signal_handler)
		
	for t in train_threads:
		t.start()
		
	signal.pause()
		
	for t in train_threads:
		t.join()

	# Save model
	if args.save_model:
		saver = tf.train.Saver(tf.trainable_variables())
		saver.save(sess, save_path)
		print "Model saved"
	