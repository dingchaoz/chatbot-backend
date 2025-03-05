import fitz  # PyMuPDF
from paddleocr import PaddleOCR
import pandas as pd
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import re
from io import StringIO
import os

# Initialize PaddleOCR for text extraction (if needed for images)
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Initialize BLIP model for image captioning (multimodal LLM)
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Function to extract text and images from PDF
def extract_pdf_content(pdf_path):
    doc = fitz.open(pdf_path)
    text_content = ""
    images = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Extract text
        text_content += f"\nPage {page_num + 1}:\n{page.get_text('text')}\n"
        
        # Extract images
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"image_page{page_num + 1}_{img_index}.{image_ext}"
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)
            images.append({"page": page_num + 1, "filename": image_filename})
    
    doc.close()
    return text_content, images

# Function to extract tables from text using regex and pandas
def extract_tables(text):
    tables = []
    table_pattern = r"Table \d+\..*?(?=\n\n|\Z)"  # Adjust regex based on table format
    matches = re.finditer(table_pattern, text, re.DOTALL)
    
    for match in matches:
        table_text = match.group()
        table_lines = table_text.split('\n')
        table_data = []
        headers = []
        title = ""
        for i, line in enumerate(table_lines):
            if i == 0:  # Assuming first line is table title
                title = line.strip()
            elif i == 1:  # Assuming second line is headers
                headers = [h.strip() for h in line.split() if h.strip()]
            else:  # Data rows
                row = [d.strip() for d in line.split() if d.strip()]
                if row and len(row) == len(headers):
                    table_data.append(row)
        
        if table_data and headers:
            df = pd.DataFrame(table_data, columns=headers)
            tables.append({"title": title, "data": df})
    
    return tables

# Function to interpret tables
def interpret_tables(tables):
    interpretations = []
    for i, table in enumerate(tables):
        title = table["title"]
        data_str = table["data"].to_string()
        interpretation = f"Table {i+1}: {title}\nDescription: This table presents data on {title.lower()}. The columns include {', '.join(table['data'].columns)}. Key observations: {data_str[:200]}..."
        interpretations.append({"metadata": f"Table {i+1}", "interpretation": interpretation})
    return interpretations

# Function to interpret images using BLIP
def interpret_images(images):
    interpretations = []
    for i, img_info in enumerate(images):
        img_path = img_info["filename"]
        page_num = img_info["page"]
        try:
            image = Image.open(img_path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt")
            out = model.generate(**inputs)
            caption = processor.decode(out[0], skip_special_tokens=True)
            interpretation = f"Figure {i+1} (Page {page_num}): {caption}"
            interpretations.append({"metadata": f"Figure {i+1} (Page {page_num})", "interpretation": interpretation})
        except Exception as e:
            interpretations.append({"metadata": f"Figure {i+1} (Page {page_num})", "interpretation": f"Error processing image: {str(e)}"})
    return interpretations

# Function to extract figure references from text (if no images are present)
def extract_and_interpret_figure_references(text):
    figures = []
    figure_pattern = r"Fig\. \d+\..*?(?=\n\n|\Z)"
    matches = re.finditer(figure_pattern, text, re.DOTALL)
    
    for i, match in enumerate(matches):
        fig_text = match.group()
        interpretation = f"Figure {i+1}: {fig_text[:100]}... (Assuming a plot or diagram related to HER-2/neu amplification analysis based on context.)"
        figures.append({"metadata": f"Figure {i+1}", "interpretation": interpretation})
    
    return figures

# Main function to process PDF
def process_pdf(pdf_path):
    # Extract text and images
    text_content, images = extract_pdf_content(pdf_path)
    
    # Extract and interpret tables
    tables = extract_tables(text_content)
    table_interpretations = interpret_tables(tables)
    
    # Interpret images if present, otherwise extract figure references from text
    if images:
        figure_interpretations = interpret_images(images)
    else:
        figure_interpretations = extract_and_interpret_figure_references(text_content)
    
    # Combine results
    result = {
        "tables": table_interpretations,
        "figures": figure_interpretations,
        "raw_text": text_content[:500] + "..."  # Truncated for brevity
    }
    
    # Clean up extracted image files
    for img in images:
        os.remove(img["filename"])
    
    return result

# Example usage
if __name__ == "__main__":
    pdf_path = "input.pdf"  # Replace with your actual PDF file path
    try:
        result = process_pdf(pdf_path)
        
        # Output results
        print("Raw Text Excerpt:")
        print(result["raw_text"])
        print("\nTable Interpretations:")
        for table in result["tables"]:
            print(f"{table['metadata']}: {table['interpretation']}")
        print("\nFigure Interpretations:")
        for figure in result["figures"]:
            print(f"{figure['metadata']}: {figure['interpretation']}")
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")