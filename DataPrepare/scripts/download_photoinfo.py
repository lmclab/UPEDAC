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

# Globle 
PRODUCER_ACTIVE = 0
LOCK = Lock() # enqueueing locks 
GLOCKS = {} # dequeueing locks

def producer(queue, group):
    """
    Accept a queue and a group, load photo lists of the group and 
    enqueue photos whose info has not been downloaded or failed to
    be downloaded, so that the consumer can try them again.

    Args:\n
    - queue: Queue, the queue holding all the images whose infos we are interested.
    - groups: str, the id of the target group
    """
    global PRODUCER_ACTIVE
    global LOCK
    gid = group
    with LOCK:
        PRODUCER_ACTIVE += 1
    pathname = osp.join(PROJROOT, "assets", gid)
    photopool = osp.join(pathname, gid+".pkl")
    # logs about done and failure photos
    donelog = osp.join(pathname, gid+".info.log.done")
    faillog = osp.join(pathname, gid+".info.log.fail")
    try:
        if not osp.isdir(pathname):
            print(gid,": cannot find assets folder, run setup.py and try again")
            return
        if not osp.isfile(photopool):
            print(gid, ": photo list file missing, skipping ")
            print(gid, ": skipped")
            return
        donedict, faildict = {}, {}
        # load logs
        if osp.isfile(donelog):
            with open(donelog) as f:
                for line in f:
                    line = line.strip()
                    donedict[line] = 1
        if osp.isfile(faillog):
            with open(faillog) as f:
                for line in f:
                    line = line.strip()
                    faildict[line] = 1
        # load photo lists
        photos = []
        with open(photopool, "rb") as f:
            photos = pkl.load(f)['photos']
        for item in photos:
            iid = item['id']
            if donedict.get(iid, None):
                continue # skip if done
            item['gid'] = gid
            queue.put(item)
    finally:
        with LOCK:
            PRODUCER_ACTIVE -= 1
    

def consumer(queue):
    """
    Consume items in the queue.
    """
    global GLOCKS
    while True:
        # terminate consumer when producer are all done and the queue is empty
        if PRODUCER_ACTIVE<1 and queue.empty():
            break
        try:
            error = None
            item = queue.get(timeout=5)
            try:
                gid = item['gid']
                iid = item['id']
                print(gid, ": download photo information", iid)
                iinfo = flickrGetPhotoInfo(iid)
                with GLOCKS[gid]:
                    if iinfo is None: # failed
                        with open(osp.join(PROJROOT, "assets", gid, gid+".info.log.fail"), 'a') as f:
                            f.write(iid+"\n")
                        continue
                    with open(osp.join(PROJROOT, "assets", gid, gid+".info.log.done"), 'a') as f:
                        f.write(iid+"\n")
                    with open(osp.join(PROJROOT, "assets", gid, gid+".info"), 'a') as f:
                        json.dump(iinfo, f)
                        f.write("\n")
            except KeyError as e:
                error = "KeyError: " + str(e)
            except Exception as e:
                error = "Exception: " + str(e)
            finally:
                if error: print(error)
        except Empty as e:
            pass


## By default, the script will use the group id(s) specified in the configure file. For
## each group, the script tries to download photo infos for each photo in its photo pool
## (i.e. photos saved in the photo list file `GID.pkl`). Retrieved information is saved in
## file `GID.info`, one line per photo. A group whose photo infos exists will be skipped. 
## Specifying target groups (via -G gid0 -G gid1) to process customized groups rather than 
## all the groups in the configure file which is the default situation.
##
## Files:
## GID.pkl, photo lists
## GID.info, photo infos, one item per line
## GID.info.log.done, photo ids whose info has been retrieved
## GID.info.log.fail, photo ids whose info has failed to be retrieved
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Photo Infos for Photos in the Pool of Flickr Groups")
    parser.add_argument("-G", "--groups", action='append', default=[], help="specify the id of target groups")
    parser.add_argument("-n", "--workers", type=int, default=4, help="number of threads, default 4")
    args = parser.parse_args()
    interact = len(args.groups)>0
    groups = args.groups if interact else [osp.basename(osp.dirname(g)) for g in config['groups'].values()]
    groups = list(set(groups)) # del repeat groups
    queue = Queue(maxsize=0)
    pool = []
    # start one enqueue thread for each group
    for gid in groups:
        glock = GLOCKS.get(gid, None)
        if glock is None:
            GLOCKS[gid] = Lock()
        enqtask = Thread(target=producer, args=(queue, gid))
        enqtask.setDaemon(True)
        enqtask.start()
        pool.append(enqtask)
    # start n dequeue thread
    for i in range(args.workers):
        deqtask = Thread(target=consumer, args=(queue, ))
        deqtask.setDaemon(True)
        deqtask.start()
        pool.append(deqtask)
    # wait until all threads terminate
    for t in pool:
        t.join()
        