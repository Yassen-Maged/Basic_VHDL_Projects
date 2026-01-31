component bcd_7seg is
generic(d_width: natural:= 3; -- data width.
n_display: natural:= 1 -- Number of 7SEG displays (i.e., for 10-bit numbers, it's 4 displays)
);
port(
binary_in: in std_logic_vector(d_width-1 downto 0);
HEX: out std_logic_vector(8*n_display-1 downto 0)
);
end component;

BIN_BCD: bcd_7seg generic map(
d_width => 8, --input data width
n_display => 3-- number of 7SEG displays
) port map (
HEX(7 downto 0) => HEX0,
HEX(15 downto 8) => HEX1,
HEX(23 downto 16) => HEX2,
-- and so on.
binary_in => din
);
