#! python3
import os
import sys
import cv2
import pdb
import argparse
import pickle
import numpy
import numpy as np
from tqdm import tqdm
from time import time
from sklearn.cluster import KMeans
from queue import Queue, Empty
import threading
import multiprocessing
#
import color_harmonization
import util
import importlib
importlib.reload(color_harmonization)
importlib.reload(util)


def texture(fname):
	oh,ph,ov,po = 0, 0, 0, 0
	img = cv2.imread(fname)
	gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	kernel_size = 5
	blur_gray = cv2.GaussianBlur(gray,(kernel_size, kernel_size),0)

	low_threshold = 50
	high_threshold = 150
	kernel = np.ones((5,5),np.uint8)
	edges = cv2.Canny(blur_gray, low_threshold, high_threshold)
	edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

	rho = 1  # distance resolution in pixels of the Hough grid
	theta = np.pi / 180  # angular resolution in radians of the Hough grid
	threshold = 80  # minimum number of votes (intersections in Hough grid cell)
	min_line_length = 100  # minimum number of pixels making up a line
	max_line_gap = 20  # maximum gap in pixels between connectable line segments
	line_image = np.copy(img) * 0  # creating a blank to draw lines on
	lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]),  min_line_length, max_line_gap)

	if lines is not None:
		if len(lines)>0:
			N = lines.shape[0]
			for i in range(N):
				x1 = lines[i][0][0]
				y1 = lines[i][0][1]    
				x2 = lines[i][0][2]
				y2 = lines[i][0][3] 
				k = (y2-y1)/(x2-x1+ 0.001)
				if (k > 1 or k < -1):  # vertical line
					oh += k
					ph += (x2+x1)/2
				else:   # horizontal line
					ov += k
					po += (y2+y1)/2
	return (oh,ph,ov,po)

def multi_thread_callback(_idx, queue, extra, mutex, pbar):
	while True:
		with mutex:
			idx = extra[0] - 1 
			extra[0] -= 1
		if idx<0: break
		try:
			with mutex:
				pbar.update()
			_, gid, uid, pid, _  = queue[idx]
			imgfile = os.path.join('..','assets', gid, 'images', '%s.jpg'%pid)
			# print("Thread %d: processing %s" %(_idx, imgfile))
			if not os.path.isfile(imgfile):
				#print("Thread %d: file not found, %s"%(_idx, toc-tic, imgfile))
				continue
			extra[1][idx] += numpy.array(texture(imgfile))
		except Empty as e:
			pass


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="")
  parser.add_argument("-e", "--exp", type=str, default='', help="the current experiment name, default NULL")
  args = parser.parse_args()
  workspace = "20200520" if len(args.exp)<1 else args.exp
	pkl_file = os.path.join('..', workspace, 'selected_usr.pkl')
	assert os.path.isfile(pkl_file)
	with open(pkl_file, 'rb') as f:
		mapping = pickle.load(f)
	mapping['uid2idx'] = dict(zip(mapping['users'], range(len(mapping['users']))))

	queue = []
	pool = []
	for gid, _gc in mapping['gid2user'].items():
		for uid, _uc in _gc.items():
			for _ic in _uc:
				queue.append(_ic)
	queue_size = len(queue)
	texture_feats = np.zeros((queue_size, 4))
	args_extra = [queue_size, texture_feats]
	# DONOT USE MULTIPROCESS, THERE EXISTS BUGS CURRENTLY. ALWAYS USE MULTITHREAD
	fn_lock, fn_worker, fn_callback = (threading.Lock, threading.Thread, multi_thread_callback)
	lock = fn_lock()
	with tqdm(total=queue_size) as pbar:
		for i in range(4): # multi thread/process
			t = fn_worker(target=fn_callback, args=(i,queue, args_extra, lock, pbar,))
			pool.append(t)
		for t in pool:
			if isinstance(t, threading.Thread): t.setDaemon(True)
			t.start()
		for t in pool:
			t.join()
	print("processing texture done.")
	kmeans_cluster_size = 15
	kmeans = KMeans(n_clusters=kmeans_cluster_size, random_state=0).fit(texture_feats)
	print("kmeans clustering done.")
	onehot = np.eye(kmeans_cluster_size, dtype=np.int)[kmeans.labels_]
	mapping['photos'] = queue
	mapping['photos_texture'] = texture_feats
	mapping['photos_kmean_label'] = kmeans.labels_
	mapping['photos_kmean_onehot'] = onehot
	# pdb.set_trace()
	usr_kmeans_hist = np.zeros((len(mapping['users']), kmeans_cluster_size),dtype=np.int)
	for i in range(queue_size):
		photo = queue[i]
		usr_kmeans_hist[mapping['uid2idx']['_'.join(photo[1:3])]] += onehot[i]
	mapping['kmeanhist'] = usr_kmeans_hist
	print("All done!")
	with open('../%s/usr_kmeans_hist.pkl'%workspace, 'wb') as f:
		pickle.dump(mapping, f)
	# pdb.set_trace()
	# for i in range(kmeans_cluster_size):
	# 	print(i, ':', usr_kmeans_hist[:,i].max())