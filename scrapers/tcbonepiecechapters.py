import httpx
from bs4 import BeautifulSoup
from operator import itemgetter


SITE = "tcbonepiecechapters" #same as url_pattern
WAIT = 10  #BEtween chapters in seconds


class Manga:

    URL_PATTERN = r"^https?://(www\.)?tcbonepiecechapters\.com/"
    def __init__(self, url, user_agent, cookies, _, __) -> None:
        self.user_agent = user_agent
        self.client = httpx.Client(headers={"User-Agent": user_agent})

        self.url = url
        

    def wait(self):
        return WAIT


    def get_cookies(self):
        """Returns the cookies and headers from the client."""
        # httpx.Client.cookies is a httpx.Cookies object, convert to dict        
        return self.client.cookies
    

    def get_chapters(self):
        
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError
        soup = BeautifulSoup(page.content, "lxml")
        serie_name = soup.find('title').text.split('|')[0].strip()
        
        #
        CHAPTERS = []
        content_block = soup.find('div', class_="col-span-2") #Where chapters are located

        try:
            # Get Chapters
            print("TCB: Getting singles chapters...")
            for url_locator, number_locator  in zip(content_block.find_all('a'), content_block.find_all('div', class_="text-lg font-bold")):
                chapter_url = url_locator.get('href', "") # Where url is located
                
                if not "chapters" in chapter_url:
                    continue
                chapter_url = f"https://tcbonepiecechapters.com{chapter_url}"
                chapter_number = float(number_locator.text.strip().split(" ")[-1])
            
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
    

    def get_image_headers(self):
        headers={"User-Agent": self.user_agent, "Referer": "https://tcbonepiecechapters.com/"}
        return headers


    def get_images_url(self, url: str):
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError

        soup = BeautifulSoup(r.content, "lxml")
        images_block = soup.find('div', class_="flex flex-col items-center justify-center")
        images = [image.get('src').strip() for image in images_block.find_all('img')] 

        return images
        


if __name__ == '__main__':
    pass