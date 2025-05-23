import os
import requests
from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
import time

def get_first_paragraph(url):
    try:
        # Add delay to be respectful to the server
        time.sleep(1)
        response = requests.get(url)
        response.encoding = 'utf-8'  # Ensure proper encoding for Chinese characters
        soup = BeautifulSoup(response.text, 'html.parser')
        first_p = soup.find('p')
        return first_p.text if first_p else "No paragraph found"
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return f"Error: {str(e)}"

def create_pdf(texts, output_file):
    # Try multiple Chinese fonts that might be available on macOS
    chinese_fonts = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/Library/Fonts/Arial Unicode.ttf',
    ]
    
    font_name = 'Helvetica'  # Default fallback
    for font_path in chinese_fonts:
        try:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Chinese', font_path))
                font_name = 'Chinese'
                print(f"Successfully loaded Chinese font: {font_path}")
                break
        except Exception as e:
            print(f"Failed to load font {font_path}: {e}")
            continue

    if font_name == 'Helvetica':
        print("Warning: Using Helvetica font. Chinese characters may not display correctly.")

    c = canvas.Canvas(output_file, pagesize=A4)
    width, height = A4
    
    # Set font and size
    c.setFont(font_name, 10)
    
    y = height - 50  # Start from top with margin
    line_height = 15
    
    for i, text in enumerate(texts, 1):
        if y < 50:  # If near bottom of page, create new page
            c.showPage()
            y = height - 50
            c.setFont(font_name, 10)
        
        # Add episode number and text
        episode_text = f"{text}"
        
        # Split text into lines that fit the page width
        # For Chinese text, we'll split by characters if needed
        if font_name == 'Helvetica':
            # For non-Chinese font, split by words
            words = episode_text.split()
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if c.stringWidth(test_line, font_name, 10) < width - 100:
                    current_line.append(word)
                else:
                    if current_line:
                        c.drawString(50, y, ' '.join(current_line))
                        y -= line_height
                        current_line = [word]
                    else:
                        c.drawString(50, y, word)
                        y -= line_height
                        current_line = []
                
                if y < 50:
                    c.showPage()
                    y = height - 50
                    c.setFont(font_name, 10)
            
            if current_line:
                c.drawString(50, y, ' '.join(current_line))
                y -= line_height * 2
        else:
            # For Chinese font, we'll draw character by character if needed
            x = 50
            for char in episode_text:
                char_width = c.stringWidth(char, font_name, 10)
                if x + char_width > width - 50:
                    y -= line_height
                    x = 50
                    if y < 50:
                        c.showPage()
                        y = height - 50
                        c.setFont(font_name, 10)
                c.drawString(x, y, char)
                x += char_width
            y -= line_height * 2
        
        if y < 50:  # Check if we need a new page
            c.showPage()
            y = height - 50
            c.setFont(font_name, 10)
    
    c.save()

def main():
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Read URLs from file
    urls_file = os.path.join(project_root, '1997', 'urls.txt')
    output_file = os.path.join(project_root, '1997', 'pokemon_episodes.pdf')
    
    print(f"Reading URLs from: {urls_file}")
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(urls)} URLs to process")
    
    # Get paragraphs for each URL
    paragraphs = []
    for i, url in enumerate(urls, 1):
        print(f"Processing URL {i}/{len(urls)}: {url}")
        paragraph = get_first_paragraph(url)
        paragraphs.append(paragraph)
        
        # Save progress every 10 episodes
        if i % 10 == 0:
            print(f"Saving progress... ({i}/{len(urls)} episodes processed)")
            create_pdf(paragraphs, output_file)
    
    # Create final PDF
    print(f"Creating final PDF: {output_file}")
    create_pdf(paragraphs, output_file)
    print("PDF creation completed!")

if __name__ == '__main__':
    main()
