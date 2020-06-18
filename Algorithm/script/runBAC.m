
function  BER = runBer5(gt,pd)
%gt = [1 0 1;
%    0 1 0;
%    1 0 0;
%    0 0 1];
%pd  = [0 0 0;
%    1 1 1;
%    1 1 1;
%    0 0 0];;

uN = size(gt,1);
nG = size(gt,2);

BER = zeros(nG,1);
spt = sum(pd,1);
[~,gidx] =sort(spt,2);

ber_m = zeros(nG, nG);
ttmax = zeros(nG, 1);

for ii =1:nG  % each class in predict
    realidx = gidx(ii);
    lpd = pd(:,realidx);
    ngt = size(gt,2);   % how many classes in current groundtruth
    tmp = zeros(ngt,1);
    for jj =1:ngt
        lgt = gt(:,jj);
        trueidx = find(lgt == 1);
        falseidx = find(lgt == 0);
        tmp = 1-0.5*(sum(lpd(trueidx) == 0)/length(trueidx) + sum(lpd(falseidx) == 1)/ length(falseidx));
        ber_m(ii, jj) = tmp;
    end
    [tmax,idx] = max(tmp);
end

BER = ber_m;
%ttmax
save('ber.mat', 'BER');
[assignment,cost] = munkres(-BER);
[assignedrows,dum]=find(assignment);

tmp = BER;
BER = [];
idx = assignedrows';
for i=1:length(idx),
    BER(i) = tmp(idx(i),i);
end
mean(BER);
[Y,I] = sort(idx);
BER = BER(I)';




