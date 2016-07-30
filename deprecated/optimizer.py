from __future__ import division
from tensorflow.examples.tutorials.mnist import input_data
from tensorflow.python.ops import control_flow_ops
import tensorflow as tf
import numpy as np

"""
Input: Gradients
Output: Change in parameters (exp transform to reverse scaling?)
Loss: Change in loss

tensorboard --logdir=/tmp/logs ./ --host 0.0.0.0
http://ec2-52-48-79-131.eu-west-1.compute.amazonaws.com:6006/
"""

summary_freq = 100
summaries_dir = '/tmp/logs'
test_evaluation = True
#rnn = False # feed-forward otherwise
#rnn_num_layers = 1
#rnn_size = 5
seq_length = 1
grad_clip_value = None # Set to None to disable

grad_scaling_methods = ['scalar','full']
grad_scaling_method = grad_scaling_methods[1]
grad_scaling_factor = 0.1
p = 10.0

#test_mlp_sigmoid = False
#test_mlp_relu = False
#test_mlp_elu = False
#test_mnist_cnn = False
#test_lstm = False
#test_pong_a3c = False

class MLP:
	def __init__(self):
		self.batch_size = 1 # 128
		self.batches = 1000

		# Define architecture
		self.x = tf.placeholder(tf.float32, [None, 784])
		self.y_ = tf.placeholder(tf.float32, [None, 10])
		
		self.W = tf.Variable(tf.truncated_normal(stddev=0.1, shape=[784,10]))
		self.b = tf.Variable(tf.constant(0.1, shape=[10]))
		y = tf.nn.softmax(tf.matmul(self.x,self.W) + self.b)
		
		correct_prediction = tf.equal(tf.argmax(y,1), tf.argmax(self.y_,1))
		self.accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

		self.loss = tf.reduce_mean(-tf.reduce_sum(self.y_ * tf.log(y), reduction_indices=[1])) # Cross-entropy
		tf.scalar_summary('loss', self.loss)

		sgd_optimizer = tf.train.GradientDescentOptimizer(0.5)
		adam_optimizer = tf.train.AdamOptimizer()
		
		grad_var_pairs = sgd_optimizer.compute_gradients(self.loss)
		grads,vars = zip(*grad_var_pairs)
		grads = [tf.reshape(i,(-1,1)) for i in grads]
		
		if not grad_clip_value is None:
			grads = [tf.clip_by_value(g, -grad_clip_value, grad_clip_value) for g in grads]
			
		self.grads = tf.concat(0,grads)
		
		self.trainable_variables = tf.trainable_variables()
		
		self.sgd_train_step = sgd_optimizer.apply_gradients(grad_var_pairs)
		self.adam_train_step = adam_optimizer.apply_gradients(grad_var_pairs)

		self.init = tf.initialize_all_variables()
	
	
	def init_optimizer_ops(self):
		input = self.grads
		input = tf.reshape(input,[1,-1,1]) ### check

		input = scale_grads(input)
		
		### All repeated in opt_net, although the variables are taken from there
		### Share code - activations functions could become different
		# Apply gradient update from the opt-net
		h = tf.nn.relu(tf.batch_matmul(input,opt_net.W1_1) + opt_net.b1)
		h = tf.nn.relu(tf.batch_matmul(h,opt_net.W2_1) + opt_net.b2) # Gradients
		
		# Apply gradients to the parameters in the train net.
		total = 0
		ret = []

		for i,v in enumerate(self.trainable_variables):
			size = np.prod(list(v.get_shape()))
			size = tf.to_int32(size)
			var_grads = tf.slice(h,begin=[0,total,0],size=[-1,size,-1])
			var_grads = tf.reshape(var_grads,v.get_shape())
			ret.append(v.assign_add(var_grads))
			size += total
		self.var_grads = input
		self.opt_net_train_step = control_flow_ops.group(*ret)		
		
	def fc_layer(input, size, act=tf.nn.relu):
		W = tf.Variable(tf.random_uniform([size[0], size[1]])) ### check shape index, truncated normal
		b = tf.Variable(tf.zeros([size[1]])) ### constant
		h = act(tf.matmul(input,W) + b)
		return h

		
