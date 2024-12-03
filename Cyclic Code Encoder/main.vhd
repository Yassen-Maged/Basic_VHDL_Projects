library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity main is
generic(k: natural := 4;-- The length of the messege.
n: natural := 7);-- The length of the codeword.
port(
U: in std_logic_vector(k-1 downto 0); --Message.
CODEWORD: out std_logic_vector(n-1 downto 0):= (others => '0') --CODEWORD.
);
end main;

architecture beh of main is
constant g: unsigned(k-1 downto 0) := "1011";-- Generator Polynomial G(x) = x3 + x + 1.
begin

process(U)
variable result: unsigned(n-1 downto 0):= (others => '0'); --the result of every iteration.
variable temp: unsigned(n-1 downto 0):= (others => '0'); --temporary register holds the result before being added to the previous one.
begin
result := (others => '0');
	for i in 0 to k-1 loop -- for every bit in the messege.
		temp:= (others => '0'); --clear the register.
		if U(i) = '1' then -- Multiply the generator matrix by the weight of (i).
			temp(k-1 downto 0) := g;
			temp := temp sll i; --The multiplication process without the need of "*".
			result := result xor temp; --Modulo-2-sum.
		else
			null;
		end if;
	end loop;
CODEWORD <= std_logic_vector(result);
end process;

end beh;