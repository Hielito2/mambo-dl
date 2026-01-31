import httpx
from operator import itemgetter


SITE = "senshimanga" #same as url_pattern
WAIT = 12
COOKIES = False
GROUP = "WORMS-ORGANIZATION"

class Manga:

    URL_PATTERN = r"^https?://(www\.)?capibaratraductor.com/senshimanga"
    def __init__(self, url) -> None:
        self.url = url.split("/")[-1]
        

    def set_client(self, cookies, user_agent):
        self.user_agent = user_agent.opera
        self.headers={"User-Agent": self.user_agent, 
                "Referer": "https://capibaratraductor.com/senshimanga",
                "x-organization": "senshimanga"}
        self.client = httpx.Client(headers=self.headers)


    def get_group_name(self):
        return GROUP


    def use_cookies(self):
        return COOKIES

    def debug(self, html):
        from pathlib import Path
        htm = (Path(__file__).parent.parent.resolve() / 'debug' / f'{SITE}.html')
        with open(htm, "w") as f:
            f.write(html)


    def wait(self):
        return WAIT
    
    def get_image_headers(self, **kwargs):
        headers={"User-Agent": self.user_agent, 
                 "Referer": "https://capibaratraductor.com/",
                 "Priority": "u=5, i",
                 "Host": "r2.capibaratraductor.com",
                 "Sec-Fetch-Site": "same-site"
                 }
        return headers, False
    

    def get_chapters(self):
        # Get the series page
        url = f"https://capibaratraductor.com/api/manga-custom/{self.url}"
        chapter_headers = self.headers
        chapter_headers['Referer'] = f'https://capibaratraductor.com/senshimanga/manga/{self.url}'
        page = self.client.get(url=url, follow_redirects=True, headers=chapter_headers)
        if page.status_code != 200:
            print(page.status_code)
            return 0
        
        self.debug(page.text)
        #
        CHAPTERS = []

        try:
            # Get Chapters
            data = page.json()['data']
            serie_name = data['title']
            for chapter_data in data['chapters']:
                chapter_number = chapter_data['number']
                chapter_url = f"{url}/chapter/{chapter_number}/pages"
                CHAPTERS.append({
                    'volume': 0,
                    'chapter_number': chapter_number,
                    'chapter_url': chapter_url
                })
        except Exception as e:
            print(f"Error in getting chapter number and url and saving it\n{e}")
        #print(CHAPTERS)
        CHAPTERS = sorted(CHAPTERS, key=itemgetter('chapter_number'))
        #print(serie_name, CHAPTERS)
        return serie_name, CHAPTERS
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError
        if True:
            self.debug(r.text)

        data = r.json()['data']
        images = [image['imageUrl'] for image in data] 

        return images
        


if __name__ == '__main__':
    pass