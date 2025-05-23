# Pokemon Wiki PDF Generator

A Python tool that generates PDF documents from Pokemon episode summaries on [52poke Wiki](https://wiki.52poke.com/). The tool crawls episode pages, extracts content, and creates well-formatted PDF documents with Traditional Chinese text.

## Features

- Crawls Pokemon episode summaries from 52poke Wiki
- Converts Simplified Chinese to Traditional Chinese
- Generates batch PDFs (20 episodes per file)
- Supports multiple Pokemon seasons
- Well-formatted PDF output with:
  - Episode titles
  - Introduction paragraphs
  - Summary sections
  - Main events with bullet points
  - Proper spacing and page layout
  - Chinese font support

## Project Structure

```
pokemon_wiki/
├── crawler.py              # Main crawler script
├── 1997/                  # Original Pokemon season
│   ├── generate_urls.py   # URL generator for 1997 season
│   ├── urls.txt          # Generated URLs
│   └── pdf/              # Generated PDFs
└── advanced_generation/   # Advanced Generation season
    ├── generate_urls.py   # URL generator for Advanced Gen
    ├── urls.txt          # Generated URLs
    └── pdf/              # Generated PDFs
```

## Requirements

- Python 3.13+
- UV package manager
- Required packages (installed via uv):
  - beautifulsoup4
  - requests
  - reportlab
  - opencc-python-reimplemented

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jkclee123/pokemon_wiki.git
cd pokemon_wiki
```

2. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

## Usage

### 1. Generate URLs for a Season

Each season has its own `generate_urls.py` script. Run it to generate the URLs for that season:

```bash
cd 1997  # or advanced_generation
uv run generate_urls.py
```

This will create a `urls.txt` file in the season directory.

### 2. Generate PDFs

Use the main crawler script to generate PDFs for a specific season:

```bash
uv run crawler.py 1997  # or advanced_generation
```

The script will:
- Create a `pdf` directory in the season folder
- Process episodes in batches of 20
- Generate PDFs named `{season}_episodes_part{N}.pdf`
- Show progress as it processes each episode

## PDF Output Format

Each episode in the PDF includes:
- Episode title (centered)
- Introduction paragraph
- Summary section
- Main events (with bullet points)
- Proper spacing between sections
- Traditional Chinese text with appropriate font

## Notes

- The crawler includes a 1-second delay between requests to be respectful to the wiki server
- PDFs are generated in batches to manage memory usage
- Chinese fonts are automatically detected from system fonts
- All text is converted to Traditional Chinese
