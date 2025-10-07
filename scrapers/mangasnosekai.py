import httpx
import time
import re
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "mangasnosekai" #same as url_pattern
WAIT = 10
COOKIES = True


def clean_filename(name: str, replacement: str = "") -> str:
    illegal_chars = r'[<>:"/\\|?*\x00]'
    cleaned_name = re.sub(illegal_chars, replacement, name)
    cleaned_name = cleaned_name.strip()


    return cleaned_name

class Manga:

    URL_PATTERN = r"^https?://(www\.)?mangasnosekai\.com/"
    def __init__(self, url, **kwargs) -> None:
        self.url = url
    

    def set_client(self, **kwargs):
        self.user_agent = kwargs['user_agent']

        if kwargs['cookies'] == {}:
            self.client = httpx.Client(headers={"User-Agent": kwargs['user_agent']})
        else:
            print(f"[mangasnosekai] using existing cookies")
            self.client = httpx.Client(headers={"User-Agent": kwargs['user_agent']}, cookies=kwargs['cookies'])
        

    def cookies(self):
        return COOKIES
    

    def debug(self, html):
        from pathlib import Path
        htm = (Path(__file__).parent.parent.resolve() / 'debug' / f'{SITE}.html')
        with open(htm, "w") as f:
            f.write(html)


    def get_cookies(self):
        """Returns the cookies and headers from the client."""
        # httpx.Client.cookies is a httpx.Cookies object, convert to dict        
        return self.client.cookies.jar._cookies
    

    def wait(self):
        return WAIT
    

    def get_image_headers(self, **kwargs):
        headers = headers={"User-Agent": self.user_agent, "Referer": kwargs['chapter_url']}
        return headers, False
    

    def get_chapters(self):
        
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError
        soup = BeautifulSoup(page.content, "lxml")
        
        self.debug(page.text)
        
        serie_name = clean_filename(soup.find_all('p', class_="font-light text-white")[2].text.split("~")[0])
        
        if not serie_name:
            print('[mangasnosekai] No serie name ??[!]?')
            return None
        
        # Get the manga ID
        manga_id = soup.find('div', class_="site-content").find_next('div').get('class')[0].split("-")[1]

        # Get last page number 
        pages_block = soup.find('div', class_="row justify-content-center")
        last_page = pages_block.find_all('a', class_="pagination-item")[-1].text
        
        # Get Chapters'
        url_1 = "https://mangasnosekai.com/wp-json/muslitos/v1/getcaps7"
        headers_1 = {"Origin": "https://mangasnosekai.com", "Alt-Used": "mangasnosekai.com",
                    "Connection": "keep-alive", "Referer": "https://mangasnosekai.com/manga/historias/}"}
        
        CHAPTERS = []
        for i in range(int(last_page)):
            data_1 = {"action" : "muslitos_anti_hack", "page": str(i+1), "mangaid": str(manga_id), "secret": "mihonsuckmydick"}
            page_1 = self.client.post(url=url_1, headers=headers_1, data=data_1)
            
            response_1 = page_1.json()
            data = response_1['chapters_to_display']
            for chapter in data:
                chapter_number = float(chapter['number'])
                chapter_url = chapter['link']
                CHAPTERS.append({
                    'volume': 0,
                    'chapter_number': chapter_number,
                    'chapter_url': chapter_url
                })

            time.sleep(2)

        CHAPTERS = sorted(CHAPTERS, key=itemgetter('chapter_number'))
        return serie_name, CHAPTERS
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError
        if True:
            self.debug(r.text)

        soup = BeautifulSoup(r.content, "lxml")
        images_block = soup.find("div", class_="reading-content").find_all("img")
        images = [image.get("data-src").strip() for image in images_block] 

        return images
        


if __name__ == '__main__':
    pass