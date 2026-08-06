import httpx
from bs4 import BeautifulSoup
from operator import itemgetter
import base64


SITE = "ragnascan" #same as url_pattern
WAIT = 10
COOKIES = True
DEBUG = True

class Manga:

    URL_PATTERN = r"^https?://(www\.)?ragnascan\.xyz/"
    def __init__(self, url) -> None:
        self.url = url
    
    def set_client(self, cookies, user_agent):
        self.user_agent = user_agent.opera
        self.client = httpx.Client(headers={"User-Agent": self.user_agent})
        if not cookies == {}:
            print(f"[{SITE}] using existing cookies")
            self.client.cookies.jar._cookies.update(cookies)
    

    def get_group_name(self):
        return self.group_name
    

    def use_cookies(self):
        return COOKIES


    def wait(self):
        return WAIT
        

    def debug(self, html):
        from pathlib import Path
        htm = (Path(__file__).parent.parent.resolve() / 'debug' / f'{SITE}.html')
        with open(htm, "w") as f:
            f.write(html)


    def get_cookies(self):
        """Returns the cookies and headers from the client."""
        # httpx.Client.cookies is a httpx.Cookies object, convert to dict        
        return self.client.cookies.jar._cookies


    def get_image_headers(self, **kwargs):
        headers={"User-Agent": self.user_agent, "Referer": kwargs['chapter_url'],
                 "Alt-Used": "lector.ragnascan.xyz"}

        return headers, True

    
    def get_chapters(self):
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError
        soup = BeautifulSoup(page.content, "lxml")
        serie_name = soup.find('title').text.split(" - ")[0].strip()
        self.group_name = "RagnaScans"
        
        chapters_block = soup.find('div', id="chaptersContainer")
        chapters_get = chapters_block.find_all('a')
        
        #
        CHAPTERS = []

        try:
            # Get Chapters
            for chapter in chapters_get:
                chapter_url = "https://lector.ragnascan.xyz" + chapter.get('href') # Where url is located
                chapter_number = float(chapter.get('data-chapter-number'))
  
                CHAPTERS.append({
                    'volume': 0,
                    'chapter_number': chapter_number,
                    'chapter_url': chapter_url
                })
        except Exception as e:
            print(f"Error in getting chapter number and url and saving it\n{e}")

        CHAPTERS = sorted(CHAPTERS, key=itemgetter('chapter_number'))    

        return serie_name, CHAPTERS
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError
        #if True:
        #    self.debug(r.text)

        try:
            soup = BeautifulSoup(r.content, "lxml")
            images_block = soup.find('div', id="pagesContainer")
            all_images = []

            for image in images_block.find_all('img'):
                image_url = base64.b64decode(image.get('data-verify').strip()).decode("utf-8")
                image_url_reversed = image_url[::-1]
                image_url_final = "https://lector.ragnascan.xyz" + image_url_reversed
                all_images.append(image_url_final)

            # GET THE real URL

        except:
            raise ValueError("ERROR get_images_url IMaGES")

        return all_images
        


if __name__ == '__main__':
    pass