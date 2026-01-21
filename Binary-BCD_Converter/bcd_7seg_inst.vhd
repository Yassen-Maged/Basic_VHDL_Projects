BIN_BCD: bcd_7seg generic map(
d_width => 8, --input data width
n_display => 3-- number of 7SEG displays
) port map (
HEX(3 downto 0) => HEX0,
HEX(7 downto 4) => HEX1,
HEX(11 downto 8) => HEX2,
-- and so on.
binary_in => din
);