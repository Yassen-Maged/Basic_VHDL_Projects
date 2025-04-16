library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity main_tb is
generic(k: natural := 4;-- The length of the messege.
n: natural := 7);-- The length of the codeword.
end main_tb;

architecture beh of main_tb is
signal clk: std_logic := '0';
signal u: unsigned(k-1 downto 0) := (others => '0');
signal codeword: std_logic_vector(n-1 downto 0) := (others => '0');
signal u_int: natural range 0 to 15; --just to convert the message from binary to integer

component main is
generic(k: natural := 4;-- The length of the messege.
n: natural := 7);-- The length of the codeword.
port(
U: in std_logic_vector(k-1 downto 0); --Message.
CODEWORD: out std_logic_vector(n-1 downto 0):= (others => '0') --CODEWORD.
);
end component;

type memory is array (0 to 15) of std_logic_vector(n-1 downto 0);
signal ver: memory := --verification memory, contains all possible codewords for G(x)= x3 +x +1.
("0000000", "1101000", "0110100", "1011100", "0011010",
 "1110010", "0101110", "1000110", "0001101", "1100101",
 "0111001", "1010001", "0010111", "1111111", "0100011", "1001011");
begin

u0: main port map(
U => std_logic_vector(u),
CODEWORD => codeword
);

u_int <= to_integer(u);

clock:process
begin
wait for 2ns;
clk <= not(clk);
end process;

process(clk)
begin
if rising_edge(clk) then
	u <= u +1;
	if ver(u_int) = codeword then
		report "CODEWORD HAS BEEN VERIFIED: " & integer'image(u_int);
	else
		assert false;
		report "WRONG CODEWORD!: " & integer'image(u_int) severity failure;
	end if;
	if u = "1111" then
		assert false;
		report "CONGRATS! EVERYTHING IS FINE!: " severity failure;
	end if;
end if;
end process;
end beh;