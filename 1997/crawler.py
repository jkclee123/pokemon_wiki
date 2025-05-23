import os
import requests
from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
import time
import re
from urllib.parse import unquote

def parse_episode_text(url):
    """Extract episode number from URL like 'https://wiki.52poke.com/wiki/宝可梦_第{N}集'"""
    decoded_url = unquote(url)
    pattern = r'(第\d+集)'
    match = re.search(pattern, decoded_url)
    if match:
        return match.group(1)
    return None

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

        episode_text = parse_episode_text(url)
        
        # Get the first paragraph
        first_text = get_first_paragraph_text(soup)
        
        # Get the summary section
        summary_texts = get_summary_section(soup)
        
        # Combine the texts
        return f"{episode_text}\n{first_text}\n\n摘要\n{summary_texts}"
            
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
    
    font_name = None
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

    if not font_name:
        print("Warning: No Chinese font loaded. Text may not display correctly.")
        font_name = 'Helvetica'

    # Create the document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Create styles
    normal_style = ParagraphStyle(
        'normal',
        fontName=font_name,
        fontSize=10,
        leading=14,  # Line height
        wordWrap='CJK',  # Special wrapping for Chinese text
        alignment=4,  # Left alignment
    )

    # Create the story (content)
    story = []
    
    for text in texts:
        # Split into paragraphs
        paragraphs = text.split('\n')
        
        for p in paragraphs:
            if p.strip():
                # Replace newlines with <br/> for PDF
                p = p.replace('\n', '<br/>')
                # Create paragraph with style
                story.append(Paragraph(p, normal_style))
            # Add space between paragraphs
            story.append(Spacer(1, 12))
        
        # Add more space between episodes
        story.append(Spacer(1, 20))

    # Build the PDF
    doc.build(story)

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
    
    # Create final PDF
    print(f"Creating final PDF: {output_file}")
    create_pdf(paragraphs, output_file)
    print("PDF creation completed!")

if __name__ == '__main__':
    main()
