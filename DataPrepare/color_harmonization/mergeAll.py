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
#


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="")
	parser.add_argument("-e", "--exp", type=str, default='', help="the current experiment name, default NULL")
	args = parser.parse_args()
	workspace = "20200520" if len(args.exp)<1 else args.exp
	usr_tag_pkl = os.path.join('..', workspace, 'usr_tag_hist.pkl')
	usr_hue_pkl = os.path.join('..', workspace, 'usr_hue_hist.pkl')
	usr_kmeans_pkl = os.path.join('..', workspace, 'usr_kmeans_hist.pkl')
	assert os.path.isfile(usr_tag_pkl)
	assert os.path.isfile(usr_hue_pkl)
	assert os.path.isfile(usr_kmeans_pkl)
	with open(usr_tag_pkl, 'rb') as f:
		usr_tag = pickle.load(f)
	with open(usr_hue_pkl, 'rb') as f:
		usr_hue = pickle.load(f)
	with open(usr_kmeans_pkl, 'rb') as f:
		usr_kmeans = pickle.load(f)
	# Prerequirements: users in groups are disjoint
	# pdb.set_trace()
	# assert len(usr_hue['users']) == len(usr_kmeans['users'])
	if False:
		num_users = len(usr_hue['users'])
		groups = []
		for gid, _gc in usr_hue['gid2user'].items():
			groups.append(gid)
		gid2idx = dict(zip(groups, range(len(groups))))
		#
		hue_feat_size = usr_hue['huehist'].shape[1]
		tag_feat_size = usr_tag['usrTagHist'].shape[1]
		kmeans_feat_size = usr_kmeans['kmeanhist'].shape[1]
		usr_feat_size = 2 + hue_feat_size + tag_feat_size + kmeans_feat_size
		usr_feat = np.zeros((num_users, usr_feat_size), dtype=np.int)
		for i in tqdm(range(num_users)):
			uid = usr_hue['users'][i]
			idx = usr_hue['uid2idx'][uid]
			_gid, _uid = uid.split('_')
			usr_feat[idx][0] = idx + 1
			usr_feat[idx][1] =  gid2idx[_gid] + 1
			usr_feat[idx][2:2+hue_feat_size] = usr_hue['huehist'][idx]
			usr_feat[idx][2+hue_feat_size:2+hue_feat_size+tag_feat_size] = usr_tag['usrTagHist'][usr_tag['usr2idx'][_uid]]
			usr_feat[idx][2+hue_feat_size+tag_feat_size:usr_feat_size] = usr_kmeans['kmeanhist'][idx]
		with open('../%s/usr_feat.pkl'%workspace, 'wb') as f:
			pickle.dump({'users':usr_hue['users'], 'uid2idx': usr_hue['uid2idx'], 'groups': groups, 'gid2idx': gid2idx, 'feat': usr_feat}, f)
		# pdb.set_trace()
	else:
		users = list(set(map(lambda x: x.split('_')[1], usr_hue['users']))) # unique users
		uid2idx = dict(zip(users, range(len(users))))
		groups = []
		for gid, _gc in usr_hue['gid2user'].items():
			groups.append(gid)
		gid2idx = dict(zip(groups, range(len(groups))))
		num_groups = len(groups)
		num_users = len(users)
		onehotG = np.eye(num_groups, dtype=np.int)
		hue_feat_size = usr_hue['huehist'].shape[1]
		tag_feat_size = usr_tag['usrTagHist'].shape[1]
		kmeans_feat_size = usr_kmeans['kmeanhist'].shape[1]
		usr_feat_size = 1 + num_groups + hue_feat_size + tag_feat_size + kmeans_feat_size
		usr_feat = np.zeros((num_users, usr_feat_size), dtype=np.int)
		for uid in tqdm(usr_hue['users']):
			_idx = usr_hue['uid2idx'][uid]
			_gid, _uid = uid.split('_')
			idx = uid2idx[_uid]
			usr_feat[idx][0] = idx + 1
			usr_feat[idx][1:1+num_groups] +=  onehotG[gid2idx[_gid]]
			usr_feat[idx][1+num_groups:1+num_groups+hue_feat_size] += usr_hue['huehist'][_idx]
			usr_feat[idx][1+num_groups+hue_feat_size:1+num_groups+hue_feat_size+tag_feat_size] = usr_tag['usrTagHist'][usr_tag['usr2idx'][_uid]]
			usr_feat[idx][1+num_groups+hue_feat_size+tag_feat_size:usr_feat_size] += usr_kmeans['kmeanhist'][_idx]
		with open('../%s/unique_usr_fusionfeat.pkl'%workspace, 'wb') as f:
			pickle.dump({'users':users, 'uid2idx': uid2idx, 'groups': groups, 'gid2idx': gid2idx, 'feat': usr_feat}, f)
		# pdb.set_trace()