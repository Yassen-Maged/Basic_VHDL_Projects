from PIL import Image
import struct

def convert_image_to_bin(input_image_path, output_bin_path, width=640, height=480):
    # Open image and resize to 640x480
    img = Image.open(input_image_path).convert('RGB')
    img = img.resize((width, height))
    pixels = list(img.getdata())

    with open(output_bin_path, 'wb') as f:
        for r, g, b in pixels:
            # Convert 8-bit to 4-bit by dividing by 17 (approx.)
            r4 = r >> 4  # or r // 17
            g4 = g >> 4
            b4 = b >> 4

            # Format: 0000 RRRR GGGG BBBB
            pixel16 = (r4 << 8) | (g4 << 4) | b4

            # Write as Little-endian (LSB first)
            f.write(struct.pack('<H', pixel16))

    print(f"Binary file saved as {output_bin_path}")

# Example usage
convert_image_to_bin('me.jpg', 'me_conv.bin')
