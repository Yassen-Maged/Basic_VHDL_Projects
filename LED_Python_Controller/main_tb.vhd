library ieee;library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity main_tb is
generic(
n: natural := 7;
max_count: natural := 100);
end main_tb;

architecture beh of main_tb is
component main is
generic(n: natural := 7);
port(
	clk,rstn,uart_rx: in std_logic;
	HEX0,HEX1,HEX2: out std_Logic_vector(7 downto 0);
	led: out std_logic);
end component;
constant uart_period: time := 104166ns;
signal clk,clk9600,led: std_logic:= '0';
signal tx,rstn: std_logic:= '1';
signal HEX0,HEX1,HEX2: std_Logic_vector(7 downto 0);
signal uart_data: unsigned(7 downto 0):= (others => '1');
signal bit_count: natural range 0 to 7:= 0;
type tx_state is (start_bit,send_data,stop_bit,waiting);
signal pr: tx_state:=start_bit;
begin

uart_clk_proc:process
begin
wait for uart_period/2;
clk9600 <= not clk9600;
end process uart_clk_proc;

clk_proc:process
begin
wait for 10ns;
clk <= not clk;
end process clk_proc;

process(clk9600)
variable wait_cnt: natural range 0 to 2:= 0;
begin

if rising_edge(clk9600) then
	case pr is
	when start_bit =>
		tx <= '0';
		pr <= send_data;
		
	when send_data =>
		if bit_count = 7 then
			bit_count <= 0;
			uart_data <= uart_data +5;
			pr <= stop_bit;
		else
			bit_count <= bit_count +1;
		end if;
		tx <= uart_data(bit_count);
		
	when stop_bit =>
		tx <= '1';
		pr <= waiting;
		
	when waiting =>
		tx <= '1';
		if wait_cnt = 2 then
			wait_cnt := 0;
			pr <= start_bit;
			if uart_data >= "01100110" then
				assert false;
				report "SIMULATION IS COMPLETE!!" severity failure;
			end if;
		else
			wait_cnt := wait_cnt +1;
		end if;
	end case;
end if;
end process;


dut: main port map(
clk => clk,
rstn => rstn,
led => led,
uart_rx => tx,
HEX0	=> HEX0,
HEX1	=> HEX1,
HEX2	=> HEX2
);


end beh;