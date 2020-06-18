import os
import os.path as osp
import sys
import csv
import argparse
import random
import json
import yaml
import pdb
import shutil
import logging
import pickle as pkl
import numpy as np
from ast import literal_eval
from datetime import datetime
def prepareTestContext():
    if __name__ == "__main__":
        PROJROOT = osp.dirname(osp.dirname(osp.abspath(__file__)))
        sys.path.insert(0,PROJROOT)
prepareTestContext()
PROJROOT = osp.dirname(osp.dirname(osp.abspath(__file__)))
from flickr import *



"""
Output:
- mapping.pkl:  
- usr_tag_hist.pkl:  
- selected_usr.pkl:  
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-G", "--groups", action='append', default=[], help="specify the id of target groups, default config['groups']")
    parser.add_argument("-e", "--exp", type=str, default='', help="the current experiment name, default NULL")
    args = parser.parse_args()
    interact = len(args.groups)>0
    groups = args.groups if interact else [osp.basename(osp.dirname(g)) for g in config['groups'].values()]
    groups = set(groups) # del repeat groups
    assets = os.path.join(PROJROOT, "assets")
    exp = os.path.join(PROJROOT, "20200520" if len(args.exp)<1 else args.exp)
    if not os.path.isdir(exp):
        os.makedirs(exp)
    #
    logger = logging.getLogger("20200520")
    logger.setLevel(logging.DEBUG)
    strHandler = logging.StreamHandler()
    strHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)-8s - %(levelname)-6s - %(message)s'))
    logger.addHandler(strHandler)
    fileHandler = logging.FileHandler(os.path.join(exp, 'log_%s.txt'%(datetime.now().strftime('%Y%m%d%H%M%S'))))
    fileHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)-8s - %(levelname)-6s - %(message)s'))
    logger.addHandler(fileHandler)
    #
    step = 1
    maps = None
    logger.info("++++++++++++++++++++++++++++")
    logger.info("==> Step %d: check working context"%step)
    if os.path.isfile(os.path.join(exp, 'mapping.pkl')):
        logger.info('existing maps found')
        logger.info('loading existing maps')
        with open(os.path.join(exp, 'mapping.pkl'), 'rb') as f:
            maps = pkl.load(f)
        if len(groups.difference(maps['groups']))>0:
            logger.warning('maps dismatch: %s in maps VS %s'%(list(maps['groups']), list(groups)))
            logger.info('existing maps are dropped because dismatch')
            maps = None
    step += 1
    #
    if maps is None:
        maps = dict(gid2items = {},
                    uid2usr = {},
                    tid2tag = {},
                    groups = groups)
        logger.info("++++++++++++++++++++++++++++")
        logger.info("==> Step %d: data processing" %step)
        for g in groups:
            logger.info("processing group: %s"%g)
            _file = osp.join(assets, g, "%s.info_alpha"%(g))
            assert(os.path.isfile(_file)), "run merge2update_photoinfo.py to create %s first"%(_file)
            _items = []
            _usr2photo = {}
            _tag2photo = {}
            n=0
            with open(_file) as f:
                for _line in f:
                    _line = _line.strip()
                    if len(_line) < 1: continue
                    _info = json.loads(_line)
                    _pid = _info['id']
                    _uid = _info['owner']['nsid']
                    _gid = g
                    _tids = tuple(x['id'].split('-')[-1] for x in _info['tags']['tag'])
                    _item = (n, _gid, _uid, _pid, _tids)
                    _items.append(_item)
                    if _uid not in _usr2photo: _usr2photo[_uid] = []
                    _usr2photo[_uid].append(_item)
                    if _uid not in maps['uid2usr']:
                        maps['uid2usr'][_uid] = _info['owner']
                    for _tag in _info['tags']['tag']:
                        _tid = _tag['id'].split('-')[-1]
                        if _tid not in _tag2photo: _tag2photo[_tid]=[]
                        _tag2photo[_tid].append(_item)
                        if _tid not in maps['tid2tag']:
                            maps['tid2tag'][_tid] = _tag
                    n += 1
            logger.debug("processing group: %s, found %d photos, %d users and %d tags"%(g, len(_items),len(_usr2photo),len(_tag2photo)))
            maps['gid2items'][g] = {'items':_items, 'usr2items':_usr2photo, '_tag2items': _tag2photo}
            logger.info("processing group: %s, done"%g)
        with open(os.path.join(exp, 'mapping.pkl'), 'wb') as f:
            pkl.dump(maps, f)
        step += 1
    
    #
    if True:
        # pdb.set_trace()
        topk = 117
        logger.info("++++++++++++++++++++++++++++")
        logger.info("==> Step %d: find top %d tags"%(step, topk))
        tags = {}
        for gid, _gc in maps['gid2items'].items():
            for tid, _tc in _gc['_tag2items'].items():
                tags[tid] = tags.get(tid, 0) + len(_tc)
        k, v = zip(*tags.items())
        k = np.array(k)
        v = np.array(v)
        _argsort = np.argsort(v)[::-1]
        tags = dict(zip(k[_argsort], v[_argsort]))
        tags2idx = dict(zip(k[_argsort], range(len(tags))))
        topktids = k[_argsort[:topk]]
        logger.info("show top %d tags: \n %s"%(topk,topktids))
        # topktids = set(topktids) # Attention!!
        step += 1

        #
        logger.info("++++++++++++++++++++++++++++")
        logger.info("==> Step %d: build user-tag histogram"%(step))
        users = {}
        for gid, _gc in maps['gid2items'].items():
            for uid, _uc in _gc['usr2items'].items():
                users[uid] = users.get(uid, 0) + len(_uc)
        k, v = zip(*users.items())
        k = np.array(k)
        v = np.array(v)
        _argsort = np.argsort(v)[::-1]
        users = dict(zip(k[_argsort], v[_argsort]))
        users2idx = dict(zip(k[_argsort], range(len(users))))
        usr_tag_hist = np.zeros((len(users), len(topktids)), dtype=np.int)
        for gid, _gc in maps['gid2items'].items():
            for uid, _uc in _gc['usr2items'].items():
                for _ic in _uc:
                    for tid in _ic[4]:
                        if tid not in topktids: continue
                        usr_tag_hist[users2idx[uid], tags2idx[tid]] += 1
        with open(os.path.join(exp,'usr_tag_hist.pkl'), 'wb') as f:
            pkl.dump({'users':users,'usr2idx':users2idx, 'tags':tags, 'tag2idx': tags2idx, 'selected':topktids, 'usrTagHist': usr_tag_hist},f)
        step += 1

    #
    if True:
        # pdb.set_trace()
        seleck = 500
        logger.info("++++++++++++++++++++++++++++")
        logger.info("==> Step %d: select users together with their photos"%(step))
        selected_usr = []
        selected_item = {}
        gid2usrnum = dict(map(lambda x: (x[0], len(x[1]['usr2items'])), maps['gid2items'].items()))
        k, v = zip(*gid2usrnum.items())
        k = np.array(k)
        v = np.array(v)
        _argsort = np.argsort(v)#[::-1]
        for i in _argsort: # from group who has the least user
            gid = k[i]
            num = v[i]
            # excluding joint users
            # if set(maps['gid2items'][gid]['usr2items']).isdisjoint(set(selected_usr)):
            #     selected_item[gid] = dict(random.sample(list(maps['gid2items'][gid]['usr2items'].items()), seleck)) if num > seleck else maps['gid2items'][gid]['usr2items']
            # else:
            #     _diff_key = set(maps['gid2items'][gid]['usr2items']).difference(set(selected_usr))
            #     _selected_key = random.sample(_diff_key, seleck) if len(_diff_key) > seleck else _diff_key
            #     selected_item[gid] = dict(map(lambda x: (x, maps['gid2items'][gid]['usr2items'][x]), _selected_key))
            # selected_usr.extend(selected_item[gid])
            # including joint users
            selected_item[gid] = dict(random.sample(list(maps['gid2items'][gid]['usr2items'].items()), seleck)) if num > seleck else maps['gid2items'][gid]['usr2items']
            selected_usr.extend(list(map(lambda x: '_'.join(x), zip([gid]*len(selected_item[gid]),selected_item[gid]))))
        with open(os.path.join(exp, 'selected_usr.pkl'), 'wb') as f:
            pkl.dump({'users': selected_usr, 'gid2user': selected_item}, f)
        step += 1

        if False:
            # Get user-color_harmonization histgram
            # pdb.set_trace()
            pass

    #
    if True:
        # pdb.set_trace()
        logger.info("++++++++++++++++++++++++++++")
        logger.info("==> Step %d: print ananlysis information"%(step))
        # find users that appear in more than one groups
        extend_users = []
        _groups = list(maps['groups'])
        while len(_groups) > 0:
            gid = _groups.pop()
            usr_in_G = set(maps['gid2items'][gid]['usr2items'])
            for _id in _groups:
                _intersec = usr_in_G.intersection(set(maps['gid2items'][_id]['usr2items']))
                if len(_intersec) < 1: continue
                extend_users.extend(_intersec)
        extend_users = set(extend_users)
        del _groups
        logger.info("---------------------------------")
        logger.info("groupID \t #user \t #user(+) \t #image \t #image(max) \t #image(min) \t #image(mean) \t sv")
        for gid, _gc in maps['gid2items'].items():
            num_usr = len(_gc['usr2items'])
            num_img = len(_gc['items'])
            num_per_usr = np.array(list(map(lambda x: len(x), _gc['usr2items'].values())))
            num_img_max = num_per_usr.max()
            num_img_min = num_per_usr.min()
            num_img_mean = num_per_usr.sum() // len(num_per_usr)
            num_img_std = num_per_usr.std()
            num_ext_usr = len(set(_gc['usr2items']).intersection(extend_users))
            logger.info("%s \t %d \t %d \t %d \t %d \t %d \t %d \t %.4f"%(gid, num_usr, num_ext_usr, num_img, num_img_max, num_img_min, num_img_mean, num_img_std))
        step += 1
    #
    logger.info("==> All done!")
    exit()