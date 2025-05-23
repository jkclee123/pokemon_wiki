import os
import requests
from bs4 import BeautifulSoup
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
import time
import re
from urllib.parse import unquote
from opencc import OpenCC
import argparse

# Initialize OpenCC converter
cc = OpenCC('s2t')  # Simplified to Traditional

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
    summary_text = "\n".join(summary_list) if summary_list else None
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
        
        # Convert all text to Traditional Chinese at once
        content = f"{episode_text}\n{first_text}\n摘要\n{summary_text}\n主要事件：\n{events_text}"
        return cc.convert(content)
            
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return f"Error: {str(e)}"

def load_chinese_font():
    """Load and register Chinese font."""
    chinese_fonts = [
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/Library/Fonts/Arial Unicode.ttf',
    ]
    
    for font_path in chinese_fonts:
        try:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Chinese', font_path))
                print(f"Successfully loaded Chinese font: {font_path}")
                return 'Chinese'
        except Exception as e:
            print(f"Failed to load font {font_path}: {e}")
            continue

    print("Warning: No Chinese font loaded. Text may not display correctly.")
    return 'Helvetica'

def create_pdf_styles(font_name):
    """Create and return PDF styles."""
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

    return title_style, normal_style, summary_style

def format_episode_content(text, title_style, normal_style, summary_style):
    """Format a single episode's content into PDF elements."""
    story = []
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

    # Add space between episodes
    story.append(Spacer(1, 30))
    return story

def create_pdf_document(output_file):
    """Create and setup PDF document with styles."""
    # Load font
    font_name = load_chinese_font()

    # Create document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=48
    )

    # Create styles
    styles = create_pdf_styles(font_name)
    
    return doc, styles

def build_episode_story(text, styles):
    """Build story elements for a single episode."""
    story = []
    sections = text.split('\n')
    
    # Group content by sections
    title = None
    intro = []
    summary = []
    events = []
    
    current_section = intro
    for section in sections:
        if not section.strip():
            continue
            
        if title is None:
            # First non-empty section is title
            title = section
        elif section.startswith('摘要'):
            current_section = summary
        elif section.startswith('主要事件'):
            current_section = events
        else:
            current_section.append(section)
    
    # Add title
    if title:
        story.append(Paragraph(title, styles[0]))  # title_style
        story.append(Spacer(1, 12))
    
    # Add introduction
    for line in intro:
        story.append(Paragraph(line, styles[1]))  # normal_style
    story.append(Spacer(1, 12))
    
    # Add summary section
    if summary:
        story.append(Paragraph('摘要', styles[2]))  # summary_style
        story.append(Spacer(1, 6))
        for line in summary:
            story.append(Paragraph(line, styles[1]))
        story.append(Spacer(1, 12))
    
    # Add events section
    if events:
        story.append(Paragraph('主要事件：', styles[2]))
        story.append(Spacer(1, 6))
        for line in events:
            if line.startswith('•'):
                story.append(Paragraph('    ' + line, styles[1]))
            else:
                story.append(Paragraph(line, styles[1]))
    
    # Add space between episodes
    story.append(Spacer(1, 30))
    
    return story

def process_url_batch(urls, start_idx, doc, styles, total_urls):
    """Process a batch of URLs and write to PDF."""
    story = []
    for i, url in enumerate(urls, start_idx):
        print(f"Processing URL {i}/{total_urls}: {url}")
        content = get_episode_content(url)
        story.extend(build_episode_story(content, styles))
    
    print(f"Building PDF for episodes {start_idx}-{start_idx + len(urls) - 1}...")
    doc.build(story)

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Generate PDFs from Pokemon episode summaries.')
    parser.add_argument('season', help='The season folder to process (e.g., "1997" or "advanced_generation")')
    args = parser.parse_args()
    
    # Get the project root directory (where crawler.py is located)
    root_dir = os.path.dirname(os.path.abspath(__file__))
    season_dir = os.path.join(root_dir, args.season)
    
    if not os.path.exists(season_dir):
        print(f"Error: Season directory '{args.season}' not found")
        return
    
    # Read URLs from file
    urls_file = os.path.join(season_dir, 'urls.txt')
    if not os.path.exists(urls_file):
        print(f"Error: URLs file not found in '{args.season}' directory")
        return
    
    pdf_dir = os.path.join(season_dir, 'pdf')
    
    # Ensure pdf directory exists
    os.makedirs(pdf_dir, exist_ok=True)
    
    print(f"Reading URLs from: {urls_file}")
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    total_urls = len(urls)
    print(f"Found {total_urls} URLs to process")
    
    # Process URLs in batches of 20
    BATCH_SIZE = 20
    for batch_start in range(0, total_urls, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_urls)
        batch_urls = urls[batch_start:batch_end]
        
        # Create new PDF document for each batch
        batch_output = os.path.join(pdf_dir, f'{args.season}_episodes_part{batch_start//BATCH_SIZE + 1}.pdf')
        doc, styles = create_pdf_document(batch_output)
        
        # Process batch
        process_url_batch(batch_urls, batch_start + 1, doc, styles, total_urls)
        print(f"Completed batch {batch_start//BATCH_SIZE + 1}")
    
    print("All batches completed!")

if __name__ == '__main__':
    main()
