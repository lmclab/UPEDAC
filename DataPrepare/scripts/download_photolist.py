import os
import os.path as osp
import sys
import argparse
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

def worker(group, workers=2):
    """
    Download photo list in the photo pool of group.

    Args:\n
    - group: str, the id of target group.
    - workers: int, number of threads created for this task, default=2.
    """
    print(group, ": downloading photo list")
    pathname = osp.join(PROJROOT, "assets", group)
    filename = osp.join(pathname, group+".pkl")
    try:
        if not osp.isdir(pathname):
            print(group,": cannot find assets folder, run setup.py and try again")
            return
        if osp.isfile(filename):
            print(group, ": photo list file already existed, skipped")
            return
        status, photos = flickrGetGroupPhotoList(group, workers=workers)
        print(group, ": total", len(photos), "photos")
        with open(filename, "wb") as f:
            pkl.dump({"photos":photos}, f)
        print(group, ": succeeded")
    except Exception as e:
        if osp.isfile(filename):
            os.remove(filename)
        print(group, ": failed,", str(e))


## By default, the script will use the group id(s) specified in the configure file. For
## each group, the script tries to download photo lists (not the photo itself) in its 
## photo pool, skipping groups whose photo lists are downloaded already. Specifying target 
## groups (via -G gid0 -G gid1) to process customized groups rather than all the groups 
## in the configure file which is the default situation.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Photo Lists (not photo) in the Pool of Flickr Groups")
    parser.add_argument("-G", "--groups", action='append', default=[], help="specify the id of target groups")
    parser.add_argument("-n", "--workers", type=int, default=4, help="number of threads, default 4")
    args = parser.parse_args()
    interact = len(args.groups)>0
    groups = args.groups if interact else [osp.basename(osp.dirname(g)) for g in config['groups'].values()]
    groups = list(set(groups)) # del repeat groups
    pool = []
    # start one thread for each group
    for gid in groups:
        task = Thread(target=worker, args=(gid,), kwargs=dict(workers=args.workers))
        task.setDaemon(True)
        task.start()
        pool.append(task)
    # wait until all threads terminate
    for t in pool:
        t.join()
        