class OptNet:
	def __init__(self):
		self.epochs = 4
		batch_size = 1 ###
		feature_sizes = [1,4,1]
		assert feature_sizes[-1] == 1
		
		if grad_scaling_method == 'full':
			feature_sizes[0] = 2

		# Define architecture
		# Feed-forward
		self.x_grads = tf.placeholder(tf.float32, [None,None,1]) # input
		self.y_losses = tf.placeholder(tf.float32) ### batch?
		
		x = scale_grads(self.x_grads)
				
		self.W1 = tf.Variable(tf.truncated_normal(stddev=0.1, shape=[feature_sizes[0],feature_sizes[1]]))
		W1_1 = tf.reshape(self.W1,(-1,feature_sizes[0],feature_sizes[1])) # Convert from rank 2 to rank 3
		self.W1_1 = tf.tile(W1_1,(batch_size,1,1))
		self.b1 = tf.Variable(tf.constant(0.1, shape=[feature_sizes[1]]))

		h = tf.nn.relu(tf.batch_matmul(x,self.W1_1) + self.b1)

		self.W2 = tf.Variable(tf.truncated_normal(stddev=0.1, shape=[4,1]))
		W2_1 = tf.reshape(self.W2,(-1,feature_sizes[1],feature_sizes[2])) # Convert from rank 2 to rank 3
		self.W2_1 = tf.tile(W2_1,(batch_size,1,1))
		self.b2 = tf.Variable(tf.constant(0.1, shape=[feature_sizes[2]]))

		h = tf.nn.relu(tf.batch_matmul(h,self.W2_1) + self.b2) # Gradients
		
		# Apply gradients to the parameters in the train net.
		total = 0
		### Shouldn't hard-code the model to be updated
		### Use in the style of the inbuilt optimizers
		for i,v in enumerate(mlp.trainable_variables):
			size = np.prod(list(v.get_shape()))
			size = tf.to_int32(size)
			var_grads = tf.slice(h,begin=[0,total,0],size=[-1,size,-1])
			var_grads = tf.reshape(var_grads,v.get_shape())
			
			if not grad_clip_value is None:
				var_grads = tf.clip_by_value(var_grads, -grad_clip_value, grad_clip_value)

			v.assign_add(var_grads)
			size += total
		
		self.x = tf.placeholder(tf.float32, [None,784])
		self.y_ = tf.placeholder(tf.float32, [None,10])

		y = tf.nn.softmax(tf.matmul(self.x,mlp.W) + mlp.b)
		new_loss = tf.reduce_mean(-tf.reduce_sum(self.y_ * tf.log(y), reduction_indices=[1])) # Cross-entropy	
		
		# Change in loss as a result of the parameter update (ideally negative)
		self.loss = new_loss - self.y_losses
		
		self.train_step = tf.train.AdamOptimizer().minimize(self.loss)

		self.init = tf.initialize_all_variables()
	
	
	def fc_layer(self, input, size, act=tf.nn.relu):
		W = tf.Variable(tf.truncated_normal(stddev=0.1, shape=[size[0],size[1]]))
		W = tf.reshape(W,(-1,size[0],size[1])) # Convert from rank 2 to rank 3
		W = tf.tile(W,(self.num_batches,1,1))
		b = tf.Variable(tf.constant(0.1, shape=[size[1]]))
		h = act(tf.batch_matmul(input,W) + b)
		return h
		
	
def scale_grads(input):
	if grad_scaling_method == 'scalar':
		input = input*tf.constant(grad_scaling_factor)	
		
	elif grad_scaling_method == 'full':	
		p_ = tf.constant(p)
		grad_threshold = tf.exp(-p_)
	
		# Operations are element-wise
		mask = tf.greater(tf.abs(input),grad_threshold)
		mask = tf.to_float(mask) # Convert from boolean
		inv_mask = 1 - mask
		
		x1_cond1 = tf.log(tf.abs(input))/p_
		x2_cond1 = tf.sign(input)
		x1_cond2 = -tf.ones(tf.shape(input))
		x2_cond2 = tf.exp(p_)*input
		
		x1 = x1_cond1*mask + x1_cond2*inv_mask
		x2 = x2_cond1*mask + x2_cond2*inv_mask
		
		input = tf.concat(2,[x1,x2])
		
	return input
		
		
sess = tf.Session()		
		
