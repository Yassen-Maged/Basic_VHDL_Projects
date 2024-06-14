library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity BIN_TO_BCD is
generic (n: natural:= 10);
port(
	SW: in std_logic_vector(9 downto 0); -- 10switches
	led: out std_logic_vector(9 downto 0); -- 10 leds indicate which switches are enabled
	HEX0,HEX1,HEX2,HEX3: out std_logic_vector(7 downto 0) -- 7-SEG displays
	--HEX0: ones, HEX3: Thousands
);
END BIN_TO_BCD;

architecture behavioral of BIN_TO_BCD is
type segmap is array (0 to 9) of std_logic_vector (7 downto 0); -- binary to 7-seg map
signal smap: segmap := --active low
(
	"11000000", --0
	"11111001", --1
	"10100100", --2
	"10110000", --3
	"10011001", --4
	"10010010", --5
	"10000010", --6
	"11111000", --7
	"10000000", --8
	"10010000"  --9
);
signal num: unsigned(9 downto 0); --converting the std_logic_vector to unsigned for arithmatic operations
signal bcd_reg : unsigned(12 downto 0) := (others => '0'); -- (1 - 4 - 4 - 4) bit per display
							   -- (11111111111)2 => 1024
begin
led <= sw;
num <= unsigned(sw);

process (num) --we don't need clock here
variable bcd : unsigned(12 downto 0) := (others => '0');
begin
bcd := (others => '0');
	for i in 0 to 9 loop -- we iterate 10 times because we have 10 bits input
		for j in 0 to 2 loop
			if bcd(4*j + 3 downto 4 * j) > 4 then --check 4 bits by 4 bits
				bcd(4*j + 3 downto 4 * j) := bcd(4*j + 3 downto 4 * j) + 3; -- add 3
			end if;
		end loop;
		bcd := bcd(11 downto 0) & num(9 - i); -- shift left by 1 bit
	end loop;
bcd_reg <= bcd;
end process;

process(bcd_reg)
begin
hex0 <= smap(to_integer(bcd_reg(3 downto 0)));
hex1 <= smap(to_integer(bcd_reg(7 downto 4)));
hex2 <= smap(to_integer(bcd_reg(11 downto 8)));
hex3 <= smap(to_integer(bcd_reg(12 downto 12)));
end process;

end behavioral;
