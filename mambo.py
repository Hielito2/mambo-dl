import click
import re
from core import download_manga, create_cbz

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

def dl(url, chapters, group_code):
    """Download manga from URL"""

    if chapters == '0000':
        limit = False
        start_chapter, end_chapter = 0, 9999
    else:
        limit = True
        # Regex to parse formats like "1-10", "5", "10-"
        match = re.match(r'^(\d+)(?:-(\d+)?)?$', chapters.strip())

        if match:
            start_str, end_str = match.groups()
            start_chapter = int(start_str)
            end_chapter = int(end_str)
            print(f"Downloading range: from {start_chapter} to {end_chapter}")

    download_manga(url=url, limit=limit, first_chapter=start_chapter, last_chapter=end_chapter, group_code=group_code)

@cli.command()
@click.argument('path')
@click.option(
    '-l', 
    '--language',  
    type=str,          
    default="en",       #
    help='Specify Language iso (en, es, pt)'
)
@click.option(
    '-s', 
    '--serie-name',  
    type=str,          
    prompt="Series name: ",       #
    help='Series name'
)
def cbz(path, language, serie_name):
    """Create cbz file from serie"""
    create_cbz(path, language, serie_name)




if __name__ == '__main__':
    cli()