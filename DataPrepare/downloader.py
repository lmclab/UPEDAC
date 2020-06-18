import os
import os.path as osp
import requests as http
from concurrent import futures
from threading import Lock

class Downloader(object):
    """
    Basic multi-thread file downloader.

    Args:\n
    - url: str, the url of the online file to be downloaded.
    - destination: str, the local destination where the downloaded file will be saved.
    - workers: int, number of workers created for this download task, 
    set `workers>1` to enable multi-thread download, default 1.
    - force: bool, set True to overwrite the destination file even when it exists.
    In general, a OSError will be raised when the destination file exists and `force=False`.
    """
    def __init__(self, url, destination, workers=1, force=False):
        super(Downloader, self).__init__()
        ## Assume users always feed in legal url and destination.
        self.url = url
        self.trueurl = url
        self.destination = destination
        self.workers = workers
        self.overwrite = force
        if not self.validate(self.destination):
            raise OSError("destination existed: " + \
                self.destination + \
                ". Set force=True to overwrite it or specify another valide destination.")
        self.size = 0
        if self.workers > 1: # multi-thread download requires the size of file
            self.size = self.getHTTPHeader("Content-Length")
            try:
                if self.size:
                    self.size = int(self.size)
            except Exception as e:
                self.size = 0
            if not self.size:
                print("cannot get Content-Length, fallback to use single thread download")
        self.status = True # indicate whether the file is downloaded successfully
        self.lock = Lock()


    def validate(self, file):
        path = osp.dirname(file)
        if len(path)==0:
            path = "."
        if not osp.isdir(path):
            os.makedirs(path)
            return True
        if osp.isfile(file):
            return True if self.overwrite else False
        return True

    def getHTTPHeader(self,k):
        """
        Retrieve a field from the HTTP header meta.

        Args:\n
        - k: str, the target field name.
        """
        r = http.head(self.url)
        try:
            while r.is_redirect:
                self.trueurl = r.headers['location']
                r = http.head(self.trueurl)
            v = r.headers[k]
        except KeyError as e:
            v = None
        return v

    def split(self, start, end):
        headers = {'Range': 'bytes='+str(start)+'-'+str(end)}
        r = http.get(self.trueurl, stream=True, headers=headers)
        if r.ok:
            with open(self.destination, 'r+b') as bw:
                bw.seek(start)
                bw.write(r.content)
        with self.lock:
            self.status = self.status and r.ok

    def run(self):
        # start multi thread 
        if self.size and self.workers>1:
            with open(self.destination, 'wb') as bw:
                bw.truncate(self.size)
            chunksize = self.size // self.workers
            chunks = list(range(0, self.size, chunksize))
            chunks.append(self.size)
            pool = futures.ThreadPoolExecutor(self.workers)
            tasks = []
            for i in range(self.workers):
                tasks.append(pool.submit(self.split, chunks[i], chunks[i+1]))
            futures.wait(tasks)
        # fallback to single thread
        else:
            r = http.get(self.trueurl, stream=True)
            if r.ok:
                with open(self.destination, 'wb') as bw:
                    bw.write(r.content)
            self.status = self.status and r.ok
        return self.status
