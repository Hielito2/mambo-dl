import httpx
import time
import random
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "manhwascan" #same as url_pattern
WAIT = 5
COOKIES = True
GROUP = "manhwascan"
DEBUG = True

class Manga:

    URL_PATTERN = r"^https?://(www\.)?manhwascan\.com/"

    def __init__(self, url) -> None:
        self.url = url
    

    def set_client(self, cookies, user_agent):
        self.user_agent = user_agent.opera
        self.client = httpx.Client(headers={"User-Agent": self.user_agent})
        if not cookies == {}:
            print(f"[{SITE}] using existing cookies")
            self.client.cookies.jar._cookies.update(cookies)

    
    def get_site(self):
        return SITE

    def get_group_name(self):
        return GROUP

    def use_cookies(self):
        return COOKIES
    
    
    def get_cookies(self):
        """Returns the cookies and headers from the client."""
        # httpx.Client.cookies is a httpx.Cookies object, convert to dict        
        return self.client.cookies.jar._cookies
    

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
        return headers, True


    def find_chapters(self, content_block: BeautifulSoup):
        # Get the chapters that have a volume
        chapters = []

        for volume in content_block.find_all('a'):
            if not "https://manhwascan.cv/manga/" in volume.get("href"):
                continue
            
            chapter_url = volume.get('href').strip()
            
            chapter_number = float(volume.text.strip().split(" ")[1].split(':')[0])

            
            data = {
                'volume': 0,
                'chapter_number': chapter_number,
                'chapter_url': chapter_url
            }
            chapters.append(data)

        return chapters
    

    def get_chapters(self):
        
        # get cookie
        page = self.client.get(url=self.url)

        page.raise_for_status()

        soup1 = BeautifulSoup(page.content, "lxml")

        self.serie_name = str(soup1.find("div", class_="post-title").find('h1').text).strip()

        # Get chapters
        request = self.client.post(f"{self.url}ajax/chapters/")


        if request.status_code != 200:
            raise ValueError(f"[{SITE}] Error at making a request")
        #
        soup = BeautifulSoup(request.content, "lxml")
        
        chapters = self.find_chapters(soup)
        
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