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

# Globle 
PRODUCER_ACTIVE = 0
LOCK = Lock() # enqueueing locks 
GLOCKS = {} # dequeueing locks

def producer(queue, groups):
    """
    Accept a queue and a list of groups, check photo existence.
    Add item into the queue when the photo is not downloaded yet.

    Args:\n
    - queue: Queue, the queue holding all the images to be download
    - groups: list, a list of urls of group's page or photo pool
    """
    global PRODUCER_ACTIVE
    global LOCK
    with LOCK:
        PRODUCER_ACTIVE += 1
    try:
        for gid in groups:
            pathname = osp.join(PROJROOT, "assets", gid)
            filename = osp.join(pathname, gid+".pkl")
            assets = osp.join(pathname, "images")
            if not osp.isfile(filename):
                print(gid, ": group photo list not found, skipped")
                continue
            photos = []
            with open(filename, "rb") as f:
                photos = pkl.load(f)['photos']
            for item in photos:
                iid = item['id']
                ## assume all image of format JPG
                if not osp.isfile(osp.join(assets, iid+".jpg")):
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
            with LOCK: # make sure each thread process an unique task
                item = queue.get(timeout=5)
            try:
                gid = item['gid']
                iid = item['id']
                secret = item['secret']
                isrv = item['server']
                iurl = osp.join(config['images'], isrv, iid+"_"+secret+".jpg")
                filename = osp.join(PROJROOT, "assets", gid, "images", iid+".jpg")
                iinfo = flickrGetPhotoInfo(iid)
                if iinfo is None: continue # skip photos whose info cannot be found
                if iinfo['media'] == "video" and config['video'] == False: continue
                print(gid, ": downloading photo ", iurl)
                worker = Downloader(iurl,filename)
                status = worker.run()
                # if status:
                #     print("done.")
                # else:
                #     print("fail.")
                # if status:
                #     with GLOCKS[gid]:
                #         with open(osp.join(PROJROOT, "assets", gid, "photoinfo@"+gid+".txt"), 'a') as f:
                #             f.write(str(iinfo)+"\n")
            except KeyError as e:
                error = "KeyError: " + str(e)
            except OSError as e:
                if not "destination existed" in str(e):
                    error = "OSError: " + str(e)
                    if osp.isfile(filename):
                        os.remove(filename)
            except Exception as e:
                error = "Exception: " + str(e)
                if osp.isfile(filename):
                    os.remove(filename)
            finally:
                if error: print(error)
        except Empty as e:
            pass


## By default, the script will use the group id(s) specified in the configure file. For
## each group, the script tries to download photos in its photo pool, skipping downloaded
## photos. Specifying target groups (via -G gid0 -G gid1) to process customized groups 
## rather than all the groups in the configure file which is the default situation.
##
## Files:
## GID.pkl, photo lists
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Photos in the Pool of Flickr Groups")
    parser.add_argument("-G", "--groups", action='append', default=[], help="specify the id of target groups")
    parser.add_argument("-n", "--workers", type=int, default=4, help="number of threads, default 4")
    args = parser.parse_args()
    interact = len(args.groups)>0
    groups = args.groups if interact else [osp.basename(osp.dirname(g)) for g in config['groups'].values()]
    groups = list(set(groups)) # del repeat groups
    queue = Queue(maxsize=0)
    pool = []
    ## prepare file read/write locks
    for gid in groups:
        glock = GLOCKS.get(gid, None)
        if glock is None:
            GLOCKS[gid] = Lock()
        # create an enqueue producer for each group
        pool.append(Thread(target=producer, args=(queue, [gid])))
    # create n dequeue consumers
    for i in range(args.workers):
        pool.append(Thread(target=consumer, args=(queue,)))
    # start all threads
    for t in pool:
        t.setDaemon(True)
        t.start()
    # wait until all threads terminate
    for t in pool:
        t.join()

