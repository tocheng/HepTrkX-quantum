# Calculates gradients of a pennylane quantum circuit
# using tensorflow
import sys, os, time, datetime, csv
sys.path.append(os.path.abspath(os.path.join('.')))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import pennylane as qml 
from pennylane import numpy as np
import tensorflow as tf
from datasets.hitgraphs import get_datasets


dev1 = qml.device("default.qubit", wires=8)
@qml.qnode(dev1,interface='tf')
def TTN_edge_forward(edge,theta_learn):
	# Takes the input and learning variables and applies the
	# network to obtain the output
	
	# STATE PREPARATION
	for i in range(8):
		qml.RY(edge[i],wires=i)
	# APPLY forward sequence
	# First Layer
	qml.RY(theta_learn[0],wires=0)
	qml.RY(theta_learn[1],wires=1)
	qml.CNOT(wires=[0,1])
	qml.RY(theta_learn[2],wires=2)
	qml.RY(theta_learn[3],wires=3)
	qml.CNOT(wires=[3,2])
	qml.RY(theta_learn[4],wires=4)
	qml.RY(theta_learn[5],wires=5)
	qml.CNOT(wires=[4,5])
	qml.RY(theta_learn[6],wires=6)
	qml.RY(theta_learn[7],wires=7)
	qml.CNOT(wires=[7,6])
	# Second Layer
	qml.RY(theta_learn[8],wires=1)
	qml.RY(theta_learn[9],wires=2)
	qml.CNOT(wires=[1,2])
	qml.RY(theta_learn[10],wires=5)
	qml.RY(theta_learn[11],wires=6)
	qml.CNOT(wires=[6,5])
	# Third Layer
	qml.RY(theta_learn[12],wires=2)
	qml.RY(theta_learn[13],wires=5)
	qml.CNOT(wires=[2,5])
	#Last Layer
	qml.RY(theta_learn[14],wires=5)		
	return qml.expval(qml.PauliZ(wires=5))

dev2 = qml.device("default.qubit", wires=12)
@qml.qnode(dev2,interface='tf')
def TTN_node_forward(edge,theta_learn):
	# Takes the input and learning variables and applies the
	# network to obtain the output
	
	# STATE PREPARATION
	for i in range(12):
		qml.RY(edge[i],wires=i)
	# APPLY forward sequence
	# First Layer
	qml.RY(theta_learn[0],wires=0)
	qml.RY(theta_learn[1],wires=1)
	qml.CNOT(wires=[0,1])
	qml.RY(theta_learn[2],wires=2)
	qml.RY(theta_learn[3],wires=3)
	qml.CNOT(wires=[3,2])
	qml.RY(theta_learn[4],wires=4)
	qml.RY(theta_learn[5],wires=5)
	qml.CNOT(wires=[4,5])
	qml.RY(theta_learn[6],wires=6)
	qml.RY(theta_learn[7],wires=7)
	qml.CNOT(wires=[7,6])
	qml.RY(theta_learn[8],wires=8)
	qml.RY(theta_learn[9],wires=9)
	qml.CNOT(wires=[8,9])
	qml.RY(theta_learn[10],wires=10)
	qml.RY(theta_learn[11],wires=11)
	qml.CNOT(wires=[11,10])
	# Second Layer
	qml.RY(theta_learn[12],wires=1)
	qml.RY(theta_learn[13],wires=2)
	qml.CNOT(wires=[1,2])
	qml.RY(theta_learn[14],wires=5)
	qml.RY(theta_learn[15],wires=6)
	qml.CNOT(wires=[6,5])
	qml.RY(theta_learn[16],wires=9)
	qml.RY(theta_learn[17],wires=10)
	qml.CNOT(wires=[10,9])	
	# Third Layer
	qml.RY(theta_learn[18],wires=2)
	qml.RY(theta_learn[19],wires=5)
	qml.CNOT(wires=[2,5])	
	# Forth Layer
	qml.RY(theta_learn[20],wires=5)
	qml.RY(theta_learn[21],wires=9)
	qml.CNOT(wires=[5,9])
	# Last Layer
	qml.RY(theta_learn[22],wires=4)		

	return qml.expval(qml.PauliZ(wires=9))
	#######################################
def edge_forward(edge_array,theta_learn):
	outputs = []
	for i in range(len(edge_array[:,0])):
		out = tf.constant((1-TTN_edge_forward(edge_array[i,:],theta_learn))/2.,dtype=tf.float64)
		outputs.append(out)
	return tf.stack(outputs)
def node_forward(node_array,theta_learn):
	outputs = []
	for i in range(len(node_array[:,0])):
		out = tf.constant((1-TTN_node_forward(node_array[i,:],theta_learn))/2.,dtype=tf.float64)
		outputs.append(out)
	return tf.stack(outputs)
