library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity bcd_7seg is
generic(d_width: natural:= 3; -- data width.
n_display: natural:= 1 -- Number of 7SEG displays (i.e. for 10-bit numbers, it's 4 displays)
);
port(
binary_in: in std_logic_vector(d_width-1 downto 0);
HEX: out std_logic_vector(4*n_display-1 downto 0)
);
end bcd_7seg;

architecture beh of bcd_7seg is
constant BCD_N: natural:= 4*n_display; --4 * Number of 7SEG displays (for 10-bit numbers, it's 4*4 = 16)
type segmap is array (0 to 9) of std_logic_vector (7 downto 0); -- binary to 7-seg map
constant smap: segmap := --active low
( --Pgfedcba
	"11000000", --0
	"11111001", --1
	"10100100", --2
	"10110000", --3
	"10011001", --4
	"10010010", --5
	"10000010", --6
	"11111000", --7
	"10000000", --8
	"10010000"--9
);
signal num: unsigned(d_width-1 downto 0):= (others => '0');  --converting to unsigned for arithmatic operations
signal bcd_reg : unsigned(BCD_N -1 downto 0):= (others => '0'); 
begin
num <= unsigned(binary_in);

process (num) --I made it async design, but if you want to make it sync,
			  --you can make it sensitive to the rising_edge of the clock.
variable bcd : unsigned(BCD_N-1 downto 0) := (others => '0');
begin
bcd := (others => '0');
	for i in 0 to d_width-1 loop -- we iterate d_width times because we have d_width bits input.
		for j in 0 to BCD_N/4 -1 loop -- we iterate as many times as the number of 7SEG displays.
			if bcd(4*j + 3 downto 4 * j) > 4 then --check 4 bits by 4 bits.
				bcd(4*j + 3 downto 4 * j) := bcd(4*j + 3 downto 4 * j) + 3; -- add 3
			end if;
		end loop;
		bcd := bcd(BCD_N-2 downto 0) & num(d_width-1 - i); -- shift left by 1 bit
	end loop;
bcd_reg <= bcd;
end process;

process(bcd_reg) --map the BCD number to 7-SEG displays
begin
for i in 0 to n_display-1 loop
	HEX(i*4 + 3 downto i*4) <= smap(to_integer(bcd_reg(i*4 + 3 downto i*4)));
end loop;
end process;

end beh;
