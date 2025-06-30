library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity vga_ip is
    Port (
        clk        : in  std_logic;              -- 25 MHz clock
        reset_n    : in  std_logic;              -- Active-low reset
        data_in    : in  std_logic_vector(11 downto 0); -- {R,G,B} = 4 bits each
        valid      : in  std_logic;              -- Input valid signal
        ready      : out std_logic;              -- Output ready signal

        hsync      : out std_logic;
        vsync      : out std_logic;
        red        : out std_logic_vector(3 downto 0);
        green      : out std_logic_vector(3 downto 0);
        blue       : out std_logic_vector(3 downto 0)
    );
end vga_ip;

architecture Behavioral of vga_ip is

    constant H_VISIBLE   : integer := 640;
    constant H_FRONT     : integer := 16;
    constant H_SYNC      : integer := 96;
    constant H_BACK      : integer := 48;
    constant H_TOTAL     : integer := H_VISIBLE + H_FRONT + H_SYNC + H_BACK; --800

    constant V_VISIBLE   : integer := 480;
    constant V_FRONT     : integer := 10;
    constant V_SYNC      : integer := 2;
    constant V_BACK      : integer := 33;
    constant V_TOTAL     : integer := V_VISIBLE + V_FRONT + V_SYNC + V_BACK; --525

    signal h_count       : integer range 0 to H_TOTAL - 1 := 0;
    signal v_count       : integer range 0 to V_TOTAL - 1 := 0;

    signal pixel_active  : std_logic := '0';
    signal data_reg      : std_logic_vector(11 downto 0) := (others => '0');

begin

    process(clk, reset_n)
    begin
        if reset_n = '0' then
            h_count <= 0;
            v_count <= 0;
            data_reg <= (others => '0');
        elsif rising_edge(clk) then
            -- Horizontal Counter
            if h_count = H_TOTAL - 1 then
                h_count <= 0;

                -- Vertical Counter
                if v_count = V_TOTAL - 1 then
                    v_count <= 0;
                else
                    v_count <= v_count + 1;
                end if;
            else
                h_count <= h_count + 1;
            end if;

            -- Load pixel only in visible region
            if pixel_active = '1' and valid = '1' then
                data_reg <= data_in;
            end if;
        end if;
    end process;

    -- Output enable for pixel data
    pixel_active <= '1' when (h_count < H_VISIBLE and v_count < V_VISIBLE) else '0';

    -- Handshake
    ready <= pixel_active;

    -- Sync pulses (active low)
    hsync <= '0' when (h_count >= H_VISIBLE + H_FRONT and h_count < H_VISIBLE + H_FRONT + H_SYNC) else '1';
    vsync <= '0' when (v_count >= V_VISIBLE + V_FRONT and v_count < V_VISIBLE + V_FRONT + V_SYNC) else '1';

    -- RGB outputs
    red   <= data_reg(11 downto 8) when pixel_active = '1' else (others => '0');
    green <= data_reg(7 downto 4)  when pixel_active = '1' else (others => '0');
    blue  <= data_reg(3 downto 0)  when pixel_active = '1' else (others => '0');

end Behavioral;
