import urllib.parse
import os
import sys

def generate_urls():
    base_url = 'https://wiki.52poke.com/wiki/'
    urls = []
    for i in range(1, 192):  # Advanced Generation has 191 episodes
        title = f'宝可梦_超世代_第{i}集'
        full_url = base_url + urllib.parse.quote(title)
        urls.append(full_url)
    
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(current_dir, 'urls.txt')
    
    print(f"Writing {len(urls)} URLs to {output_file}")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(urls))
        print("Successfully wrote URLs to file")
    except Exception as e:
        print(f"Error writing file: {e}", file=sys.stderr)

if __name__ == '__main__':
    generate_urls() 