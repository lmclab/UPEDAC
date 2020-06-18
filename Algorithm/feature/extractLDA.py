import pickle
import numpy as np
f=open('unique_usr_fusionfeat.pkl', 'rb') 
data = pickle.load(f)
f.close()

feature = data['feat']

str = []
totalCNT = 0

N = feature.shape[0]
for i in range(N):
	docid = feature[i][0]
	f = feature[i][21:]
	for j in range(140):
		t = f[j]
		if t>0:
			tt = '%d %d %d' % (docid,j+1,t)
			str.append(tt)
			totalCNT += t

fw = open('../data/feature.txt','w')
fw.write('%d\n%d\n%d\n' % (N,140,totalCNT))

fw.write('\n'.join(str))
fw.close()



			
		
	