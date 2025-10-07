import httpx
from pathlib import Path
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "example" #same as url_pattern
WAIT = 10


class Manga:

    URL_PATTERN = r"^https?://(www\.)?example\.com/"
    def __init__(self, url, user_agent, cookies) -> None:
        headers = headers={"User-Agent": user_agent}
        if cookies == {}:
            self.client = httpx.Client(headers=headers)
        else:
            print(f"{SITE} using existing cookies")
            self.client = httpx.Client(headers=headers, cookies=cookies)
        self.url = url
        
    def debug(self, html):
        htm = (Path(__file__).parent.parent.resolve() / 'debug' / f'{SITE}.html')
        with open(htm, "w") as f:
            f.write(html)

    def get_cookies(self):
        """Returns the cookies and headers from the client."""
        # httpx.Client.cookies is a httpx.Cookies object, convert to dict        
        return self.client.cookies
    

    def wait(self):
        return WAIT
    
    def get_image_headers(self, *args):
        headers = headers={"User-Agent": "", "Referer": args[0]}
        return headers
    

    def get_chapters(self):
        
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError
        soup = BeautifulSoup(page.content, "lxml")
        serie_name = soup.find()
        
        #
        CHAPTERS = []
        content_block = soup.find() #Where chapters are located
        if content_block == None: # In case the previuos can change (could be a dict in case)
            content_block = soup.find()
        try:
            chapters_block = content_block.find_all() # idk, html varies alot
        except Exception as e:
            print("Error in finding the stuff in the HTML")
        
        extra = 900 #Some sites doesn't have chapter number "extra chapter" smth like that)
        try:
            # Get Chapters
            print("Inventario: Getting singles chapters...")
            for chapter in content_block.find_all():
                chapter_url = chapter.get() # Where url is located
                try:
                    chapter_number = float()
                except:
                    chapter_number = extra
                    extra+=1
                CHAPTERS.append({
                    'volume': 0,
                    'chapter_number': chapter_number,
                    'chapter_url': chapter_url
                })
        except Exception as e:
            print(f"Error in getting chapter number and url and saving it\n{e}")
        #print(CHAPTERS)
        CHAPTERS = sorted(CHAPTERS, key=itemgetter('chapter_number'))
        
        return serie_name, CHAPTERS
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError
        if True:
            self.debug(r.text)

        soup = BeautifulSoup(r.content, "lxml")
        images = [image.get().strip() for image in soup.find().find_all()] 

        return images
        


if __name__ == '__main__':
    from fake_useragent import UserAgent
    ua = UserAgent()
    agent = ua.google
    url = ""
    a = Manga(url, agent, {})
    chapters = a.get_chapters(url)
    print(chapters)