def map2angle(B):
	# Maps input features to 0-2PI
	r_min     = 0.
	r_max     = 1.
	phi_min   = -1.
	phi_max   = 1.
	z_min     = 0.
	z_max     = 1.2
	B[:,0] =  (B[:,0]-r_min)/(r_max-r_min) * 2 * np.pi 
	B[:,1] =  (B[:,1]-phi_min)/(phi_max-phi_min) * 2 * np.pi 
	B[:,2] =  (B[:,2]-z_min)/(z_max-z_min) * 2 * np.pi 
	return B
############################################################################################
class EdgeNet(tf.keras.layers.Layer):
	def __init__(self,name):
		super(EdgeNet, self).__init__(name=name)
		#self.theta_learn = tf.Variable(np.random.rand(15) * np.pi * 2,dtype=tf.float64)
		self.theta_learn = tf.Variable(tf.random.uniform(shape=[15,],minval=0,maxval=np.pi*2,dtype=tf.float64))

	def call(self,X, Ri, Ro):
		bo = tf.matmul(Ro,X,transpose_a=True)
		bi = tf.matmul(Ri,X,transpose_a=True)
		B  = tf.concat([bo, bi], axis=1)  
		return edge_forward(B,self.theta_learn)

class NodeNet(tf.keras.layers.Layer):
	def __init__(self,name):
		super(NodeNet, self).__init__(name=name)
		#self.theta_learn = tf.Variable(np.random.rand(23) * np.pi * 2,dtype=tf.float64)
		self.theta_learn = tf.Variable(tf.random.uniform(shape=[23,],minval=0,maxval=np.pi*2,dtype=tf.float64))

	def call(self, X, e, Ri, Ro):

		bo  = tf.matmul(Ro, X, transpose_a=True) # n_edge x 4
		bi  = tf.matmul(Ri, X, transpose_a=True) # n_edge x 4
	
		#Rwo = tf.multiply(Ro, tf.reshape(e,[e.shape[0],1])) # n_node x 1 
		#Rwi = tf.multiply(Ri, tf.reshape(e,[e.shape[0],1])) # n_node x 1
		Rwo = tf.math.multiply(Ro,e)
		Rwi = tf.math.multiply(Ri,e)
		
		mi = tf.matmul(Rwi, bo)
		mo = tf.matmul(Rwo, bi)
		M = tf.concat([mi, mo, X], axis=1)
		return node_forward(M,self.theta_learn)

class InputNet(tf.keras.layers.Layer):
	def __init__(self, num_outputs,name):
		super(InputNet, self).__init__(name=name)
		self.num_outputs = num_outputs
		#self.kernel = tf.Variable(np.random.rand(3,num_outputs),dtype=tf.float64,trainable=True)
		self.kernel = tf.Variable(tf.random.uniform(shape=[3,self.num_outputs],minval=0,maxval=1.,dtype=tf.float64))

	'''
	def build(self, input_shape):
		self.kernel = self.add_variable("kernel",shape=[3,self.num_outputs],trainable=True)
	'''
	def call(self, arr):
		return tf.matmul(arr, self.kernel)

class GNN(tf.keras.Model):
	def __init__(self):
		super(GNN, self).__init__(name='GNN')
		self.InputNet0 = InputNet(1,name='InputNet0')
		self.EdgeNet0 = EdgeNet(name='EdgeNet0')
		self.NodeNet0 = NodeNet(name='NodeNet0')
		self.EdgeNet1 = EdgeNet(name='EdgeNet1')

	def call(self, edge_array):
		X,Ri,Ro = edge_array
		H = self.InputNet0(X) # not normalized, be careful !
		H = tf.concat([H,X],axis=1)
		e = self.EdgeNet0(H, Ri, Ro)
		H = self.NodeNet0(H, e, Ri, Ro)
		H = tf.concat([H[:,None],X],axis=1)
		e = self.EdgeNet1(H, Ri, Ro)
		return e

def binary_cross_entropy(label,output):
	return tf.tensordot(output,output,axes=1)
	#return - tf.tensordot(label,tf.math.log(output+1e-6)) - tf.tensordot((1-label),tf.math.log(1-output+1e-6)) 
def gradient(block,edge_array,label):
	with tf.GradientTape() as tape:
		loss = tf.keras.losses.binary_crossentropy(label,block(edge_array))
		print('Loss: %.3f' %loss)
	grad = tape.gradient(loss,block.trainable_variables)
	print(grad)
	return grad
############################################################################################

if __name__ == '__main__':
	tf.executing_eagerly()
	tf.keras.backend.set_floatx('float64')
	input_dir = 'data/hitgraphs_big'
	n_train = 2
	train_data, valid_data = get_datasets(input_dir, n_train, 2)
	block = GNN()

	opt = tf.keras.optimizers.Adam(learning_rate=0.01)

	for i in range(n_train):
		X, Ri, Ro, labels = train_data[i]
		labels = tf.constant(labels,dtype=tf.float64)
		X = tf.constant(map2angle(X),dtype=tf.float64)
		Ri = tf.constant(Ri,dtype=tf.float64)
		Ro = tf.constant(Ro,dtype=tf.float64)
		edge_array = [X,Ri,Ro]
		grads = gradient(block,edge_array,labels)
		opt.apply_gradients(zip(grads, block.trainable_variables))
	

	





