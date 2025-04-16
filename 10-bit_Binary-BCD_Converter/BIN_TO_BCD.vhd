library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity bin_to_bcd is
generic(N: natural:= 10;
BCD_N: natural :=13 -- (1 - 4 - 4 - 4) bits per display for 16-bit binary number
);
port(
clk,reset: in std_logic;
binary_in: in std_logic_vector(n-1 downto 0);
HEX0,HEX1,HEX2,HEX3: out std_logic_vector(7 downto 0)
);
end bin_to_bcd;

architecture beh of bin_to_bcd is
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
signal num: unsigned(n-1 downto 0); --converting the std_logic_vector to unsigned for arithmatic operations
signal bcd_reg : unsigned(BCD_N -1 downto 0) := (others => '0'); 
begin
num <= unsigned(binary_in);

process (num) --I made it async design, but if you want to make it sync,
			  --you can make it sensitive to the rising_edge of the clock.
variable bcd : unsigned(BCD_N-1 downto 0) := (others => '0');
begin
bcd := (others => '0');
	for i in 0 to n-1 loop -- we iterate N times because we have N bits input
		for j in 0 to 2 loop
			if bcd(4*j + 3 downto 4 * j) > 4 then --check 4 bits by 4 bits
				bcd(4*j + 3 downto 4 * j) := bcd(4*j + 3 downto 4 * j) + 3; -- add 3
			end if;
		end loop;
		bcd := bcd(BCD_N-2 downto 0) & num(n-1 - i); -- shift left by 1 bit
	end loop;
bcd_reg <= bcd;
end process;

process(bcd_reg) --Display the BCD number on 7-SEG display
begin
hex0 <= smap(to_integer(bcd_reg(3 downto 0)));	--ones
hex1 <= smap(to_integer(bcd_reg(7 downto 4)));	--tens
hex2 <= smap(to_integer(bcd_reg(11 downto 8)));	--hundreds
hex3 <= smap(to_integer(bcd_reg(12 downto 12)));--thousands
end process;
end beh;
