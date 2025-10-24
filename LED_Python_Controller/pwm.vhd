library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity pwm is
generic(
	max_count: natural := 100;
	n: natural := 7);
port(
clk,rstn: in std_logic;
duty: in std_logic_vector(n-1 downto 0):= (others => '0');
pwm_out,ready: out std_Logic:= '0'
);
end pwm;

architecture beh of pwm is
constant max_percent: unsigned(n-1 downto 0):= "1100100";
signal duty_cycle,count: natural range 0 to max_count:=0;
signal safety_check: unsigned(n-1 downto 0):= (others => '0');
begin

safety_check <= unsigned(duty);
duty_cycle <= to_integer(safety_check) when safety_check <= max_percent else
					0;
process(rstn,clk)
begin
if rstn = '0' then
	pwm_out <= '0';
	ready <= '0';
	count <= 0;
elsif rising_edge(clk) then
	if duty_cycle = 100 then
		pwm_out <= '1';
	elsif count >= duty_cycle then
		pwm_out <= '0';
	else
		pwm_out <= '1';
	end if;
	
	if count >= max_count then
		count <= 0;
	else
		if count = 0 then
			ready <= '1';
		else
			ready <= '0';
		end if;
		count <= count +1;
	end if;
end if;
end process;
end beh;