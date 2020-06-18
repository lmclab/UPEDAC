import pdb
import os
import os.path as osp
from concurrent import futures
from threading import Lock
import requests as http
import urllib.parse as urlparse
import time
import oauth2
from config import config

# lambda functions
repeatc = lambda c,n: "".join([c]*n)

def flickrGetGroupId(url):
    """
    Given the url to the group's page or photo pool, get its group ID. API: \n
    https://www.flickr.com/services/rest/?method=flickr.urls.lookupGroup&api_key=$APIKEY$&url=$URL$&format=json&nojsoncallback=1

    Args:\n
    - url: str, the url to the group's page or photo pool

    Output:\n
    Group ID if succeed, or else None.
    """
    id = None
    query = {
        "method": "flickr.urls.lookupGroup",
        "api_key": config['api_key'],
        "url": url,
        "format": "json",
        "nojsoncallback": 1
    }
    try:
        r = http.get(config['rest'], params=query,
            headers={'Content-Type':'application/json'},
            proxies=config.get("proxies", None))
        if r.ok:
            result = r.json()
            if result["stat"] == "ok":
                id = result["group"]["id"]
            else:
                print(query["method"],":", result['code'], ",", result['message'])
    except Exception as e:
        print("Exception: flickrGetGroupId()", str(e))
    return id

def flickrGetGroupPhotoList(id, workers=2, meta_only=False):
    """
    Given group id, get the meta of photos in the group. API:\n
    https://www.flickr.com/services/rest/?method=flickr.groups.pools.getPhotos&api_key=$APIKEY$&group_id=$GROUPID$&format=json&nojsoncallback=1

    Args:\n
    - id: str, group id
    - workers: int, number of thread, default 2.
    - meta_only: bool, set True to get meta information only.

    Output:\n
    [Bool, List], True only when the whole lists is downloaded, List contains the lists currently downloaded.
    If `meta_only=True` return compact meta info in format of `dict`, 
    e.g. {"page": 2, "pages": "1183", "perpage": 10, "total": "11825"}
    """
    def getListByPage(page):
        query = {
            "method": "flickr.groups.pools.getPhotos",
            "api_key": config['api_key'],
            "group_id": id,
            "page": page,
            "format": "json",
            "nojsoncallback": 1
        }
        metax = None
        try:
            r = http.get(config['rest'], params=query,
                headers={'Content-Type':'application/json'},
                proxies=config.get("proxies", None))
            if r.ok:
                result = r.json()
                if result['stat'] == "ok":
                    metax = result['photos']
                else:
                    print(query["method"],":", result['code'], ",", result['message'])
        except Exception as e:
            print("Exception: flickrGetGroupPhotoList()", str(e))
        return metax
    def getListByRange(scope):
        for i in scope:
            metax = getListByPage(i)
            if metax:
                with lock:
                    photos.extend(metax['photo'])
    ##
    photos = []
    lock = Lock()
    meta = getListByPage(1)
    if not meta:
        if meta_only:
            return None
        else:
            return False, photos
    if meta_only:
        # For meta only
        meta.pop("photo",None)
        return meta
    # For get photo list
    pages = int(meta['pages'])
    total = int(meta['total'])
    if total < 1: # in case of the group pool has no photos
        return True, photos
    workers = min(workers, pages) # when too few pages
    chunksize = pages // workers
    chunks = list(range(1, pages+1, chunksize))
    chunks.append(pages+1)
    pool = futures.ThreadPoolExecutor(workers)
    tasks = []
    for i in range(workers):
        tasks.append(pool.submit(getListByRange, range(chunks[i], chunks[i+1])))
    futures.wait(tasks)
    ## active users continue to upload photos to active group which means
    ## total number of photos will exceed the `total` we retrieved at the 
    ## begining of download task. So we take it as success when the total
    ## retrieved photo items is larger than the `total`.
    return total<=len(photos), photos

def flickrGetPhotoInfo(id):
    """
    Given photo ID, retrieve its information.

    Args:\n
    - id: str, photo id 

    Output:\n
    Return photo information if succeed, or else None.
    """
    info = None
    query = {
        "method": "flickr.photos.getInfo",
        "api_key": config['api_key'],
        "photo_id": id,
        "format": "json",
        "nojsoncallback": 1
    }
    try:
        r = http.get(config['rest'], params=query,
            headers={'Content-Type':'application/json'},
            proxies=config.get("proxies", None))
        if r.ok:
            result = r.json()
            if result["stat"] == "ok":
                info = result["photo"]
            else:
                print(query["method"],":", result['code'], ",", result['message'])
    except Exception as e:
        print("Exception: flickrGetPhotoInfo()", str(e))
    return info