mlp = MLP()
sess.run(mlp.init)

train_grads_list = []
train_losses_list = []
train_params_list = []

mnist = input_data.read_data_sets("MNIST_data/", one_hot=True)

# Create training data
print "\nCreating training dataset..."
for i in range(mlp.batches):
	batch_x, batch_y = mnist.train.next_batch(mlp.batch_size)
	# Train the batch, remembering the gradients and the loss
	tmp = sess.run([mlp.adam_train_step,mlp.loss,mlp.grads] + mlp.trainable_variables, feed_dict={mlp.x: batch_x, mlp.y_: batch_y})
	loss_,grads_ = tmp[1:3]
	params_ = tmp[3:]
	
	train_losses_list.append(loss_)
	train_grads_list.append(grads_)
	train_params_list.append(params_)
	
print(sess.run(mlp.accuracy, feed_dict={mlp.x: mnist.test.images, mlp.y_: mnist.test.labels}))

opt_net = OptNet()
mlp.init_optimizer_ops()
sess.run(opt_net.init)

sess.run(mlp.init) # reset variables for safety

# Train opt net
print "\nTraining optimizer..."
for epoch in range(opt_net.epochs):
	print "Epoch ", epoch

	# Leave room for the rest of the sequence at the end
	max_length = len(train_grads_list) - seq_length
	perm = np.random.permutation(range(max_length))
	losses = []

	for i in range(max_length):
		start = perm[i]
		end = start + seq_length
		train_grads_seq = train_grads_list[start:end]
		train_params = train_params_list[end]
		train_loss = train_losses_list[end]
		
		# Used to compute the change in the loss
		batch_x, batch_y = mnist.train.next_batch(mlp.batch_size)
		
		# Set params
		for j,v in enumerate(mlp.trainable_variables):
			v.assign(train_params[j])
		
		### Do in batches
		# Train the optimizer
		_,loss_ = sess.run([opt_net.train_step,opt_net.loss], 
							feed_dict={	opt_net.x_grads: train_grads_seq,
										opt_net.y_losses: train_loss,
										opt_net.x: batch_x,
										opt_net.y_: batch_y})

		#if i % summary_freq == 0:
		#	print loss_, i										
		losses.append(loss_)
	
	print np.mean(losses)

##### Compare optimizer performance using TensorBoard #####
# Optimizer parameters are now treated as fixed

if test_evaluation:
	print "\nRunning optimizer comparison..."

	if tf.gfile.Exists(summaries_dir):
		tf.gfile.DeleteRecursively(summaries_dir)
	tf.gfile.MakeDirs(summaries_dir)
	
	# Merge all the summaries and write them out to /tmp/mnist_logs (by default)
	merged = tf.merge_all_summaries()

	sgd_writer = tf.train.SummaryWriter(summaries_dir + '/sgd')
	adam_writer = tf.train.SummaryWriter(summaries_dir + '/adam')
	opt_net_writer = tf.train.SummaryWriter(summaries_dir + '/opt_net')

	# SGD
	sess.run(mlp.init)
	for i in range(mlp.batches):
		batch_x, batch_y = mnist.train.next_batch(mlp.batch_size)
		summary,_ = sess.run([merged, mlp.sgd_train_step], feed_dict={mlp.x: batch_x, mlp.y_: batch_y})
		sgd_writer.add_summary(summary,i)
		
	sgd_writer.close()
	
	# Adam
	sess.run(mlp.init)
	for i in range(mlp.batches):
		batch_x, batch_y = mnist.train.next_batch(mlp.batch_size)
		summary,_ = sess.run([merged, mlp.adam_train_step], feed_dict={mlp.x: batch_x, mlp.y_: batch_y})
		adam_writer.add_summary(summary,i)
		
	adam_writer.close()
	
	# Opt net
	sess.run(mlp.init) # Reset parameters of net to be trained
	for i in range(mlp.batches):
		batch_x, batch_y = mnist.train.next_batch(mlp.batch_size)
		### Two possible train steps here - should only be one
		summary,_,l = sess.run([merged, mlp.opt_net_train_step, mlp.var_grads], feed_dict={mlp.x: batch_x, mlp.y_: batch_y})
		#print l
		opt_net_writer.add_summary(summary,i)
	
	opt_net_writer.close()
	
