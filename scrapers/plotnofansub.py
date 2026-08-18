import httpx
from bs4 import BeautifulSoup
from operator import itemgetter
import time

SITE = "plotnofansub" #same as url_pattern
WAIT = 4
COOKIES = False
GROUP = "Plot Twist No Fansub"
DEBUG = False

class Manga:

    URL_PATTERN = r"^https?://(www\.)?plotnofansub\.com/"
    def __init__(self, url) -> None:
        self.url = url
    

    def set_client(self, cookies, user_agent):
        self.user_agent = user_agent.opera

        self.client = httpx.Client(headers={"User-Agent": self.user_agent})
        if not cookies == {}:
            print(f"[{SITE}] using existing cookies")
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
        headers={"User-Agent": self.user_agent, "Alt-Used": "imagenes.plotnofansub.com"}
        return headers, True

    
    def get_chapters(self):
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError
        soup = BeautifulSoup(page.content, "lxml")
        serie_name = soup.find('title').text.split("-")[0].strip()

        # 
        serie_id = soup.find('div', class_="site-content").find_next('div').get('class')[0].split('-')[1]
        if DEBUG:
            print(f"serie_name: {serie_name}")
            print(f"serie_id: {serie_id}")

        total_pages = int(soup.find('button', id="mn-detail-load-more").get('data-total'))

        if DEBUG:
            print('total_pages: ',total_pages)

        # Get the other pages
    
        get_page_url = "https://plotnofansub.com/wp-admin/admin-ajax.php"

        CHAPTERS = []
        for page in range(total_pages):
            print(f"Getting page {page} of {total_pages}")
            page_data = {'action': 'plot_load_chapters',
                         'manga_id': serie_id,
                         'page': page}
            
            data_page = self.client.post(get_page_url, data=page_data)

            data_json = data_page.json()
            page_soup = BeautifulSoup(data_json.get('data')['html'], "lxml")

            for chapter in page_soup.find_all('a'):
                chapter_url = chapter.get('href')
                chapter_number = float(chapter.find('div', class_="mn-detail-chapter-name").text)

                CHAPTERS.append({
                    'volume': 0,
                    'chapter_number': chapter_number,
                    'chapter_url': chapter_url
                })
            
            
            time.sleep(1)
        


        CHAPTERS = sorted(CHAPTERS, key=itemgetter('chapter_number'))
        
        return serie_name, CHAPTERS
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError
        if True:
            self.debug(r.text)

        soup = BeautifulSoup(r.content, "lxml")
        images_block = soup.find('div', class_="read-container")
        images = [image.get('data-src').strip() for image in images_block.find_all('img')] 

        return images
        


if __name__ == '__main__':
    pass