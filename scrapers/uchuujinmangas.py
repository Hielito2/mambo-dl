import httpx
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "uchuujinmangas" #same as url_pattern
WAIT = 15


class Manga:

    URL_PATTERN = r"^https?://(www\.)?uchuujinmangas\.com/"
    def __init__(self, url, user_agent, cookies, *_) -> None:
        self.user_agent = user_agent
        if cookies == {}:
            self.client = httpx.Client(headers={"User-Agent": user_agent})
        else:
            print(f"Inventario using existing cookies")
            self.client = httpx.Client(headers={"User-Agent": user_agent}, cookies=cookies)
        self.url = url

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
        return self.client.cookies


    def get_image_headers(self, *args):
        headers = headers={"User-Agent": self.user_agent, "Referer": args[0]}
        return headers

    
    def get_chapters(self):
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError
        soup = BeautifulSoup(page.content, "lxml")
        serie_name = soup.find('title').text.split(" – ")[0].strip()
        
        #
        CHAPTERS = []
        content_block = soup.find('ul', class_="clstyle") #Where chapters are located

        try:
            # Get Chapters
            print("Inventario: Getting singles chapters...")
            for chapter in content_block.find_all('li'):
                chapter_url = chapter.find('a').get('href') # Where url is located
                try:
                    chapter_number = float(chapter.get("data-num"))
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
        print(page.cookies)
        return serie_name, CHAPTERS
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError
        if True:
            self.debug(r.text)

        soup = BeautifulSoup(r.content, "lxml")
        images_block = soup.find('div', id="readerarea")
        images = [image.get('src').strip() for image in images_block.find_all('img')] 

        return images
        


if __name__ == '__main__':
    pass