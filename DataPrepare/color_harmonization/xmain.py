#! python3
import os
import sys
import cv2
import pdb
import argparse
import pickle
import numpy
from tqdm import tqdm
from time import time
from queue import Queue, Empty
import threading
import multiprocessing
#
import color_harmonization
import util
import importlib
importlib.reload(color_harmonization)
importlib.reload(util)


def getColorHarm(fname, size=None):
	"""Get color harmonization.

	Args:
	  fname: the image file name
	  size: if set, resize before getting color harmonization
	"""
	# pdb.set_trace()
	color_image = cv2.imread(fname, cv2.IMREAD_COLOR)
	if size is not None:
		height = float(color_image.shape[0])
		width  = float(color_image.shape[1])
		if height > width:
			height = height/width * size
			width = size
		else:
			width = width/height * size
			height = size
		color_image = cv2.resize(color_image, (int(width),int(height)), interpolation = cv2.INTER_AREA)

	HSV_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
	best_harmomic_scheme = color_harmonization.B(HSV_image)
	#print("Harmonic Scheme Type  : ", best_harmomic_scheme.m)
	#print("Harmonic Scheme Alpha : ", best_harmomic_scheme.alpha)
	return best_harmomic_scheme.m

def multi_thread_callback(_idx, queue, mapping, mutex, pbar):
	while True:
		if queue.empty(): break
		try:
			with mutex:
				item = queue.get(timeout=5)
				pbar.update()
			#item = queue.get(timeout=5)
			#pbar.update()
			# pdb.set_trace()
			_, gid, uid, pid, _  = item
			imgfile = os.path.join('..','assets', gid, 'images', '%s.jpg'%pid)
			# print("Thread %d: processing %s" %(_idx, imgfile))
			if not os.path.isfile(imgfile):
				#print("Thread %d: file not found, %s"%(_idx, toc-tic, imgfile))
				continue
			tic = time()
			ch = getColorHarm(imgfile, 64*2)
			toc = time()
			#print("Thread %d: getColorHarm cost %.4f seconds, %s"%(_idx, toc-tic, imgfile))
			_uid = '_'.join([gid, uid])
			uidx = mapping['uid2idx'][_uid]
			with mutex:
				mapping['huehist'][uidx] += numpy.array(mapping['hue_template']) == ch
			#mapping['huehist'][uidx] += numpy.array(mapping['hue_template']) == ch
		except Empty as e:
			pass



##HueTemplates = ["i","V","L","mirror_L","I","T","Y","X" ]
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="")
  parser.add_argument("-e", "--exp", type=str, default='', help="the current experiment name, default NULL")
  args = parser.parse_args()
  workspace = "20200520" if len(args.exp)<1 else args.exp	
  pkl_file = os.path.join('..', workspace, 'selected_usr.pkl')
	assert os.path.isfile(pkl_file)
	with open(pkl_file, 'rb') as f:
		mapping = pickle.load(f)
	
	queue = Queue(maxsize=0)
	pool = []
	HueTemplates = ["i","V","L","mirror_L","I","T","Y","X"]
	huehist = numpy.zeros((len(mapping['users']), len(HueTemplates)), dtype=numpy.int)
	mapping['uid2idx'] = dict(zip(mapping['users'], range(len(mapping['users']))))
	mapping['huehist'] = huehist
	mapping['hue_template'] = HueTemplates

	for gid, _gc in mapping['gid2user'].items():
		for uid, _uc in _gc.items():
			for _ic in _uc:
				queue.put(_ic)
	# DONOT USE MULTIPROCESS, THERE EXISTS BUGS CURRENTLY. ALWAYS USE MULTITHREAD
	fn_lock, fn_worker, fn_callback = (threading.Lock, threading.Thread, multi_thread_callback)
	lock = fn_lock()
	with tqdm(total=queue.qsize()) as pbar:
		for i in range(8): # multi thread/process
			t = fn_worker(target=fn_callback, args=(i,queue, mapping, lock, pbar,))
			pool.append(t)
		for t in pool:
			if isinstance(t, threading.Thread): t.setDaemon(True)
			t.start()
		for t in pool:
			t.join()
	print("All done!")
	# pdb.set_trace()
	with open('../%s/usr_hue_hist.pkl'%workspace, 'wb') as f:
		pickle.dump(mapping, f)
