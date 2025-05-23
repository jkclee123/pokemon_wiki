import os
import requests
from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
import time

def get_first_paragraph_text(soup):
    """Extract the first paragraph text from the soup."""
    first_p = soup.find('p')
    return first_p.text.strip() if first_p else "No first paragraph found"

def get_summary_section(soup):
    """Extract all paragraphs from the summary section."""
    # Find the summary section (h2 with span id "摘要")
    summary_h2 = soup.find('span', id='.E6.91.98.E8.A6.81')
    if not summary_h2:
        return None
    
    summary_h2 = summary_h2.find_parent('h2')
    if not summary_h2:
        return None
        
    # Get all paragraphs between this h2 and the next h2
    summary_texts = []
    current = summary_h2.find_next_sibling()
    while current and current.name != 'h2':
        if current.name == 'p':
            text = current.text.strip()
            if text:  # Only add non-empty paragraphs
                summary_texts.append(text)
        current = current.find_next_sibling()
    
    return summary_texts if summary_texts else None

def get_episode_content(url):
    """Get both first paragraph and summary section for an episode."""
    try:
        # Add delay to be respectful to the server
        time.sleep(1)
        response = requests.get(url)
        response.encoding = 'utf-8'  # Ensure proper encoding for Chinese characters
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get the first paragraph
        first_text = get_first_paragraph_text(soup)
        
        # Get the summary section
        summary_texts = get_summary_section(soup)
        
        # Combine the texts
        if summary_texts:
            summary = "\n\n".join(summary_texts)
            return f"{first_text}\n\n摘要：\n{summary}"
        else:
            return f"{first_text}\n\nNo summary section found."
            
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
        paragraph = get_episode_content(url)
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
