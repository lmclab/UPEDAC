import pickle
import numpy as np
f=open('unique_usr_fusionfeat.pkl', 'rb') 
data = pickle.load(f)
f.close()

feature = data['feat']

np.savetxt('../data/rawfeature.txt',feature,fmt='%d')



			
		
	