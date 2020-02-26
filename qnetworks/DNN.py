import numpy as np
import tensorflow as tf
#################################################
class EdgeNet(tf.keras.layers.Layer):
	def __init__(self,hid_dim,name):
		super(EdgeNet, self).__init__(name=name)
		self.network = tf.keras.Sequential([
            		tf.keras.layers.Dense(hid_dim,input_shape=((hid_dim+3)*2,),activation='tanh'),
            		tf.keras.layers.Dense(1,activation='sigmoid')
            		])
	def call(self,X, Ri, Ro):
		bo = tf.matmul(Ro,X,transpose_a=True)
		bi = tf.matmul(Ri,X,transpose_a=True)
		B  = tf.concat([bo, bi], axis=1)  
		return self.network(B)
#################################################
class NodeNet(tf.keras.layers.Layer):
	def __init__(self,hid_dim,name):
		super(NodeNet, self).__init__(name=name)
		self.network = tf.keras.Sequential([
            		tf.keras.layers.Dense(hid_dim,input_shape=((hid_dim+3)*3,),activation='tanh'),
            		tf.keras.layers.Dense(hid_dim,activation='sigmoid')
            		])
	def call(self, X, e, Ri, Ro):
		bo  = tf.matmul(Ro, X, transpose_a=True) # n_edge x 4
		bi  = tf.matmul(Ri, X, transpose_a=True) # n_edge x 4	
		Rwo = Ro * tf.transpose(e)
		Rwi = Ri * tf.transpose(e)
		mi = tf.matmul(Rwi, bo)
		mo = tf.matmul(Rwo,bi)
		M = tf.concat([mi, mo, X], axis=1)
		return self.network(M)
#################################################
class InputNet(tf.keras.layers.Layer):
	def __init__(self, num_outputs,name):
		super(InputNet, self).__init__(name=name)
		self.layer = tf.keras.layers.Dense(num_outputs,input_shape=(3,),activation='sigmoid')
	
	def call(self, arr):
		return self.layer(arr)
#################################################
class GNN(tf.keras.Model):
	def __init__(self, hid_dim=1, n_iters=2):
		super(GNN, self).__init__(name='GNN')
		self.InputNet = InputNet(hid_dim, name='InputNet')
		self.EdgeNet = EdgeNet(hid_dim, name='EdgeNet0')
		self.NodeNet = NodeNet(hid_dim, name='NodeNet')
		self.n_iters = n_iters

	def call(self, edge_array):
		X,Ri,Ro = edge_array
		H = self.InputNet(X) # not normalized, be careful !
		H = tf.concat([H,X],axis=1)
		e = self.EdgeNet(H, Ri, Ro)
		for i in range(self.n_iters):
			H = self.NodeNet(H, e, Ri, Ro)
			H = tf.concat([H,X],axis=1)
			e = self.EdgeNet(H, Ri, Ro)
		return e
#################################################
