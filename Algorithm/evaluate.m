addpath('script');

feature =  importdata('data/rawfeature.txt');
gt = feature(:,2:21);


%%%%
feature =  importdata('data/graphshift_output.txt');
pd = zeros(7455,20);
for i=0:19
    idx = find(feature(:,2) == i );
    pd(feature(idx,1)+1,i+1) = 1;
end

BER = runBAC(gt,pd)