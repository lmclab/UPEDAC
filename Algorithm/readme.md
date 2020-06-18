# The code could be run step by step:

1.  At first, please copy the "unique_usr_fusionfeat.pkl" from DataPrepare section to feature folder and then make feature from raw data,
```
cd feature; 
python extractLDA.py 
python extractfeature2.py
```
2. make regularization dialog matrix
```
matlab -r "makeDiag"
```
3. extract feature by LDA and compute the KL divergence matrix.
```
matlab -r "runlda"
```
4. do GraphShift Cluster
```
python graphshift.py
```
5. evaluate by BAC
```
matlab -r "evaluate"
```
