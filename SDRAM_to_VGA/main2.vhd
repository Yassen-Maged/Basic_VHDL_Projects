library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity main2 is
generic(xy: natural := 640*480;
vga_width: natural := 12);
port(
clk50,rstn:in std_logic:= '0';
R,B,G: out std_logic_vector(3 downto 0);
Hsync, Vsync: out std_logic;
DRAM_ADDR        	: out   std_logic_vector(12 downto 0):= (others => 'Z');
DRAM_BA          	: out   std_logic_vector(1 downto 0):= (others => 'Z');
DRAM_CAS_N       	: out   std_logic:='Z';
DRAM_CKE         	: out   std_logic:='Z';
DRAM_CLK        	: out   std_logic:='Z';
DRAM_CS_N        	: out   std_logic:='Z';
DRAM_DQ     		: inout std_logic_vector(15 downto 0):= (others => 'X');
DRAM_LDQM    		: out   std_logic:='Z';
DRAM_RAS_N		   : out   std_logic:='Z';
DRAM_UDQM		   : out   std_logic:='Z';
DRAM_WE_N		   : out   std_logic:='Z'
);
end main2;

architecture beh of main2 is
--------------------SDRAM--------------------
	component sys1 is
		port (
			sdram_s1_address         : in    std_logic_vector(24 downto 0) := (others => 'X'); -- address
			sdram_s1_byteenable_n    : in    std_logic_vector(1 downto 0)  := (others => 'X'); -- byteenable_n
			sdram_s1_chipselect      : in    std_logic                     := 'X';             -- chipselect
			sdram_s1_writedata       : in    std_logic_vector(15 downto 0) := (others => 'X'); -- writedata
			sdram_s1_read_n          : in    std_logic                     := 'X';             -- read_n
			sdram_s1_write_n         : in    std_logic                     := 'X';             -- write_n
			sdram_s1_readdata        : out   std_logic_vector(15 downto 0);                    -- readdata
			sdram_s1_readdatavalid   : out   std_logic;                                        -- readdatavalid
			sdram_s1_waitrequest     : out   std_logic;                                        -- waitrequest
			
			sdram_wire_addr          : out   std_logic_vector(12 downto 0);                    -- addr
			sdram_wire_ba            : out   std_logic_vector(1 downto 0);                     -- ba
			sdram_wire_cas_n         : out   std_logic;                                        -- cas_n
			sdram_wire_cke           : out   std_logic;                                        -- cke
			sdram_wire_cs_n          : out   std_logic;                                        -- cs_n
			sdram_wire_dq            : inout std_logic_vector(15 downto 0) := (others => 'X'); -- dq
			sdram_wire_dqm           : out   std_logic_vector(1 downto 0);                     -- dqm
			sdram_wire_ras_n         : out   std_logic;                                        -- ras_n
			sdram_wire_we_n          : out   std_logic;                                        -- we_n

			sdram_ctrl_clk100_clk    : in    std_logic                     := 'X';             -- clk
			sdram_ctrl_reset_reset_n : in    std_logic                     := 'X'              -- reset_n
		);
	end component sys1;
signal init_cnt: natural range 0 to 10100:= 0; --SDRAM initialization wait for 101 us, with clk = 10 ns.
signal prev_addr,addr: natural range 0 to xy-1 :=0; -- SDRAM cell address
signal sdram_addr: std_logic_vector (24 downto 0);
signal read_n, readdatavalid, waitrequest: std_logic:='1'; -- SDRAM Control signals
signal sdram_dqm: std_logic_vector(1 downto 0); -- PHY layer
signal sdram_rdata: std_logic_vector(15 downto 0):=( others =>'0'); -- read data output
--------------------VGA--------------------
COMPONENT VGA_IP
	port(
		-- Clock and Reset
		clk    : in  STD_LOGIC;
		reset_n      : in  STD_LOGIC;
		
		-- Pixel Data Interface
		data_in   : in  STD_LOGIC_VECTOR(11 downto 0);  -- 4-bit R, 4-bit G, 4-bit B
		valid  : in  STD_LOGIC;                       -- Data valid signal
		ready  : out STD_LOGIC;                       -- Ready to accept new pixel
		
		-- VGA Output Signals
		hsync       : out STD_LOGIC;
		vsync       : out STD_LOGIC;
		red        : out STD_LOGIC_VECTOR(3 downto 0);
		green        : out STD_LOGIC_VECTOR(3 downto 0);
		blue        : out STD_LOGIC_VECTOR(3 downto 0)		
	);
end component VGA_IP;

