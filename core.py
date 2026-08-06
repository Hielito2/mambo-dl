import time
import random
import importlib.util
import sys

from pathlib import Path

from utils.downloader import download_image
from utils.create_dirs import create_directory, check_valid_output
from utils.user_agent import agent 
from utils.cookies import save_cookies, load_cookies
from utils.cbz import cbz_wu

# --- Configuration --- should be a .yaml but I'dont wanna do that yet, no yet
SOURCES_DIR = (Path(__file__).parent / "scrapers")


DEBUG = False


class Core:
    def __init__(self, **kwargs) -> None:
        self.url = str(kwargs['url'])
        self.limit = kwargs['limit']
        self.first_chapter = int(kwargs['first_chapter'])
        self.last_chapter = int(kwargs['last_chapter'])
        self.group_code = kwargs['group_code']
        #
        self.scraper = self._load_source_classes()

        self.site_name = " ".join(self.url.split("//")[1].split('.')[0:-1])
        self.output = check_valid_output(kwargs['output'])

    def _load_source_classes(self) -> list: 
        # https://pytutorial.com/python-importlibutilspec_from_file_location-guide/
        try:
            for source_file in SOURCES_DIR.glob("*.py"):
                module_name = source_file.stem
                
                if module_name not in self.url:
                    continue
                
                spec = importlib.util.spec_from_file_location(module_name, source_file)

                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                if module.SITE.lower() in ['mangadex','zonatmo']:
                    scraper = module.Manga(self.url, self.group_code)
                else:
                    scraper = module.Manga(self.url)
                if scraper is None:
                    print('None scraper? ')
                    sys.exit()
        finally:
            return scraper



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

    
    def get_wait(self):
        return self.scraper.wait()
        

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
            # 3.5. Clean chapters for mangadex  | NOT NECCESARY ?
            """try:
                if hasattr(self.scraper, 'clean_chapters'):
                    chapters_clean = self.scraper.clean_chapters(chapters_clean)
                return chapters_clean
            except Exception as e:
                raise ValueError(f"An error occurred during cleaning chapters: {e}")"""
            
            return chapters_clean

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

        if DEBUG:
            print(f'[CORE] ', chapters)

        return chapters
    

    def get_image_urls(self, chapter_data):
        chapter_images = self.scraper.get_images_url(chapter_data['chapter_url']) # THe urls
        return chapter_images
    
    def chapters_iter(self, chapters):
        for chapter_data in chapters:
            yield chapter_data


    def get_download(self, chapter_data, chapter_images):
        headers, use_cookies = self.scraper.get_image_headers(chapter_url=chapter_data['chapter_url'])
        cookies = {}
        if use_cookies:
            cookies = self.scraper.get_cookies()
        if DEBUG:
            print(headers, '\n', cookies)
        self.series_paths()
        download_image(serie_name=self.serie_name, volumen=chapter_data['volume'], 
                       chapter_number=self.check_float(chapter_data['chapter_number']), 
                       chapter_images=chapter_images, series_path=self.series_path, 
                       headers=headers, cookies=cookies, 
                       group_name=self.group_name)
        
        

    def series_paths(self):
        self.group_name = self.scraper.get_group_name()
        self.series_path = Path(self.output / self.site_name / f"{self.serie_name} ({self.group_name})")
        create_directory(self.series_path)


def get_take_time(task, start):
    end = time.time()
    print(f"[TASK] {task} took: {end - start}")


def get_chapter_wait(start_time, site_wait):
    end_time = time.time()
    tooked_time = round(float(end_time - start_time), 2)
    if tooked_time < site_wait and tooked_time > 0:
        time_to_wait = round((site_wait - tooked_time), 2)
        return random.uniform(time_to_wait, time_to_wait+1)
    return random.randint(0,1)


def download_manga(**kwargs):
    serie = Core(**kwargs)
    serie.set_client()
    #
    chapters = serie.get_chapters()
    serie.update_cookies()
    site_wait = serie.get_wait()
    for chapter_data in serie.chapters_iter(chapters):
        start_time = time.time()
        chapter_images = serie.get_image_urls(chapter_data)
        if len(chapter_images) < 1:
            print(f"Chapter {chapter_data['chapter_number']} got 0 Images..")
            continue
        serie.get_download(chapter_data, chapter_images)
        serie.update_cookies()
        wait_time = get_chapter_wait(start_time, site_wait)
        time.sleep(wait_time)



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
        blok = []
        for ch in chapter.name:
            if ch.isdigit():
                blok.append(str(ch))
        
        blok = "".join(blok)
        if "v" in blok:
            # Assume is volume
            volume = True
            number = int(blok.replace("v", ""))
            title = f"Volume {number}"
        else:
            volume = False
            number = float(blok)
            title = f"Chapter {number}"
            

        # 3. Create cbz 
        cbz_wu(path=chapter, volume=volume, number=number, title=title, language=language, series=series, output=output_path)





if __name__ == "__main__":
    print('AH')

