function D = JSdiv(P,Q)
%JSDIV   Jensen-Shannon divergence.
%   D = JSDIV(P,Q) calculates the Jensen-Shannon divergence of the two 
%   input distributions.
%
%   See also KLDIST, FDIV, HDISC, BDIST, CHISQUAREDIV, VARDIST and 
%   HARMONICMEAN.

% Input argument check
error(nargchk(2,2,nargin))
if abs(sum(P(:))-1) > 0.00001 || abs(sum(Q(:))-1) > 0.00001
    %error('Input arguments must be probability distributions.')
    Q = Q ./repmat(sum(Q,2),[1 size(Q,2)]); 
    P = P ./repmat(sum(P,2),[1 size(P,2)]); 
end
if ~isequal(size(P),size(Q))
    error('Input distributions must be of the same size.')
end

% JS-divergence
%M = (P + Q) / 2;
D1 = KLdist(P,Q);
D2 = KLdist(Q,P);
D = (D1 + D2) / 2;

function D = KLdist(P,Q)
%KLDIST   Kullbach-Leibler distance.
%   D = KLDIST(P,Q) calculates the Kullbach-Leibler distance (information
%   divergence) of the two input distributions.
%
%   See also JSDIV, FDIV, HDISC, BDIST, CHISQUAREDIV, VARDIST and 
%   HARMONICMEAN.

% Input argument check
error(nargchk(2,2,nargin))
if abs(sum(P(:))-1) > 0.00001 || abs(sum(Q(:))-1) > 0.00001
    error('Input arguments must be probability distributions.')
end
if ~isequal(size(P),size(Q))
    error('Input distributions must be of the same size.')
end

% KL-distance
P2 = P(P.*Q>0);     % restrict to the common support
Q2 = Q(P.*Q>0);
P2 = P2 / sum(P2);  % renormalize
Q2 = Q2 / sum(Q2);

D = sum(P2.*log(P2./Q2));