signal vga_valid,vga_ready : std_logic:= '0';
signal pixel: std_logic_vector(vga_width-1 downto 0);

--------------------PLL--------------------
component pll0 IS
	PORT
	(
		areset		: IN STD_LOGIC  := '0';
		inclk0		: IN STD_LOGIC  := '0';
		c0		: OUT STD_LOGIC ; -- to VGA clock
		c1		: OUT STD_LOGIC ; -- to SDRAM Controller
		c2		: OUT STD_LOGIC 	-- to SDRAM PHY (lagging -3ns than the controller clock)
	);
END component pll0;

signal rst,clk100,SDRAM_CLK,VGA_CLK: std_logic:= '1';
----------------------------------------

begin
DRAM_LDQM <= sdram_dqm(0);
DRAM_UDQM <= sdram_dqm(1);
DRAM_CLK <= SDRAM_CLK;
rst <= not(rstn);
sdram_addr <= std_logic_vector(to_unsigned(addr,sdram_addr'length));


pll: pll0 PORT MAP (
		areset	 => rst,
		inclk0	 => clk50,
		c0	 => VGA_CLK, 		-- 25MHz clock for VGA
		c1	 => clk100, 		-- 100MHz clock for SDRAM controller
		c2	 => SDRAM_CLK		-- 100MHz clock with -3 ns phase shift for SDRAM PHY
	);

	u0 : component sys1
		port map (
			sdram_ctrl_clk100_clk    => clk100,    			--  sdram_ctrl_clk100.clk
			sdram_ctrl_reset_reset_n => rstn,  					--  sdram_ctrl_reset.reset_n
			sdram_s1_address         => sdram_addr,         --  sdram_s1.address
			sdram_s1_byteenable_n    => "00",    				--          .byteenable_n
			sdram_s1_chipselect      => '1',     				--          .chipselect
			sdram_s1_writedata       => ( others =>'Z'),    --          .writedata
			sdram_s1_read_n          => read_n,          	--          .read_n
			sdram_s1_write_n         => '1',         			--          .write_n
			sdram_s1_readdata        => sdram_rdata,        	--          .readdata
			sdram_s1_readdatavalid   => readdatavalid,   	--          .readdatavalid
			sdram_s1_waitrequest     => waitrequest,     	--          .waitrequest
			
			sdram_wire_addr          => DRAM_ADDR,          --  sdram_wire.addr
			sdram_wire_ba            => DRAM_BA,            --            .ba
			sdram_wire_cas_n         => DRAM_CAS_N,         --            .cas_n
			sdram_wire_cke           => DRAM_CKE,           --            .cke
			sdram_wire_cs_n          => DRAM_CS_N,          --            .cs_n
			sdram_wire_dq            => DRAM_DQ,            --            .dq
			sdram_wire_dqm           => (sdram_dqm),  		--            .dqm
			sdram_wire_ras_n         => DRAM_RAS_N,         --            .ras_n
			sdram_wire_we_n          => DRAM_WE_N          	--            .we_n
			
			
		);
		
-----------------SDRAM-----------------
SDRAM_process:process(rstn,clk100)
begin
if rstn = '0' then
	prev_addr <= 0;
	init_cnt <= 0;
elsif rising_edge(clk100) then
	read_n <= '1';
	if init_cnt >= 10100 then -- check whether the sdram has finished its initialization.
		if prev_addr /= addr then -- avoid repeated reading commands.
			if waitrequest = '0' then -- check if the sdram is ready for read command.
				read_n <= '0';
				prev_addr <= addr;
			end if;
		end if;
	else
		init_cnt <= init_cnt +1;
	end if;
end if;
end process SDRAM_process;

-----------------VGA-----------------
vga_controller: vga_ip
port map(
clk => VGA_CLK,
reset_n => rstn,

data_in =>pixel,
valid => vga_valid,
ready => vga_ready,

hsync => Hsync,
vsync => Vsync,
red	 => R,
green	 => G,
blue	 => B
);

process(readdatavalid)
begin
if readdatavalid = '1' then
	pixel <= sdram_rdata(11 downto 0); -- latch the sdram output data.
end if;
end process;

process(rstn,VGA_CLK)
begin
if rstn = '0' then
	addr <= 0;
elsif rising_edge(VGA_CLK) then
	if vga_ready = '1' then --obtain the pixel colors.
		if addr = xy-1 then --end of the frame
			addr <= 0;
		else
			addr <= addr + 1;
		end if;
	end if;
end if;
end process;
vga_valid <= '1';



end beh;