from pathlib import Path

from cbz.comic import ComicInfo
from cbz.constants import PageType, Manga, Format
from cbz.page import PageInfo


def cbz_wu(**kwargs):
    path = Path(kwargs['path'])
    paths = list(path.iterdir())

    # Load each page from the 'images' folder into a list of PageInfo objects
    pages = [
        PageInfo.load(
            path=path,
            type=PageType.FRONT_COVER if i == 0 else PageType.BACK_COVER if i == len(paths) - 1 else PageType.STORY
        )
        for i, path in enumerate(sorted(paths))
    ]

    # Create a ComicInfo object using ComicInfo.from_pages() method
    #try
    if kwargs['number'] == int(kwargs['number']):
        kwargs['number'] = int(kwargs['number'])
    comic = ComicInfo.from_pages(
        pages=pages,
        title=kwargs['title'],
        series=kwargs['series'],
        number=kwargs['number'],
        language_iso=kwargs['language'],
        format=Format.WEB_COMIC,
        manga=Manga.YES
    )

    # Show the comic using the show()
    #comic.show()

    # Pack the comic book content into a CBZ file format
    cbz_content = comic.pack()

    # Define the path where the CBZ file will be saved
    cbz_path = kwargs['output'] / f'{path.name}.cbz'

    # Write the CBZ content to the specified path
    cbz_path.write_bytes(cbz_content)
    print(f"Created ::  {path.name}.cbz")
    