from PIL import Image
import os

def add_padding():
    input_path = "src-tauri/icons/app-icon.png"
    output_path = "src-tauri/icons/app-icon-padded.png"
    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found")
        exit(1)

    try:
        # Open the original image
        img = Image.open(input_path).convert("RGBA")
        width, height = img.size
        
        # Calculate new dimensions (82% size to create ~9% padding on each side)
        # 82% is a common safe zone for macOS icons (approx 1024 -> 840)
        scale_factor = 0.82
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # Resize the image
        # LANCZOS is high-quality downsampling filter
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a new transparent image with original dimensions
        new_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        
        # Calculate paste position to center the image
        x_offset = (width - new_width) // 2
        y_offset = (height - new_height) // 2
        
        # Paste the resized image onto the transparent background
        new_img.paste(resized_img, (x_offset, y_offset))
        
        # Save the result
        new_img.save(output_path, "PNG")
        print(f"Successfully created padded icon at {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        exit(1)

if __name__ == "__main__":
    add_padding()
