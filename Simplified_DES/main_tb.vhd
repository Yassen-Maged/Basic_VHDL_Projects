library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity main_tb is
generic(n: natural:= 8);
end main_tb;

architecture beh of main_tb is
component main is
generic(
IV_n: natural := 10;
n: natural := 8);
port(
CLK: in std_logic;
Encrypt: in std_logic:= '1'; -- '1' for encrypt and '0' for decrypt.
Encrypt_LED: out std_logic:= 'Z'; -- ON for encrypt and OFF for decrypt (just indicator).
input_word: in std_logic_vector(0 to n-1):= (others => 'Z'); -- 8 Switches.
output_word: out std_logic_vector(0 to n-1):= (others => 'Z')-- 8 LEDs.
);
end component;
signal clk: std_logic:= '0';
signal encrypt: std_logic:= '1';
signal in_word,out_word: std_logic_vector(0 to n-1):= (others => '0');
signal err: boolean := false; -- error indicator.
begin

u0: main port map(
clk => clk,
Encrypt => Encrypt,
input_word => in_word,
output_word => out_word
);
clk_process : process
begin
    clk <= '0';
    wait for 50 ns;
    clk <= '1';
    wait for 50 ns;
end process clk_process;

process(clk)

begin
if falling_edge(clk) then

	if encrypt = '1' then
		if in_word = "01110010" then
			if out_word = "01110111" then
				in_word <= "00000000";
			else
				err <= true;
			end if;
	
		elsif in_word = "00000000" then
			if out_word = "11001110" then
				in_word <= "11111111";
			else
				err <= true;
			end if;
	
		elsif in_word = "11111111" then
			if out_word = "00101010" then
				in_word <= "10101010";
			else
				err <= true;
			end if;
	
		elsif in_word = "10101010" then
			if out_word = "10001101" then
				in_word <= "01110111";
				encrypt <= '0';
			else
				err <= true;
			end if;
	
		else
			in_word <= "01110010";
			encrypt <= '1';
		end if;

	elsif encrypt = '0' then --DECRYPT
		if in_word = "01110111" then
			if out_word = "01110010" then
				in_word <= "11001110";
			else
				err <= true;
			end if;
		
		elsif in_word = "11001110" then
			if out_word = "00000000" then
				in_word <= "00101010";
			else
				err <= true;
			end if;
		
		elsif in_word = "00101010" then
			if out_word = "11111111" then
				in_word <= "10001101";
			else
				err <= true;
			end if;
		
		elsif in_word = "10001101" then
			if out_word = "10101010" then
				assert false;
				report "EVERYTHING IS FINE AND CORRECT!!" severity failure;
			else
				err <= true;
			end if;
		
		else
			in_word <= "01110010";
			encrypt <= '1';
		end if;
	end if;
	
	if err then
		assert false;
		report "WRONG OUTPUT!" severity failure;
	end if;
	
end if;
end process;

end beh;