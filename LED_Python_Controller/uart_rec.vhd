library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity uart_rec is
port(
clk,rx,rstn: in std_logic;
valid: out std_logic:= '0';
uart_data: out std_logic_vector(7 downto 0):= (others =>'0')
);
end uart_rec;

architecture beh of uart_rec is
signal data: std_logic_vector(7 downto 0):= (others =>'0');
type uart_fsm is (start_bit,data_receive,stop_bit);
signal pr: uart_fsm:= start_bit;
signal bit_count: natural range 0 to 7:= 0;
begin

process(rstn,clk)
begin
if rstn = '0' then
	pr <= start_bit;
	data <= (others =>'0');
	bit_count <= 0;
	valid <= '0';
elsif rising_edge(clk) then
	case pr is
	when start_bit =>
		bit_count <= 0;
		valid <= '0';
		if rx = '0' then
			pr <= data_receive;
		else
			pr <= start_bit;
		end if;
	when data_receive =>
		valid <= '0';
		data(bit_count) <= rx;
		if bit_count >= 7 then
			bit_count <= 0;
			pr <= stop_bit;
		else
			bit_count <= bit_count +1;
		end if;
	when stop_bit =>
		if rx = '1' then
			pr <= start_bit;
			uart_data <= data;
			valid <= '1';
		else
			pr <= stop_bit;
		end if;
	end case;
end if;
end process;
end beh;