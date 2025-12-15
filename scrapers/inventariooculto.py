import httpx
import time
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "inventariooculto" #same as url_pattern
WAIT = 5
COOKIES = True
GROUP = "Inventario-Oculto"


class Manga:

    URL_PATTERN = r"^https?://(www\.)?inventariooculto\.com/"

    def __init__(self, url) -> None:
        self.url = url
    

    def set_client(self, cookies, user_agent):
        self.user_agent = user_agent.safari
        
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
        headers={"User-Agent": self.user_agent, "Referer": kwargs['chapter_url']}
        return headers, False
    

    def get_chapters(self):
        try:
            # Get the series page
            page = self.client.get(url=self.url, follow_redirects=True)
            if page.status_code != 200:
                raise ValueError
            soup = BeautifulSoup(page.content, "lxml")
            serie_name = str(soup.find("div", class_="post-title").find('h1').text).strip()

            if self.url.endswith('/'):
                new_url = (self.url + "ajax/chapters/")
            else:
                new_url = (self.url + "/ajax/chapters/")
            
            time.sleep(2)
            b = self.client.post(url=new_url)
            self.debug(b.text)
            if b.status_code != 200:
                raise ValueError
        except Exception as e:
            print(f"Error in making the requests {e}")
        
        #
        CHAPTERS = []
        # Scrape myDict = { k:v for (k,v) in zip(keys, values)}  
        soup = BeautifulSoup(b.content, "lxml")
        content_block = soup.find("ul", class_="main version-chap volumns")
        if content_block == None:
            content_block = soup.find("ul", class_="main version-chap no-volumn")
        try:
            volumes_blocks = content_block.find_all("a", class_="has-child")
            chapters_block = content_block.find_all("ul", class_="sub-chap-list")
        except Exception as e:
            print("Error in finding the stuff in the HTML")

        try:
            # Get Chapters with volume
            for volume, chapters in zip(reversed(volumes_blocks), reversed(chapters_block)):
                vol_number = int(volume.text.split(' ')[1])
                for i in reversed(chapters.find_all("a")):
                    chapter_url = i.get("href")
                    try:
                        chapter_number = float(i.text.strip().split(" ")[1])
                    except:
                        chapter_number = round(float(previous_chapter+0.22), 2)

                    CHAPTERS.append({
                        'volume': vol_number,
                        'chapter_number': chapter_number,
                        'chapter_url': chapter_url
                    })
                    previous_chapter = chapter_number
            
            #print(CHAPTERS)
            # Get Chapters without volume
            for chapter in content_block.find_all('a'):
                if not self.url in chapter.get("href", "") or "volumen" in chapter.get("href", "") or isinstance(chapter.get("title"), str): 
                    continue
                else:
                    chapter_url = chapter.get("href")
                    try:
                        chapter_number = float(chapter.text.strip().split(" ")[1])
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
        images = [image.get("src").strip() for image in soup.find("div", class_="reading-content").find_all("img")]

        return images
        


if __name__ == '__main__':
    pass