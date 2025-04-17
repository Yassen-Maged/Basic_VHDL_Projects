function [K1,K2] = SDES_Key_Generation(P_8,P_10,IV)
temp = perm(IV,P_10,10);
left = temp(1:5);
right = temp(6:10);
%Generating K1
left = [left(2:5),left(1)]; %shift_left-1
right = [right(2:5),right(1)]; %shift_left-1
K1 = perm([left,right],P_8,8);
%Generating K2
left = [left(3:5),left(1:2)]; %shift_left-2
right = [right(3:5),right(1:2)]; %shift_left-2
K2 = perm([left,right],P_8,8);
end

