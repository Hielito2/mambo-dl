# scraper.py
import importlib.util
import re
import sys
import json
import time
from pathlib import Path

from utils.downloader import download_image
from utils.create_dirs import create_directory
from utils.user_agent import agent 
from utils.cookies import save_cookies, load_cookies
from utils.cbz import cbz_wu

# --- Configuration --- should be a .yaml but I'dont wanna do that yet, no yet
SOURCES_DIR = (Path(__file__).parent / "scrapers")

DOWNLOAD = Path('/mnt/ssd/Manga-Scrape/')

class Manga():
    def __init__(self, **kwargs) -> None:
        self.url = kwargs['url']
        self.limit = kwargs['limit']
        self.first_chapter = int(kwargs['first_chapter'])
        self.last_chapter = int(kwargs['last_chapter'])
        self.group_code = kwargs['group_code']
        #
        self.all_source_classes = self._load_source_classes()
        if not self.all_source_classes:
            raise ValueError("Error: No valid source classes were loaded from the Sources directory.")
        self.scraper = self._get_scraper_for_url()
        self.site_name = self.url.split("//")[1].split('.')[0]


    def _load_source_classes(self) -> list: # READY
        source_classes = []
        
        # Temporarily add the Sources directory to the path for correct relative imports
        sys.path.insert(0, str(SOURCES_DIR.parent))
        
        try:
            for source_file in SOURCES_DIR.glob("*.py"):
                if source_file.name == "__init__.py":
                    continue

                module_name = source_file.stem
                class_name =  "Manga"
                
                # --- Dynamic Module Loading ---
                spec = importlib.util.spec_from_file_location(module_name, source_file)
                if spec is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module) # type: ignore

                # --- Class Extraction and Validation ---
                if hasattr(module, class_name):
                    scraper_class = getattr(module, class_name)
                    
                    # Validation: Check if it has the required URL_PATTERN for matching
                    if hasattr(scraper_class, 'URL_PATTERN'):
                        source_classes.append(scraper_class)
                    else:
                        print(f"Warning: Class {class_name} in {module_name}.py is missing 'URL_PATTERN' attribute. Skipping.")
                else:
                    print(f"Warning: Could not find class '{class_name}' in {module_name}.py. Skipping.")

        finally:
            # Clean up the system path
            if sys.path[0] == str(SOURCES_DIR.parent):
                sys.path.pop(0)

        return source_classes


    def _get_scraper_for_url(self): # READY
        """
        Finds and instantiates the correct scraper class for the given URL
        by matching the URL against the class'volumens URL_PATTERN.
        """
        for scraper_class in self.all_source_classes:
            # Use the class's URL_PATTERN (must be a static/class attribute)
            pattern = getattr(scraper_class, 'URL_PATTERN')
            if re.match(pattern, self.url):
                # Instantiate the class with the URL
                return scraper_class(self.url)
                
        raise ValueError(f"Not found scraper for {self.url}")


    def check_float(self, number): # READY
        if "." in str(number) and int(str(number).split('.')[1]) == 0:
            number =  int(number)
        return number
    

    def set_client(self):        
        use_cookies = self.scraper.use_cookies()
        if use_cookies:        
            cookies = load_cookies(self.site_name)
        else:
            cookies = {}
        self.scraper.set_client(cookies=cookies, user_agent=agent())


    def update_cookies(self):
        site_cookies = self.scraper.use_cookies()
        if site_cookies:
            new_cookies = self.scraper.get_cookies()
            if new_cookies != {}:
                save_cookies(new_cookies, self.site_name)


    def get_chapters(self):

        def clean_chapters(chapters):
            chapters_clean = []
            # CLean -  remove chapters not in first and last chapters
            if self.limit:
                for chapter_data in chapters:
                    if int(chapter_data['chapter_number']) < self.first_chapter:
                        continue
                    elif int(chapter_data['chapter_number']) > self.last_chapter:
                        continue
                    else:
                        chapters_clean.append(chapter_data)
            else:
                chapters_clean = chapters
            # 3.5. Clean chapters for mangadex
            try:
                if hasattr(self.scraper, 'clean_chapters'):
                    chapters_clean = self.scraper.clean_chapters(chapters_clean, self.limit, self.first_chapter, self.last_chapter)
                return chapters_clean
            except Exception as e:
                raise ValueError(f"An error occurred during cleaning chapters: {e}")
            
        print("\n--- Getting Chapters ---")
        try:
            self.serie_name, chapters = self.scraper.get_chapters()
            # Should find a better way of doing this 
            print(f"\nSerie: {self.serie_name}\nChapters: {len(chapters)}")
        except Exception as e:
            print(f"An error occurred during getting chapters: {e}")
            return None
        # You can call other common methods as well (EXAMPLE)
        if hasattr(self.scraper, 'get_info'):
            info = self.scraper.get_info()
            print(f"Additional Info: {info}")
        
        chapters = clean_chapters(chapters)
        return chapters
    

    def get_image_urls(self, chapter_data):
        chapter_images = self.scraper.get_images_url(chapter_data['chapter_url']) # THe urls

        if len(chapter_images) == 0:
            raise ValueError("[get_image_urls] 0 Images got")

        return chapter_images
    
    def chapters_iter(self, chapters):
        for chapter_data in chapters:
            yield chapter_data


    def get_download(self, chapter_data, chapter_images):
        headers, use_cookies = self.scraper.get_image_headers(chapter_url=chapter_data['chapter_url'])
        if not use_cookies:
            cookies = {}
        else:
            cookies = self.scraper.get_cookies()
        self.series_paths()
        download_image(serie_name=self.serie_name, volumen=chapter_data['volume'], 
                       chapter_number=self.check_float(chapter_data['chapter_number']), 
                       chapter_images=chapter_images, series_path=self.series_path, 
                       headers=headers, cookies=cookies, 
                       group_name=self.group_name)
        

    def series_paths(self):
        self.group_name = self.scraper.get_group_name()
        self.series_path = Path(DOWNLOAD / self.site_name / f"{self.serie_name} ({self.group_name})")
        create_directory(self.series_path)



def download_manga(**kwargs):
    # class
    serie = Manga(**kwargs)
    serie.set_client()
    #
    chapters = serie.get_chapters()
    all_chapters_data = serie.chapters_iter(chapters)
    for chapter_data in all_chapters_data:
        chapter_images = serie.get_image_urls(chapter_data)
        serie.get_download(chapter_data, chapter_images)



def create_cbz(path: str, language: str, series:str):
    pathe = Path(path)
    # 1. Check path exists
    if not pathe.exists() or not pathe.is_dir():
        print("[create_cbz] Invalid path.")
        return None

    # 2. Get the volumes and chapters of the serie
    # 2.1. Get the chapter info
    CHAPTERS = []
    output_path = create_directory(Path(pathe.parent, f"{pathe.name} (CBZ)"))
    for chapter in sorted(Path(path).iterdir()):
        if not chapter.is_dir():
            continue
        # 2.5 Get volume or chapter
        # 2.6 Chapter
        if not chapter.name.split(' (')[0].split(' ')[-1].startswith("v"):            
            volume = False
            number = float(chapter.name.split(" ")[-2])
            title = f"Chapter {number}"
        else:
            # Assume is volume
            volume = True
            number = int(chapter.name.split(' (')[0].split(' ')[-1][1:])
            title = f"Volume {number}"

        # 3. Create cbz 
        cbz_wu(path=chapter, volume=volume, number=number, title=title, language=language, series=series, output=output_path)





if __name__ == "__main__":
    print('AH')

