import click
import os
from core import download_manga, create_cbz

@click.group()
def cli():
    """Manga Downloader CLI"""
    pass

@cli.command()
@click.argument('url')
@click.option(
    '-w', 
    '--chapters',
    type=str,
    default=None,
    help='Specify a chapter range to download (e.g., 1-10, 5, or 10-)'
)
@click.option(
    '-gc', 
    '--group-code',
    type=str,
    default=None,
    help='[Mangadex] The specific group link or code.'
)
@click.option(
    '-all',
    is_flag=True,
    help='Download all series from a website, go brrr.' # No implemented yet
)
@click.option(
    '-o',
    '--output',
    default=None,
    help='Download all series from a website, go brrr.'
)
def dl(url, chapters, group_code, all, output):
    if not chapters:
        limit = False
        start_chapter, end_chapter = 0, 9999
    else:
        limit = True
        try:
            start_chapter = int(chapters.split('-')[0])
            end_chapter = int(chapters.split('-')[1])
            print(f"Downloading range: from {start_chapter} to {end_chapter}")
        except:
            raise ValueError(f"Not valid {chapters}")
 
    download_manga(url=url, limit=limit, first_chapter=start_chapter, 
                   last_chapter=end_chapter, group_code=group_code, all=all, output=output)

@cli.command()
@click.argument('path')
@click.option(
    '-l',
    '--language',
    type=str,
    default="en",
    help='Specify Language iso (en, es, pt)'
)
@click.option(
    '-s',
    '--serie-name',
    type=str,
    prompt="Series name: ",
    help='Series name'
)
def cbz(path, language, serie_name):
    """Create cbz file from serie"""
    create_cbz(path, language, serie_name)




if __name__ == '__main__':
    cli()