function [left_o, right_o] = SDES_Encryption(left,right,K,EP,P4,S0,S1)
ep_out = perm(right,EP,8);
ep_out = xor(ep_out,K);

s0_in = ep_out(1:4);
s_r = 2*s0_in(1) + s0_in(4)+1;
s_c = 2*s0_in(2) + s0_in(3)+1;
s0_out = dec2bin(S0(s_r,s_c),2);

s1_in = ep_out(5:8);
s_r = 2*s1_in(1) + s1_in(4)+1;
s_c = 2*s1_in(2) + s1_in(3)+1;
s1_out = dec2bin(S1(s_r,s_c),2);

s_out = ([s0_out, s1_out]);
temp = zeros(1,4);
for i = 1:4
    temp(i) = bin2dec(s_out(P4(i)));
end
s_out = temp;
s_out = xor(s_out,left);
left_o = s_out;
right_o = right;
end

