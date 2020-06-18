function dist = kldiv(P)

N = size(P,1);
dist1 = zeros(N,N);
for i =1:N
	Pt = repmat(P(i,:),N,1);
	dist10 = kldiv0(P,Pt);
	dist1(i,:) = dist10;
end

dist2 = zeros(N,N);
for i =1:N
	Pt = repmat(P(i,:),N,1);
	dist20 = kldiv0(Pt,P);
	dist2(i,:) = dist20;
end

dist = (dist1 + dist2)/2;

end

function dist = kldiv0(P,Q)

Q = Q ./repmat(sum(Q,2),[1 size(Q,2)]); 
P = P ./repmat(sum(P,2),[1 size(P,2)]); 
M=log(P./Q); 
M(isnan(M))=0; 
dist = sum(P.*M,2); 
end