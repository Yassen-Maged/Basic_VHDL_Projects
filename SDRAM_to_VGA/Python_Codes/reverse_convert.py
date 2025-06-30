from PIL import Image
import struct

def convert_bin_to_image(bin_file_path, output_image_path, width=640, height=480):
    # Open the .bin file in binary mode
    with open(bin_file_path, 'rb') as f:
        data = f.read()

    # Make sure the size is correct
    expected_size = width * height * 2  # 2 bytes per pixel
    if len(data) != expected_size:
        raise ValueError(f"Unexpected file size: expected {expected_size} bytes, got {len(data)}")

    # Prepare a list to store (R, G, B) tuples
    pixels = []

    for i in range(0, len(data), 2):
        # Read 16-bit value
        word = struct.unpack('<H', data[i:i+2])[0]  # big-endian

        # Extract R, G, B components
        R = (word >> 8) & 0x0F
        G = (word >> 4) & 0x0F
        B = word & 0x0F

        # Scale 4-bit values to 8-bit (0-255)
        R *= 17
        G *= 17
        B *= 17

        pixels.append((R, G, B))

    # Create image and set pixels
    img = Image.new('RGB', (width, height))
    img.putdata(pixels)
    img.save(output_image_path)
    print(f"Image saved as {output_image_path}")

# Example usage
convert_bin_to_image('me_conv.bin', 'output_image_reverse.png')
