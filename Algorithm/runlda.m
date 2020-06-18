

clear all;
addpath('rLDA');
addpath('script');
%% Data files
corpus_fname = 'data/feature.txt';
vocab_fname  = 'data/vocab.txt';


%% Parameter setting
config.T            = 20;
config.beta         = 0.01;
config.alpha        = -999;  %% later set alpha = 0.05 * N / (D*T)
config.gibbs_iter   = 500;
config.lag_iter     = 50;
config.reg_iter     = 10;
config.nu           = 0.5;

%% run Quad-Reg LDA
reg = 1;  regmatrix_fname   = 'data/reg_matrix.mat';
rand('state', 7);
[Nwt, Ndt, PHIwt] = regularized_lda(corpus_fname, vocab_fname, reg, regmatrix_fname, config);
save('data/result-rlda','Nwt','Ndt','PHIwt');

dist = kldiv1(Ndt);
dist = (dist +dist')/2;

save('data/kldiv','dist');