def flickrGetPhotoFaves(id, workers=2, meta_only=False):
    """
    Given photoID, retrieve its favorites which is a list of connection with other
    Flickr users. Photo favorites are usually in number of thousand item splitted
    into multi pages by Flickr `flickr.photos.getFavorites` API, so we enable 
    multi-thread retrieval by setting `worker=N` to speed up the process.
    API:\n
    https://www.flickr.com/services/rest/?method=flickr.photos.getFavorites&api_key=$APIKEY$&url=$URL$&format=json&nojsoncallback=1

    Args:\n
    - id: str, photo id
    - workers: int, number of thread, default 2.
    - meta_only: bool, set True to get meta information only.

    Output:\n
    [Bool, List], True only when the whole lists is downloaded, List contains the lists currently downloaded.
    If `meta_only=True` return compact meta info in format of `dict`, 
    e.g. `{"id": "20225336653", "secret": "42ba3d8afc", "server": "573", "farm": 1, "page": 1, "pages": "1552", "perpage": 10, "total": "15511"}`
    """
    def getFavesByPage(page):
        query = {
            "method": "flickr.photos.getFavorites",
            "api_key": config['api_key'],
            "photo_id": id,
            "page": page,
            "per_page": 30,
            "format": "json",
            "nojsoncallback": 1
        }
        metax = None
        try:
            r = http.get(config['rest'], params=query,
                headers={'Content-Type':'application/json'},
                proxies=config.get("proxies", None))
            if r.ok:
                result = r.json()
                if result['stat'] == "ok":
                    metax = result['photo']
                else:
                    print(query["method"],":", result['code'], ",", result['message'])
        except Exception as e:
            print("Exception: flickrGetPhotoFaves()", str(e))
        return metax
    def getFavesByRange(scope):
        for i in scope:
            metax = getFavesByPage(i)
            if metax:
                with lock:
                    faves.extend(metax['person'])
    ##
    faves = []
    lock = Lock()
    meta = getFavesByPage(1)
    if not meta:
        if meta_only:
            return None
        else:
            return False, faves
    if meta_only:
        # For meta only
        meta.pop("person",None)
        return meta
    # For get photo list
    pages = int(meta['pages'])
    total = int(meta['total'])
    if total < 1: # when no faves
        return True, faves
    workers = min(workers, pages)
    chunksize = pages // workers
    chunks = list(range(1, pages+1, chunksize))
    chunks.append(pages+1)
    pool = futures.ThreadPoolExecutor(workers)
    tasks = []
    for i in range(workers):
        tasks.append(pool.submit(getFavesByRange, range(chunks[i], chunks[i+1])))
    futures.wait(tasks)
    ## active users continue to like a photos which means total number of favorites, 
    ## the connection between users, continuously increases and has a high probability
    ## to exceed the `total` we retrieved at the begining of retrieval task. So we take 
    ## it as success when the total retrieved favorites are larger than the `total`.
    return total<=len(faves), faves


def flickrAuthorizedAPI(method, params={}):
    """
    Generate authorized flickr rest api based on access token.
    Additional query parameters `params` supported. The final 
    url is signed using HMAC-SHA1 encryption as required by 
    Flickr.

    Args:\n
    - method: str, Flickr supported API methods as list in 
    https://www.flickr.com/services/api/
    - params: dict, additional api parameter

    Examples:\n
    >>> flickrAuthorizedAPI("flickr.photos.getSizes", params=dict(
        nojsoncallback=1,
        format="json"
        ))
    """
    query = dict(
        method=method,
        oauth_nonce=oauth2.generate_nonce(),
        oauth_timestamp=oauth2.generate_timestamp(),
        oauth_consumer_key=config["api_key"],
        oauth_signature_method="HMAC-SHA1",
        oauth_version="1.0",
        oauth_token=config["oauth"]["access_token_key"]
    )
    query.update(params)
    req = oauth2.Request(method="GET", url=config["rest"], parameters=query)
    signmethod = oauth2.SignatureMethod_HMAC_SHA1()
    req.sign_request(
        signmethod, 
        oauth2.Consumer(config["api_key"], config["api_secret"]), 
        oauth2.Token(
            config["oauth"]["access_token_key"],
            config["oauth"]["access_token_secret"])
        )
    return req.to_url()

class FlickrOAuthException(Exception):
    pass

