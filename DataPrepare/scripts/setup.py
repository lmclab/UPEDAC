import os
import os.path as osp
import sys
import csv
def prepareTestContext():
    if __name__ == "__main__":
        PROJROOT = osp.dirname(osp.dirname(osp.abspath(__file__)))
        sys.path.insert(0,PROJROOT)
prepareTestContext()
PROJROOT = osp.dirname(osp.dirname(osp.abspath(__file__)))
from flickr import *

# prepare filesystem
if __name__ == "__main__":
    for g in config['groups'].values():
        gid = osp.basename(osp.dirname(g))
        pathname = osp.join(PROJROOT, "assets", gid)
        assets = osp.join(pathname, "images")
        if not osp.isdir(assets):
            os.makedirs(assets)