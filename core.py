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

# --- Configuration --- should be a .yaml but I'dont wanna do that yet
SOURCES_DIR = (Path(__file__).parent / "scrapers")

DOWNLOAD = Path('/mnt/ssd/Manga-Scrape/')
# I just learn about **kwargs

def load_source_classes(sources_dir: Path) -> list:
    """
    Dynamically loads all source classes from the given directory.
    It expects each .py file to contain a class that follows the
    naming convention (e.g., SourceA.py -> SourceA_Scraper) and has
    a static 'URL_PATTERN' attribute.
    """
    source_classes = []
    
    # Temporarily add the Sources directory to the path for correct relative imports
    sys.path.insert(0, str(sources_dir.parent))
    
    try:
        for source_file in sources_dir.glob("*.py"):
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
        if sys.path[0] == str(sources_dir.parent):
            sys.path.pop(0)

    return source_classes


def get_scraper_for_url(url: str, available_classes: list, **kwargs):
    """
    Finds and instantiates the correct scraper class for the given URL
    by matching the URL against the class'volumens URL_PATTERN.
    """
    for scraper_class in available_classes:
        # Use the class's URL_PATTERN (must be a static/class attribute)
        pattern = getattr(scraper_class, 'URL_PATTERN')
        if re.match(pattern, url):
            # Instantiate the class with the URL
            return scraper_class(url, **kwargs)
            
    return None


def main(url: str, **kwargs):
    """
    Main function to execute the scraping logic.
    """
    print(f"Attempting to scrape URL: {url}")
    
    # 1. Load all available source classes
    all_source_classes = load_source_classes(SOURCES_DIR)
    
    if not all_source_classes:
        print("Error: No valid source classes were loaded from the Sources directory.")
        return
    
    # 2. Get the correct, instantiated scraper object for the URL
    user_agent = agent() # Should be set by site instead
    scraper = get_scraper_for_url(url, all_source_classes, **kwargs)
    
    if scraper is None:
        print(f"Error: No scraper found that matches the URL: {url}")
        return
    
    site_name = url.split("//")[1].split('.')[0]
    site_cookies = scraper.cookies()
    if site_cookies:        
        cookies = load_cookies(site_name)
        print("[core] Load cookies.")
    else:
        cookies = {}
    scraper.set_client(user_agent=user_agent, cookies=cookies)

    # 3. Execute the common methods (this is the core of your request)
    print("\n--- Getting Chapters ---")
    try:
        serie_name, chapters = scraper.get_chapters()
        # Should find a better way of doing this 
        print(f"\nSerie: {serie_name}\nChapters: {len(chapters)}")
    except Exception as e:
        print(f"An error occurred during getting chapters: {e}")
        return None
    # You can call other common methods as well (EXAMPLE)
    if hasattr(scraper, 'get_info'):
        info = scraper.get_info()
        print(f"Additional Info: {info}")
    # 3.5. Clean chapters for mangadex
    try:
        # Mangadex
        if hasattr(scraper, 'clean_chapters'):
            chapters = scraper.clean_chapters(chapters, kwargs['limit'], kwargs['start_chapter'], kwargs['end_chapter'])
    except Exception as e:
        print(f"An error occurred during cleaning chapters: {e}")
        return None

    # 4. Save new cookies in case they changed
    if site_cookies:
        new_cookies = scraper.get_cookies()
        if new_cookies != {}:
            save_cookies(new_cookies, site_name)
            cookies = load_cookies(site_name)
        else:
            cookies = {}

    # 5. Getting the images of each chapter and download
    print("\n--- Downloading Chapters ---")
    # 5.1 Get group name [Mangadex & zonatmo]
    if hasattr(scraper, 'get_group_name'):
        group_name = scraper.get_group_name()
        series_path = create_directory(Path(DOWNLOAD / site_name / f"{serie_name} [{group_name}]"))
    else:
        series_path = create_directory(Path(DOWNLOAD / site_name / serie_name))
    wait = scraper.wait()
    try:
        for chapter in chapters:
            if kwargs['limit']:
                if int(chapter['chapter_number']) < kwargs['start_chapter']:
                    continue
                if int(chapter['chapter_number']) > kwargs['end_chapter']:
                    continue
            start_time = time.time()
            chapter_images = scraper.get_images_url(chapter['chapter_url']) # THe urls
            headers, use_cookies = scraper.get_image_headers(chapter_url=chapter['chapter_url'])
            if not use_cookies:
                cookies = {}
            download_image(serie_name, chapter['volume'], chapter['chapter_number'], chapter_images, series_path, headers, cookies) # Should use async
            taked_time = (time.time() - start_time)
            if taked_time < wait:
                time.sleep(wait - taked_time + 0.16)
            else:
                time.sleep(0.40)
    except Exception as e:
        print(f"An error occurred during downloading chapters: {e}")

    
    print("--- Execution Complete ---")


def create_cbz(path: str, language: str, series:str):
    pathe = Path(path)
    # 1. Check path exists
    if not pathe.exists() or not pathe.is_dir():
        print("[create_cbz] Invalid path.")
        return None
    
    # 1.5. Make sure is series path and not chapter or vol path
    test = [file for file in pathe.iterdir() if file.is_file()]
    if len(test) > 0:
        print("[create_cbz] Invalid path. (must be serie path)")
        return None
    
    # 2. Get the volumes and chapters of the serie
    # 2.1. Get the chapter info
    CHAPTERS = []
    for chapter in sorted(Path(path).iterdir()):
        # 2.5 Get volume or chapter
        # 2.6 Chapter
        if " Chapter " in chapter.name:
            volume = False
            number = float(chapter.name.split(" ")[-1])
            title = f"Chapter {number}"
        else:
            # Assume is volume
            volume = True
            number = int(chapter.name.split(" ")[-1][1:])
            title = f"Volume {number}"

        # 3. Create cbz 
        cbz_wu(path=chapter, volume=volume, number=number, title=title, language=language, series=series)

    
    print("--- Execution Complete ---")




if __name__ == "__main__":
    print('AH')

