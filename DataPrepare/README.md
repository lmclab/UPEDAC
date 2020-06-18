===
# Before we start
Properly configure `config.py`:  
- api_key
- api_secret
- proxies
- groups
- groupids
- groupnames
- oauth

Then run `python scripts/setup.py` to prepare the working context.

# Prepare data
Download photo information, photos and their associated favorites.

First, pull photo list in each group from flickr server:
```python
python scripts/download_photolist.py 
```

For each photo in one group, pull its information, its associated favorites and the photo itself:
```python
python scripts/download_photoinfo.py 
python scripts/download_photofaves.py 
python scripts/download.py 
```

Then we merge photo information and favorites stored in separate files into a single file:
```python
python scripts/merge2update_photoinfo.py
```

# Feature Generation
Run `python scripts/20200520.py` to build mappings:  
- *photo-group*: photo A belongs to group B
- *photo-user*: photo A belongs to user B
- *photo-tag*: photo A has tag B

The script additionally do:
- select top 117 frequently used tags and build *user-tag* histgram
- randomly select <=500 users from each group together with their photos
- do a basic and simple data analysis

The above details matters in the process of generating user features. Now let's change into directory `color_harmonization` and then build *user-texture* feature and *user-ch* feature.
```sh
cd color_harmonization
```

**Build *user-texture* feature**: we extract texture features for photos that belong to selected users, and then perform kmean clustering (with 15 clusters). We derive *user-texture* feature of a user by summing over all 15-d labels of photos belonging to the user.
```python
# pwd: color_harmonization
python tmain.py
```

**Build *user-ch* feature**: The color harmony feature is a 8-d onehot vector. For each photo, we extract its color harmony feature and sum to derive the *user-ch* feature.
```python
# pwd: color_harmonization
python xmain.py
```

For the final user feature:
```python
# pwd: color_harmonization
python mergeAll.py
```
The script merges *user-tag*, *user-texture* and *user-ch* to generate the final 140-d user features.

The user feature is in format of `uid|groups|ch|tag|texture`, splitting into 5 parts:
- *uid*: the 1-based user index
- *groups*: group label of the user, e.g. if user A in group 1 and 2, its label is `110000...`
- *ch*: the 8-d user feature in color harmony space
- *tag*: the 117-d user feature in tag space
- *texture*: the 15-d user feature in texture space




