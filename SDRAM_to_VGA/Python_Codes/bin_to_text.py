def bin_to_vhdl_mem(bin_file_path, output_vhdl_mem_path):
    with open(bin_file_path, 'rb') as f:
        data = f.read()

    with open(output_vhdl_mem_path, 'w') as out:
        for i in range(0, len(data), 2):
            word = int.from_bytes(data[i:i+2], byteorder='little')
            out.write(f"{word:04X}\n")  # write as hex

    print(f"VHDL-compatible memory file saved as {output_vhdl_mem_path}")

# Example usage:
bin_to_vhdl_mem("me_conv.bin", "image_data.mem")
