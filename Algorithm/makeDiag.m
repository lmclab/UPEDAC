feature =  importdata('data/rawfeature.txt');
pfeature = feature(:,30:147);  % tag feature
pd = pdist(pfeature);
Z = squareform(pd);
S = exp(-Z/ max(Z(:)));
save('data/reg_matrix.mat','S')