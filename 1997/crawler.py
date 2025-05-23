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
    """Extract episode text from URL like '第{N}集'"""
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
    summary_list = []
    current = summary_h2.find_next_sibling()
    while current and current.name != 'h2':
        if current.name == 'p':
            text = current.text.strip()
            if text:  # Only add non-empty paragraphs
                summary_list.append(text)
        current = current.find_next_sibling()
    
    # Join the paragraphs with newlines
    summary_text =  "\n".join(summary_list) if summary_list else None
    return summary_text

def get_main_events(soup):
    """Extract the main events section (主要事件) and its bullet points."""
    # Find the main events section (h2 with span id "主要事件")
    events_h2 = soup.find('span', id='.E4.B8.BB.E8.A6.81.E4.BA.8B.E4.BB.B6')
    if not events_h2:
        return None
    
    events_h2 = events_h2.find_parent('h2')
    if not events_h2:
        return None
        
    # Get the ul that follows this h2
    ul = events_h2.find_next_sibling('ul')
    if not ul:
        return None
    
    # Extract all list items
    events = []
    for li in ul.find_all('li', recursive=False):
        event_text = li.get_text(strip=True)
        if event_text:
            events.append(event_text)
    
    return events if events else None

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
        summary_text = get_summary_section(soup)
        summary_text = summary_text if summary_text else "No summary found."

        # Get main events
        main_events = get_main_events(soup)
        events_text = "\n• " + "\n• ".join(main_events) if main_events else "No main events found."
        
        # Combine the texts
        return f"{episode_text}\n{first_text}\n摘要\n{summary_text}\n主要事件：\n{events_text}"
            
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return f"Error: {str(e)}"

def create_pdf(texts, output_file):
    # Try multiple Chinese fonts that might be available on macOS
    chinese_fonts = [
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
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=48
    )

    # Create styles
    title_style = ParagraphStyle(
        'title',
        fontName=font_name,
        fontSize=12,
        leading=16,  # Line spacing for title
        spaceAfter=12,  # Space after title
        alignment=1,  # Center alignment
    )

    normal_style = ParagraphStyle(
        'normal',
        fontName=font_name,
        fontSize=10,
        leading=14,  # Line spacing for normal text
        spaceBefore=6,  # Space before paragraph
        spaceAfter=6,  # Space after paragraph
        wordWrap='CJK',
        alignment=4,  # Left alignment
    )

    summary_style = ParagraphStyle(
        'summary',
        fontName=font_name,
        fontSize=10,
        leading=14,  # Line spacing for summary
        spaceBefore=12,  # More space before summary section
        spaceAfter=6,
        wordWrap='CJK',
        alignment=4,
    )

    # Create the story (content)
    story = []
    
    for text in texts:
        # Split into sections
        sections = text.split('\n')
        
        for i, section in enumerate(sections):
            if section.strip():
                if i == 0:  # First line (episode number)
                    story.append(Paragraph(section, title_style))
                elif section.startswith('摘要') or section.startswith('主要事件'):
                    story.append(Paragraph(section, summary_style))
                elif section.startswith('•'):
                    # Indent bullet points
                    story.append(Paragraph('    ' + section, normal_style))
                else:
                    story.append(Paragraph(section, normal_style))

        # Add more space between episodes
        story.append(Spacer(1, 30))

    # Build the PDF
    doc.build(story)

def main():
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Read URLs from file
    urls_file = os.path.join(project_root, '1997', 'urls.txt')
    output_file = os.path.join(project_root, '1997', '1997_episodes.pdf')
    
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
