import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict
from scipy.spatial.distance import pdist
from scipy.spatial.distance import squareform

from collections import defaultdict
from sklearn.cluster import SpectralClustering
import scipy.io as sio
import os

from time import time

import sys
prob_thre = 1e-16
dec_thre = 0.038
num_vertex = 7455

def makeInitCluster():
    adjacency_matrix = readW()
    sc = SpectralClustering(20, affinity='precomputed', n_init=100, assign_labels='discretize')
    label_list = sc.fit_predict(adjacency_matrix)
    
    with open('data/cluster_rst.txt', 'w') as f:
        for v_idx, label in enumerate(label_list):
            f.write('%d %d\n' % (v_idx, label))

# implement equation 1
# A: d*d, x: d*1, y: d*1
def a_x_y(tmp_x_A, y):
    return np.matmul(tmp_x_A, y)

def fast_a_x_y(tmp_x_A, y):
    #import pdb; pdb.set_trace()
    return tmp_x_A[0][y]

# implement equation 9
# A: d*d, x: d*1
def evolve_x(label, x, A, times):

    count = 0
    while True:
        t0 = time()
        tmp_x_A = np.matmul(np.transpose(x), A)
        tmp_lam = a_x_y(tmp_x_A, x)
        
        flag = True

        difference = []
        for v_id, value in enumerate(x):
            if value > prob_thre and fast_a_x_y(tmp_x_A, v_id) > tmp_lam:
                difference.append(fast_a_x_y(tmp_x_A, v_id) - tmp_lam)
        if np.mean(difference) > dec_thre:
            x = x * np.matmul(A, x) / tmp_lam
            
            flag = False
        
        print("np.sum(x):%.4f"%np.sum(x))        
        t1 = time()
        if count % 50 == 0:
            print('label: %d, times:%d, try %d, cost:%.4fs' % (label, times, count, t1-t0))
            print(np.mean(difference))
        count += 1

        if flag:
            return x, tmp_x_A

def is_mode(tmp_x_A, x, A):
    t0 = time()
    g_x = a_x_y(tmp_x_A, x)

    for v_id in range(num_vertex):
        if x[v_id] < prob_thre:
            #print(v_id)
            if fast_a_x_y(tmp_x_A, v_id) > g_x:
                t1 = time()
                print('is_mode v_id:%d, value:%.4f, cost:%.4fs' % (v_id, fast_a_x_y(tmp_x_A, v_id) - g_x, t1-t0))
                return False
    return True

# implement equation 10 and calculate s, zeta, omega
def get_all_vertex_values(tmp_x_A, x, A):
    vertex_vector = np.zeros((num_vertex, 1))

    g_x = a_x_y(tmp_x_A, x)

    for v_id in range(num_vertex):
        if x[v_id] > prob_thre:
            vertex_vector[v_id] = 0.0
        else:
            vertex_vector[v_id] = max(fast_a_x_y(tmp_x_A, v_id) - g_x, 0)
    #pdb.set_trace()
    s = np.sum(vertex_vector)
    zeta = np.sum(vertex_vector**2)

    tmp_x_A = np.matmul(np.transpose(vertex_vector), A)
    omega = a_x_y(tmp_x_A, vertex_vector)

    t = min(1.0/s, zeta/(g_x*s*s+2*s*zeta-omega))
    
    if s == 0:
        import pdb; pdb.set_trace()

    return s, t, vertex_vector

# implement equation 12
def compute_delta_x(tmp_x_A, x, A):
    s, t, vertex_vector = get_all_vertex_values(tmp_x_A, x, A)

    delta_x = np.zeros((num_vertex,1))
    for v_id in range(num_vertex):
        if x[v_id] > prob_thre:
            delta_x[v_id] = (0 - x[v_id] * s) * t
        else:
            delta_x[v_id] = vertex_vector[v_id] * t
    return delta_x


def cluster():
    cluster_dict = defaultdict(set)
    
    f = open('data/cluster_rst.txt')
    for line in f:
        tmp = line.strip('\n').split(' ')
        v_id, label = int(tmp[0]), int(tmp[1])
        cluster_dict[label].add(v_id)
    
    cluster_vector = {}
    for label, values in cluster_dict.items():
        x = np.zeros((num_vertex, 1))
        for v_id in range(num_vertex):
            if v_id in values:
                x[v_id] = 1.0 / len(values)
        cluster_vector[label] = x

    return cluster_vector

def readW():
	data = sio.loadmat('data/kldiv.mat')
	W = data['dist']
		
	W = np.exp(-W)
	for vid in range(num_vertex):
		W[vid, vid] = 0
	
	return W
	

if __name__ == "__main__":
    import pdb
    makeInitCluster()
    
    A = readW()
    cluster_vector = cluster()
    cluster_rst = open('data/graphshift_output.txt', 'w')

    vertex_set = set()
    count  = 0
    for label in set(range(20)):
        times = 0
        x = cluster_vector[label]
        x, tmp_x_A = evolve_x(label, x, A, times)
        while not is_mode(tmp_x_A, x, A): 
            times += 1
            delta_x = compute_delta_x(tmp_x_A, x, A)
            x += delta_x
            x, tmp_x_A = evolve_x(label, x, A, times)
        cluster_vector[label] = x
        for v_id, prob in enumerate(x):
            if prob > prob_thre:
                vertex_set.add(v_id)
        print('num of vertex:%d' % (len(vertex_set)))
    for label, value in cluster_vector.items():
        for v_id in range(num_vertex):
            if value[v_id] > prob_thre:
                cluster_rst.write('%d %d\n' % (v_id, label))
                vertex_set.add(v_id)
    cluster_rst.close()


