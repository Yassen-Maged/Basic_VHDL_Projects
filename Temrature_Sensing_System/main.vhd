library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity main is
port(
clk10,rst_n: in std_logic:= '0';
LEDR: OUT STD_LOGIC_VECTOR(9 DOWNTO 0):= (others => '0');
tx: out std_logic := 'Z';
HEX0,HEX1,HEX2,HEX3,HEX4,HEX5: out std_logic_vector(7 downto 0):= (others => '1')
);
end main;

architecture beh of main is
----------------------Temprature (ADC)------------------------------
	component sys1 is
		port (
			adc_clk_clk           : in  std_logic                     := 'X';             -- clk
			reset_reset_n         : in  std_logic                     := 'X';             -- reset_n
			
			adc_rsp_valid         : out std_logic;                                        -- valid
			adc_rsp_channel       : out std_logic_vector(4 downto 0);                     -- channel
			adc_rsp_data          : out std_logic_vector(11 downto 0);                    -- data
			adc_rsp_startofpacket : out std_logic;                                        -- startofpacket
			adc_rsp_endofpacket   : out std_logic;                                        -- endofpacket
			
			adc_cmd_valid         : in  std_logic                     := 'X';             -- valid
			adc_cmd_channel       : in  std_logic_vector(4 downto 0)  := (others => 'X'); -- channel
			adc_cmd_startofpacket : in  std_logic                     := 'X';             -- startofpacket
			adc_cmd_endofpacket   : in  std_logic                     := 'X';             -- endofpacket
			adc_cmd_ready         : out std_logic                                         -- ready
		);
	end component sys1;
signal data,data_r: std_logic_vector(11 downto 0):= (others => '0');
signal rsp_valid,read_temp: std_logic := '0'; -- ADC Response Valid
signal int_temp: natural := 0; --Integer value of the Temprature
----------------------BCD------------------------------
	component bin_to_bcd is
		generic(N: natural:= 12; -- data width.
			BCD_N: natural :=4*3 -- 4 * Number of 7SEG displays (for 10-bit numbers, it's 4*4 = 16)
		);
		port(
			binary_in: in std_logic_vector(n-1 downto 0);
			HEX0,HEX1,HEX2: out std_logic_vector(7 downto 0);
			ones,tens,hunds: out natural range 0 to 9
		);
	end component;
signal ones,tens,hunds: natural:= 0;
signal binary_in: std_logic_vector(7 downto 0):= (others => '0');

----------------------UART------------------------------
	component PLL9600 IS
		PORT
		(
			inclk0		: IN STD_LOGIC  := '0'; -- 10MHz
			c0		: OUT STD_LOGIC 		--9600 Hz (104166.6667 ns)
		);
	END component;
type ascii_map is array (0 to 11) of std_logic_vector(7 downto 0);
constant ascii: ascii_map:= (
"00110000", "00110001", "00110010", "00110011", --0 1 2  3
"00110100", "00110101", "00110110", "00110111", --4 5 6  7
"00111000", "00111001", "00001010", "00001101"  --8 9 LF CR
);
type state is (idle,start_bit,data_send,stop_bit);
signal pr: state:= idle;
signal bit_counter: natural range 0 to 7:= 0;
signal char_counter: natural range 0 to 4:= 0;
signal data_to_send: std_logic_vector(7 downto 0):= ascii(4);
signal clk9600: std_logic:= '0';
constant baud: natural := 9600;
signal delay_counter: natural range 0 to baud/2 -1:= 0;-- delay for 0.5 sec between characters
----------------------------------------------------

begin

u0 : component sys1
	port map (
		adc_clk_clk           => clk10,         -- adc_clk.clk
		reset_reset_n         => rst_n,         -- reset.reset_n
		
		adc_rsp_valid         => rsp_valid, -- adc_rsp.valid
		adc_rsp_data          => data,      --        .data
		adc_cmd_valid         => read_temp, -- adc_cmd.valid
		adc_cmd_channel       => "00001",   --        .channel
		adc_cmd_startofpacket => '1', 		--    	 .startofpacket
		adc_cmd_endofpacket   => '1'   		--    	 .endofpacket
	);

process(rsp_valid)
begin
if rising_edge(rsp_valid) then
	data_r <= data;
end if;
end process;
--Based on the equation in the ADC IP documentation:
-- Temprature = ADC_output_value * Vref/2^12
int_temp<= (500*to_integer(unsigned(data_r)))/4096;
--Keep in mind that the sensor resolution is 10mv
--Vref = 5V -> 500 in our equation.
---

	Temp_value : component bin_to_bcd
		generic map (n => 8, BCD_N => 4*3)
		port map(
			binary_in => binary_in,
			HEX0 => HEX0,
			HEX1 => HEX1,
			HEX2 => HEX2,
			ones => ones,
			tens => tens,
			hunds => hunds
		);

binary_in <= std_logic_vector(to_unsigned(int_temp,8));
---

uart_clk: pll9600 port map(
inclk0 => clk10,
c0 => clk9600
);


data_to_send <= ascii(hunds) when char_counter = 0 else
					 ascii(tens)  when char_counter = 1 else
					 ascii(ones)  when char_counter = 2 else
					 ascii(11)    when char_counter = 3 else --CR
					 ascii(10)    when char_counter = 4 else --LF
					 ascii(10);

UART:process(rst_n,clk9600)
begin
if rst_n = '0' then
	read_temp <= '0';
	delay_counter <= 0;
	pr <= idle;
	tx <= '1';
	bit_counter <= 0;
	char_counter <= 0;
elsif rising_edge(clk9600) then
	case pr is
	when idle =>
		tx <= '1';
		delay_counter <= delay_counter +1;
		pr <= idle;
		read_temp <= '0';
		bit_counter <= 0;
		if delay_counter >= baud/2 -1 then -- delay for 0.5 sec
			delay_counter <= 0;
			pr <= start_bit;
		elsif delay_counter = 0 and char_counter = 0 then
			read_temp <= '1';
		end if;

	when start_bit =>
		tx <= '0';
		pr <= data_send;

	when data_send =>
		tx <= data_to_send(bit_counter);
		if bit_counter >= 7 then
			bit_counter <= 0;
			pr <= stop_bit;
		else
			bit_counter <= bit_counter +1;
			pr <= data_send;
		end if;

	when stop_bit =>
		tx <= '1';
		pr <= idle;
		if (char_counter >= 4) then
			char_counter <= 0;
		else
			char_counter <= char_counter +1;
		end if;
	end case;	
end if;
end process UART;



ledr(2 downto 0) <= std_logic_vector(to_unsigned(char_counter,3));
ledr(9) <= not rst_n;
HEX3 <= (OTHERS => '1');
HEX4 <= (OTHERS => '1');
HEX5 <= (OTHERS => '1');
end beh;