import click
import re
from pathlib import Path
from core import main

@click.group()
def cli():
    """Manga Downloader CLI"""
    pass

@cli.command()
@click.argument('url')
@click.option(
    '-w', 
    '--chapters',  # Change the internal name for clarity
    type=str,           # Accept a string input (e.g., "1-10")
    default="0000",       # Set a default value when the option is not provided
    help='Specify a chapter range to download (e.g., 1-10, 5, or 10-)'
)
@click.option(
    '-gc', 
    '--group-code',     # The new, site-specific option Mangadex
    type=str,           
    default=None,       
    help='[Mangadex] The specific group link or code.'
)
@click.option(
    '-l', 
    '--language',     # The new, site-specific option Mangadex
    type=str,           
    default="en",       
    help='[Mangadex] The specific language tag required by this source. [es-la, fr, pt-br, it, es]'
)


def dl(url, chapters, group_code, language):
    """Download manga from URL"""

    print(f"URL: {url}")    

    
    if chapters == '0000':
        limit = False
        start_chapter, end_chapter = None, None
    else:
        limit = True
        # Regex to parse formats like "1-10", "5", "10-"
        match = re.match(r'^(\d+)(?:-(\d+)?)?$', chapters.strip())

        if match:
            start_str, end_str = match.groups()
            start_chapter = int(start_str)
            end_chapter = int(end_str)
            print(f"Downloading range: from {start_chapter} to {end_chapter}")

    main(url, limit=limit, start_chapter=start_chapter, end_chapter=end_chapter, group_code=group_code, language=language)


if __name__ == '__main__':
    cli()