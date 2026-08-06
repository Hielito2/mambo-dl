import httpx
import time
import random
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "visormanga" #same as url_pattern
WAIT = 5
COOKIES = False
GROUP = "visormanga"
DEBUG = False

class Manga:

    URL_PATTERN = r"^https?://(www\.)?visormanga\.com/"

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
        headers={"User-Agent": self.user_agent, "Referer": "https://www.visormanga.com/",
                 "Sec-Fetch-Dest": "image", "Sec-Fetch-Mode": "no-cors", "Sec-Fetch-Site": "cross-site"}
        return headers, False
    

    def find_chapters(self, content_block: BeautifulSoup):
        # Get the chapters that have a volume
        chapters = []
        urls = []

        previous_chap_num = None
        for volume in reversed(content_block.find_all('a')):
            
            if not "www.visormanga.com" in volume.get("href"):
                continue
            
            chapter_url = volume.get('href').strip()

            if chapter_url in urls:
                continue
            else:
                urls.append(chapter_url)
                
            
            
            chapter_number = float(volume.text.strip().split(" ")[1])
               
            
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
        soup = BeautifulSoup(request.content, "lxml")
        content_block = soup.find("div", class_="chapters-list noselect")
        serie_name = soup.find('title').text.strip().split(" |")[0]
        chapters = self.find_chapters(content_block)

        


        return serie_name, chapters
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url)


        soup = BeautifulSoup(r.content, "lxml")
        images = [image.get("data-src").strip() for image 
                  in soup.find("div", id="image-alls").find_all("img")] 
        
        return images   
        


if __name__ == '__main__':
    pass