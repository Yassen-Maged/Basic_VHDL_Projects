library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity main is
generic(
IV_n: natural := 10; -- the length of the Initial value used in key generation.
n: natural := 8 -- the length of the plain/cipher text.
);
port(
CLK: in std_logic;
Encrypt: in std_logic:= '1'; -- '1' for encrypt and '0' for decrypt.
Encrypt_LED: out std_logic:= 'Z'; -- ON for encrypt and OFF for decrypt (just indicator).
input_word: in std_logic_vector(0 to n-1):= (others => '0'); -- 8 Switches.
output_word: out std_logic_vector(0 to n-1):= (others => 'Z')-- 8 LEDs.
);
end main;

architecture beh of main is
---------------------PERMUTATION FUNCTION----------------------------------
type Perm is array(0 to IV_n-1) of natural; -- array of the indices of every permutation block.
function permute(message: unsigned; bits_order: perm; output_length: natural)
 return unsigned is
variable permuted_message: unsigned(0 to output_length -1);
begin

	for i in 0 to output_length -1 loop
		permuted_message(i) := message(bits_order(i) -1);
	end loop;
	return permuted_message;
end; 
------------------KEY GENERATION FUNCTION-----------------------------
function Key_generation (IV:unsigned(0 to 9); P10,P8: perm)
 return unsigned is
variable temp: unsigned(0 to IV_n-1):= (others => '0'); -- stores the result of every process.
variable L,R: unsigned(0 to IV_n/2-1):= (others => '0');-- the left and right parts of temp
variable k1,k2: unsigned(0 to n-1):= (others => '0');
begin
	
	temp:= permute(IV,P10,IV_n); -- permute with P10 
	L:= temp(0 to IV_n/2-1) rol 1; --Rotate left by 1.
	R:= temp(IV_n/2 to IV_n-1) rol 1; --Rotate left by 1.
	temp := L&R;
	
	temp(0 to n-1):= permute(temp,P8,n); -- permute with P8 
	k1 := temp(0 to n-1); --Key1
	
	L := L rol 2; --Rotate left by 2.
	R := R rol 2; --Rotate left by 2.
	temp := L&R;
	
	temp(0 to n-1):= permute(temp,P8,n);
	k2 := temp(0 to n-1); -- Key 2.
	
	return (k1&k2);
end; 

constant IV: unsigned(0 to IV_n-1):= "1010000010";
constant P10: perm := (3,5,2,7,4,10,1,9,8,6);
constant P8: perm := (6,3,7,4,8,5,10,9,0,0);
signal k1: unsigned(0 to n-1):= Key_generation(IV,P10,P8)(0 to n-1);
signal k2: unsigned(0 to n-1):= Key_generation(IV,P10,P8)(n to 2*n-1);
----------------------------------------------------------------
----------------------S-BOX FUNCTION-------------------------------
type sbox is array (0 to 15) of natural; -- array of 2-bit numbers
function sbox_out(s: sbox; index: unsigned(0 to 3)) return unsigned is
variable col, row, idx: natural := 0; --column, row, index of element.
variable s_value: unsigned(1 downto 0):= "00"; -- the output value.
variable x: unsigned(1 downto 0):="00"; --temporary variable
begin												 --(used to mitigate some simulation errors).
x:=index(0) & index(3);
row := to_integer(x) * 4; -- the index of the first element of the second row is 4
x:= index(1) & index(2);  				--and for the one of the third row is 8...etc.
col := to_integer(x); 
idx := row+col; -- the exact index of the desired element in the S-box.
s_value := to_unsigned(s(idx),2);
return s_value;
end;

constant s0: sbox := (1,0,3,2,3,2,1,0,0,2,1,3,3,1,3,2);
constant s1: sbox := (0,1,2,3,2,0,1,3,3,0,1,0,2,1,0,3);
----------------------------------------------------------------
----------------------ENCRYPTION/DECRYPTION FUNCTION------------------------------------
function SDES_Enc(word: std_logic_vector(0 to n-1); key1,key2: unsigned(0 to n-1);
s0,s1: sbox; IP,EP,P4,IP_1: perm; Encrypt: boolean; First_Round: boolean)
 return std_logic_vector is
variable L,R: unsigned(0 to 3):=(others => '0'); -- split the input in half.
variable temp: unsigned(0 to n-1):=(others => '0'); -- Stores the final result and the result of every process.
variable L1,R1: unsigned(0 to 1):=(others => '0'); -- stores the output of the S-boxes.
begin
	temp:= unsigned(word); -- convert the input to be unsigned.
	if First_Round then 
		temp := permute(temp,IP,n); -- Initial Permutation.
	end if;
	L:= temp(0 to 3);
	R:= temp(4 to n-1);
	temp:= permute(R,EP,8); -- Extension and Permutation with E/P.
	
	if First_Round then
		if Encrypt then
			temp:= temp xor key1;
		else
			temp:= temp xor key2; -- switch keys in 
		end if;
	else -- Final Round
		if Encrypt then
			temp:= temp xor key2;
		else
			temp:= temp xor key1;
		end if;
	end if;
	
	L1:= sbox_out(s0,temp(0 to 3));
	R1:= sbox_out(s1,temp(4 to n-1));
	temp(0 to 3):= unsigned(L1&R1);
	
	temp(0 to 3):= permute(temp(0 to 3),P4,4); --Permute with P4.
	L:= temp(0 to 3) xor L;
	
	if First_Round then 
		temp:= R & L; --Switch.
	else -- Final Round.
		temp:= L&R; -- no switching.
		temp:= permute(temp, IP_1, n); --Final Permutation.
	end if;
	return std_logic_vector(temp);
end;

constant IP: perm:= (2,6,3,1,4,8,5,7,0,0);
constant EP: perm:= (4,1,2,3,2,3,4,1,0,0);
constant IP_1: perm:= (4,1,3,5,7,2,8,6,0,0);
constant P4: perm:= (2,4,3,1,0,0,0,0,0,0);
----------------------------------------------------------------

begin

process(clk)
variable temp: std_logic_vector(0 to n-1):= (others => '0'); -- stores the first round output.
begin
if rising_edge(clk) then
	if encrypt = '1' then
		temp:= -- Round #1
		sdes_enc(
		word => input_word, key1 => k1,
		key2 => k2, s0 => s0, s1 => s1,
		IP => IP, EP => EP, P4 => P4, IP_1 => IP_1,
		Encrypt => true, First_Round => true
		);
		
		output_word <= -- Final Round
		sdes_enc(
		word => temp, key1 => k1,
		key2 => k2, s0 => s0, s1 => s1,
		IP => IP, EP => EP, P4 => P4, IP_1 => IP_1,
		Encrypt => true, First_Round => false
		);
	else
		temp:= -- Round #1
		sdes_enc( 
		word => input_word, key1 => k1,
		key2 => k2, s0 => s0, s1 => s1,
		IP => IP, EP => EP, P4 => P4, IP_1 => IP_1,
		Encrypt => false, First_Round => true
		);
		
		output_word<= -- Final Round
		sdes_enc(
		word => temp, key1 => k1,
		key2 => k2, s0 => s0, s1 => s1,
		IP => IP, EP => EP, P4 => P4, IP_1 => IP_1,
		Encrypt => false, First_Round => false
		);
	end if;
end if;
end process;
end beh;