class FlickrOAuth(object):
    """
    Module `py-oauth2` donot set proxy so if you can only access Flickr behind
    a proxy please set `http_proxy` and `hhtps_proxy` environment variables in
    ahead of calling this class.
    """
    def __init__(self,
        api_key=None,
        api_sec=None
        ):
        self.REQUEST_TOKEN_URL = "https://www.flickr.com/services/oauth/request_token"
        self.AUTHORIZATION_URL = "https://www.flickr.com/services/oauth/authorize"
        self.ACCESS_TOKEN_URL = "https://www.flickr.com/services/oauth/access_token"
        self.api_key = api_key or config["api_key"]
        self.api_sec = api_sec or config["api_secret"]
        self.app = oauth2.Consumer(self.api_key, self.api_sec)
    
    def build_token(self, key, secret, verifier=None):
        """
        Give token key and secret, return an oauth2.Token instance 
        representing the token. Additional oauth verifier is supported.
        
        Args:\n
        - key: str, the token key
        - secret: str, the token secret
        - verifier [optional]: str, the oauth verifier string
        """
        token = oauth2.Token(key, secret)
        if verifier is not None:
            token.set_verifier(verifier)
        return token

    def get_signed_request(self, callback):
        """
        Flickr only supports HMAC-SHA1 signature encryption.
        This method will sign your requests to 
        `https://www.flickr.com/services/oauth/request_token`
        for Request Token with the `callback` url. The returned
        signed url is a Request Token request.

        Args:\n
        - callback: str, the callback url.

        Output:\n
        The Request Token request url signed with HMAC-SHA1.

        For example: \n
        >>> get_signed_request("https://api.flickr.com/services/rest/?method=flickr.test.echo")
        """
        params = dict(
            oauth_nonce=oauth2.generate_nonce(),
            oauth_timestamp=oauth2.generate_timestamp(),
            oauth_consumer_key=self.api_key,
            oauth_signature_method="HMAC-SHA1",
            oauth_version="1.0",
            oauth_callback=callback,
        )
        req = oauth2.Request(method="GET", url=self.REQUEST_TOKEN_URL, parameters=params)
        signmethod = oauth2.SignatureMethod_HMAC_SHA1()
        req.sign_request(signmethod, self.app, None)
        return req.to_url()

    def get_request_token(self, callback):
        """
        Get the request token for further authorization of users' requests
        to `callback`.

        Args:\n
        - callback: str, the callback url.

        Output:\n
        An oauth2.Token instance with acquired request token.
        """
        token = None
        try:
            signed_req = self.get_signed_request(callback)
            r = http.get(signed_req, proxies=config.get("proxies", None))
            if r.ok:
                rtext = dict(urlparse.parse_qsl(r.text))
                if rtext.get("oauth_problem") is not None:
                    raise FlickrOAuthException(rtext["oauth_problem"])
                if rtext.get("oauth_token") is not None:
                    token = oauth2.Token(
                        rtext["oauth_token"],
                        rtext["oauth_token_secret"]
                    )
                else:
                    raise FlickrOAuthException("invalid return value")
            else:
                raise FlickrOAuthException(r.reason)
        except Exception as e:
            print("Exception: FlickrOAuth.get_request_token()", str(e))
        return token

    def get_authorization_request(self, token, perms="read"):
        """
        For Request Token `token`, get the user authorization URL.

        Args:\n
        - token: oauth2.Token, an oauth2.Token instance represents the Request Token
        - perms: str, the permission you are requiring, `"read", "write" or "delete"`

        Output:\n
        The authorization URL, e.g. `https://www.flickr.com/services/oauth/authorize
        ?oauth_token=72157626737672178-022bbd2f4c2f3432`
        """
        params = dict(
            oauth_token=token.key,
            perms=perms
        )
        req = oauth2.Request(method="GET", url=self.AUTHORIZATION_URL, parameters=params)
        return req.to_url()

    def get_access_token(self, request_token):
        """
        Exchange the approved Request Token `token` for an Access Token.

        Args:\n
        - request_token: oauth2.Token, An oauth2.Token instance represents 
        the Request Token, token secret and oauth_verifier must be set.

        Output:\n
        An oauth2.Token instance with acquired access token.

        Note: oauth_verifier represents oauth verifier returned in the callback after authorization.
        """
        token = None
        params = dict(
            oauth_nonce=oauth2.generate_nonce(),
            oauth_timestamp=oauth2.generate_timestamp(),
            oauth_consumer_key=self.api_key,
            oauth_signature_method="HMAC-SHA1",
            oauth_version="1.0",
            oauth_token=request_token.key,
            oauth_verifier=request_token.verifier
        )
        req = oauth2.Request(method="GET", url=self.ACCESS_TOKEN_URL, parameters=params)
        signmethod = oauth2.SignatureMethod_HMAC_SHA1()
        req.sign_request(signmethod, self.app, request_token)
        try:
            r = http.get(req.to_url(), proxies=config.get("proxies", None))
            if r.ok:
                rtext = dict(urlparse.parse_qsl(r.text))
                if rtext.get("oauth_problem") is not None:
                    raise FlickrOAuthException(rtext["oauth_problem"])
                if rtext.get("oauth_token") is not None:
                    token = oauth2.Token(
                        rtext["oauth_token"],
                        rtext["oauth_token_secret"]
                    )
                    print(
                        "Info: FlickrOAuth.get_access_token() received token", 
                        "username="+rtext["username"]+"&id="+rtext["user_nsid"])
                else:
                    raise FlickrOAuthException("invalid return value")
            else:
                raise FlickrOAuthException(r.reason)
        except Exception as e:
            print("Exception: FlickrOAuth.get_access_token()", str(e))
        return token

##
class FlickrPhotoPageExcpetion(Exception):
    pass

class FlickrPhotoPage(object):
    pass