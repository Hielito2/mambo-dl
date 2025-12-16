import httpx
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "uchuujinmangas" #same as url_pattern
WAIT = 10
COOKIES = True
GROUP = "UCHUUJIN"

class Manga:

    URL_PATTERN = r"^https?://(www\.)?uchuujinmangas\.com/"
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
        headers={"User-Agent": self.user_agent, "Referer": kwargs['chapter_url']}
        return headers, True

    
    def get_chapters(self):
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError
        soup = BeautifulSoup(page.content, "lxml")
        serie_name = soup.find('title').text.split(" – ")[0].strip()

        # Get cookies
        serie_id = soup.find('article').get('id').split('-')[1]
        cookies_data = {"action": "get_chapters", "id": serie_id}
        cookies_url = "https://uchuujinmangas.com/wp-admin/admin-ajax.php"
        cookies_headers = {"User-Agent": self.user_agent, "Origin": "https://uchuujinmangas.com/", "Referer": self.url}
        cookies_request = self.client.post(url=cookies_url, headers=cookies_headers, data=cookies_data)
        
        soup = BeautifulSoup(cookies_request.content, "lxml")
        chapters_get = soup.find_all('option')
        #
        CHAPTERS = []

        try:
            # Get Chapters
            for chapter in chapters_get:
                chapter_url = chapter.get('value') # Where url is located
                chapter_number = float(chapter.text.split(' ')[1])
  
                CHAPTERS.append({
                    'volume': 0,
                    'chapter_number': chapter_number,
                    'chapter_url': chapter_url
                })
        except Exception as e:
            print(f"Error in getting chapter number and url and saving it\n{e}")
        #print(CHAPTERS)
        CHAPTERS = sorted(CHAPTERS, key=itemgetter('chapter_number'))
        
        #print(self.client.cookies)
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