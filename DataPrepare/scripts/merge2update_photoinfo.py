import os
import os.path as osp
import sys
import argparse
import json
import pickle as pkl
def prepareTestContext():
    if __name__ == "__main__":
        PROJROOT = osp.dirname(osp.dirname(osp.abspath(__file__)))
        sys.path.insert(0,PROJROOT)
prepareTestContext()
PROJROOT = osp.dirname(osp.dirname(osp.abspath(__file__)))
from flickr import *
from downloader import Downloader
from queue import Queue, Empty
from concurrent import futures
from threading import Thread, Lock
import time


## By default, the script will use the group id(s) specified in the configure file. For
## each group, the script tries to merge photo infos and faves.
## The script loads prepared GID.info and GID.faves and update photo info with faves.
## Only photo whose info and faves are both available is processed and its updated info is serialized
## into file `GID.info_alpha`, one line per photo.
##
## Files:
## GID.info, photo infos, one item per line
## GID.faves, photo faves, one item per line
## GID.info_alpha, updated photo info with faves
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Photo Infos for Photos in the Pool of Flickr Groups")
    parser.add_argument("-G", "--groups", action='append', default=[], help="specify the id of target groups")
    args = parser.parse_args()
    interact = len(args.groups)>0
    groups = args.groups if interact else [osp.basename(osp.dirname(g)) for g in config['groups'].values()]
    groups = list(set(groups)) # del repeat groups
    assets = os.path.join(PROJROOT, "assets")
    for g in groups:
        print("processing group: %s" % g)
        info_file = os.path.join(assets, g, '%s.info'%g)
        infos = {}
        with open(info_file) as f:
            for line in f:
                line=line.strip()
                if len(line)<1: continue
                _info = json.loads(line)
                infos.update({_info["id"]: _info})
        print("processing group: %d infos in %s"%(len(infos), g))
        faves_file = os.path.join(assets, g, '%s.faves'%g)
        faves = {}
        with open(faves_file) as f:
            for line in f:
                line=line.strip()
                if len(line)<1: continue
                _faves = json.loads(line)
                faves.update({_faves["id"]: _faves})
        print("processing group: %d faves in %s"%(len(faves),g))
        intersection = set(infos.keys()).intersection(set(faves.keys()))
        if len(intersection)<1: 
            print("processing group: no valid infos and faves in %s, abort"%g)
            continue
        # selected = dict(zip(intersection, [1]*len(intersection)))
        with open(os.path.join(assets,g,'%s.info_alpha'%g),'w') as f:
            for i in intersection:
                _info = infos[i]
                _info.update({"faves":{"person":faves[i]["person"]}})
                json.dump(_info, f)
                f.write("\n")
        print("processing group: %s done"%(g))