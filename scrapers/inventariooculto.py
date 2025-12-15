import httpx
import time
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "inventariooculto" #same as url_pattern
WAIT = 5
COOKIES = True
GROUP = "Inventario-Oculto"
DEBUG = True

class Manga:

    URL_PATTERN = r"^https?://(www\.)?inventariooculto\.com/"

    def __init__(self, url) -> None:
        self.url = url
    

    def set_client(self, cookies, user_agent):
        self.user_agent = user_agent.opera
        
        self.client = httpx.Client(headers={"User-Agent": self.user_agent})
        if not cookies == {}:
            print(f"[Inventario] using existing cookies")
            self.client.cookies.jar._cookies.update(cookies)
    
    
    def get_group_name(self):
        return GROUP

    def use_cookies(self):
        return COOKIES
    

    def wait(self):
        return WAIT

        
    def write_html(self, html):
        from pathlib import Path
        htm = (Path(__file__).parent.parent.resolve() / 'debug' / f'{SITE}.html')
        with open(htm, "w") as f:
            f.write(html)
    

    def get_cookies(self):
        """Returns the cookies and headers from the client."""
        # httpx.Client.cookies is a httpx.Cookies object, convert to dict        
        return self.client.cookies.jar._cookies
    

    def get_image_headers(self, **kwargs):
        headers={"User-Agent": self.user_agent, "Referer": kwargs['chapter_url']}
        return headers, False
    

    def chapters_block_request(self):
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError("[inventario-Oculto] Error at making a request")
        soup = BeautifulSoup(page.content, "lxml")
        self.serie_name = str(soup.find("div", class_="post-title").find('h1').text).strip()

        if self.url.endswith('/'):
            new_url = (self.url + "ajax/chapters/")
        else:
            new_url = (self.url + "/ajax/chapters/")
        
        return new_url


    def find_chapters(self, content_block: BeautifulSoup):
        # Get the chapters that have a volume
        chapters = []

        def get_volume_chapters(data, volume_number):
            for chapter in data.find_all('a'):
                if not "https://inventariooculto.com/manga" in chapter.get("href"):
                    continue
                chapter_url = chapter.get("href")
                chapter_number = float(chapter.text.split(" ")[1].strip())
                datax = {
                    'volume': volume_number,
                    'chapter_number': chapter_number,
                    'chapter_url': chapter_url
                }
                chapters.append(datax)
        
        def get_single_chapter(datax, volume_number):
            chapter = datax.find('a')
            if not "https://inventariooculto.com/manga" in chapter.get("href"):
                return
            chapter_url = chapter.get("href")
            chapter_number = float(chapter.text.split(" ")[1].strip())
            data = {
                'volume': volume_number,
                'chapter_number': chapter_number,
                'chapter_url': chapter_url
            }
            chapters.append(data)
    
        for volume in  content_block.find_all("li"):
            if 'class' in volume.attrs and 'has-child' in volume.attrs['class']:
                volume_number = int(volume.find('a').text.split(" ")[1].strip())
                get_volume_chapters(volume, volume_number)
            elif volume.attrs == {}:
                break
            else:
                volume_number = 0
                get_single_chapter(volume, volume_number)          

        return chapters



    def get_chapters(self):
        url = self.chapters_block_request()
        
        request = self.client.post(url=url)
        if DEBUG:
            self.write_html(request.text)
        if request.status_code != 200:
            raise ValueError("[inventario-Oculto] Error at making a request")
        #
        soup = BeautifulSoup(request.content, "lxml")
        content_block = soup.find("div", class_="page-content-listing single-page")
        chapters = self.find_chapters(content_block)
        
        chapters = sorted(chapters, key=itemgetter('chapter_number'))
        if DEBUG:
            for a in chapters:
                print(a)
        return self.serie_name, chapters
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError
        if True:
            self.write_html(r.text)

        soup = BeautifulSoup(r.content, "lxml")
        images = [image.get("src").strip() for image in soup.find("div", class_="reading-content").find_all("img")]

        return images
        


if __name__ == '__main__':
    pass