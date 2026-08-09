import httpx
import time
import random
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "visorikigai" #same as url_pattern
WAIT = 5
COOKIES = True
GROUP = "visorikigai"
DEBUG = True

class Manga:

    URL_PATTERN = r"^https?://(www\.)?visorikigai\.gettocaboca.com\.com/"

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
    

    def wait(self):
        return WAIT



    def get_cookies(self):
        """Returns the cookies and headers from the client."""
        # httpx.Client.cookies is a httpx.Cookies object, convert to dict        
        return self.client.cookies.jar._cookies
    

    def get_image_headers(self, **kwargs):
        headers={"User-Agent": self.user_agent, "Referer": "https://visualikigai.sakanamenu.online/", "Alt-Used": "image3.ikigaimangas.cloud"}
        return headers, False
    

    def find_chapters(self, content_block: BeautifulSoup):
        # Get the chapters that have a volume
        chapters = []
        urls = []
        for volume_tab in reversed(content_block.find_all('li', class_="w-full")):
            volume = volume_tab.find('a')
            if DEBUG:
                print("volume", volume.get("href"))
            
            if not "/capitulo/" in volume.get("href"):
                continue
            
            chapter_url = "https://visualikigai.sakanamenu.online" + volume.get('href').strip()

            if DEBUG:
                print(chapter_url)
                
            if chapter_url in urls:
                continue
            else:
                urls.append(chapter_url)
                
            
            
            chapter_number = float(volume.find('h3').text.strip().split(" ")[1].split(':')[0])
               
            
            data = {
                'volume': 0,
                'chapter_number': chapter_number,
                'chapter_url': chapter_url
            }
            
            if DEBUG:
                print(data)
                
            chapters.append(data)
        return sorted(chapters, key=itemgetter('chapter_number'))
    
     

    def get_chapters(self):

        request = self.client.get(url=self.url)
        if request.status_code != 200:
            raise ValueError(f"[{SITE}] Error at get_chapters")
        #
        if DEBUG:
            print(request.status_code)
        soup = BeautifulSoup(request.content, "lxml")
        content_block = soup.find("ul", class_="grid lg:grid-cols-2 gap-2")    
        serie_name = soup.find('h1', class_="card-title").text.strip()
        if DEBUG:
            print(serie_name)
        chapters = self.find_chapters(content_block)

        

        return serie_name, chapters
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url, headers={"Alt-Used": "visualikigai.sakanamenu.online", "Referer": "https://visualikigai.sakanamenu.online/series/cuidado-con-la-villana-manhwa/", "User-Agent": self.user_agent, "Upgrade-Insecure-Requests": "1"})

 
        soup = BeautifulSoup(r.content, "lxml")

        images = []
        for image_block in soup.find("div", class_="flex flex-col w-full").find_all("div", class_="w-full"):
            image_pre_url = str(image_block.get('q:key'))
            if not "/series/" in image_pre_url:
                continue
            if '000a.webp' in image_pre_url or '999.webp' in image_pre_url:
                continue

            image = image_pre_url.strip()
            images.append(image)

        return images   
        


if __name__ == '__main__':
    pass