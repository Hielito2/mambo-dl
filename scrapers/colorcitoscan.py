import httpx
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "colorcitoscan" #same as url_pattern
WAIT = 15
COOKIES = True

class Manga:

    URL_PATTERN = r"^https?://(www\.)?colorcitoscan\.com/"
    def __init__(self, url, **kwargs) -> None:
        self.url = url
    

    def set_client(self, **kwargs):
        self.user_agent = kwargs['user_agent']

        if kwargs['cookies'] == {}:
            self.client = httpx.Client(headers={"User-Agent": kwargs['user_agent']})
        else:
            print(f"[{SITE}] using existing cookies")
            self.client = httpx.Client(headers={"User-Agent": kwargs['user_agent']})
            self.client.cookies.jar._cookies.update(kwargs['cookies'])
    

    def get_group_name(self):
        return self.group_name
    

    def cookies(self):
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
        headers={"User-Agent": self.user_agent, "Referer": "https://colorcitoscan.com/"}
        return headers, True

    
    def get_chapters(self):
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError
        soup = BeautifulSoup(page.content, "lxml")
        serie_name = soup.find('title').text.split("|")[0].strip()
        self.group_name = soup.find('a', class_="w-fit flex gap-3 items-center").text
        
        chapters_block = soup.find('div', class_="w-full flex flex-col gap-3")
        chapters_get = chapters_block.find_all('a')
        #
        CHAPTERS = []

        try:
            # Get Chapters
            for chapter in chapters_get:
                chapter_url = chapter.get('href') # Where url is located
                chapter_number = float(chapter.find_next('p').text.split(' ')[1])
  
                CHAPTERS.append({
                    'volume': 0,
                    'chapter_number': chapter_number,
                    'chapter_url': f'https://colorcitoscan.com{chapter_url}'
                })
        except Exception as e:
            print(f"Error in getting chapter number and url and saving it\n{e}")

        CHAPTERS = sorted(CHAPTERS, key=itemgetter('chapter_number'))        

        return serie_name, CHAPTERS
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError
        if True:
            self.debug(r.text)

        soup = BeautifulSoup(r.content, "lxml")
        images_block = soup.find('div', class_="w-full max-w-4xl mx-auto px-2 sm:px-4")

        images = [image.get('src').strip() for image in images_block.find_all('img')] 

        # GET THE real URL
        urls = []
        headers={"User-Agent": self.user_agent, "Referer": "https://colorcitoscan.com/"}

        for image in images:
            response = httpx.get(url=image, headers=headers)
            urls.append(response.headers['location'])

        return urls
        


if __name__ == '__main__':
    pass