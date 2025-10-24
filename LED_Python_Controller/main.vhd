library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity main is
generic(n: natural := 7);
port(clk,rstn,uart_rx: in std_logic;
HEX0,HEX1,HEX2: out std_Logic_vector(7 downto 0);
led: out std_logic);
end main;

architecture beh of main is
component bin_to_bcd is
generic(
	N: natural:= 7; -- data width.
	BCD_N: natural :=4*3 -- 4 * Number of 7SEG displays (i.e. for 10-bit numbers, it's 4*4 = 16)
);
port(
	binary_in: in std_logic_vector(n-1 downto 0):= (others => '0');
	HEX0,HEX1,HEX2: out std_logic_vector(7 downto 0):= (others => '0')
);
end component;
signal bin_value: std_logic_vector(n -1 downto 0):= (others => '0');

component pll9600
	PORT
	(
		inclk0		: IN STD_LOGIC  := '0';
		c0		: OUT STD_LOGIC 
	);
end component;
signal clk9600: std_logic;

component pwm is
generic(
	max_count: natural := 100;
	n: natural := 7);
port(
	clk,rstn: in std_logic;
	duty: in std_logic_vector(n-1 downto 0);
	pwm_out,ready: out std_Logic
);
end component;
signal pwm_duty: std_logic_vector(n-1 downto 0):= (others => '0');
signal pwm_ready: std_logic;

component uart_rec is
port(
	clk,rx,rstn: in std_logic;
	valid: out std_logic:= '0';
	uart_data: out std_logic_vector(7 downto 0):= (others =>'0')
);
end component;
signal uart_valid: std_logic:= '0';
signal uart_data: std_logic_vector(7 downto 0):= (others => '0');
begin

BCD: bin_to_bcd port map(
	binary_in	=> bin_value,
	HEX0			=> HEX0,
	HEX1			=> HEX1,
	HEX2			=> HEX2
);

uart_pll : pll9600 PORT MAP (
		inclk0	 => clk,
		c0	 => clk9600
	);

pwm_led: pwm port map(
	clk	=> clk,
	duty	=> pwm_duty,
	pwm_out	=> led,
	ready	=> pwm_ready,
	rstn 	=> rstn
);

uart: uart_rec port map(
clk			=> clk9600,
rx				=> uart_rx,
rstn			=> rstn ,
valid			=> uart_valid,
uart_data	=> uart_data
);

process(clk)
begin
if rising_edge(clk) then
	if (uart_valid ='1' and pwm_ready = '1') then
		pwm_duty <= uart_data(n-1 downto 0);
		bin_value <= uart_data(n-1 downto 0);
	end if;
end if;
end process;

end beh;