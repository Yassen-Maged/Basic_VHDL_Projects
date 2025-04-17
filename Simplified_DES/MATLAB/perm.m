function key_out = perm(key_in,bit_order,n)
key_out = zeros(1,n);
    for i = 1:n
        key_out(i) = key_in(bit_order(i));
    end
end

