import httpx
from bs4 import BeautifulSoup
from operator import itemgetter
import time

SITE = "zonatmo" #same as url_pattern
WAIT = 22
COOKIES = True


class Manga:

    URL_PATTERN = r"^https?://(www\.)?zonatmo\.com/"

    def __init__(self, url, group_code) -> None:
        self.url = url
        self.group_code = group_code

    def set_client(self, cookies, user_agent):
        self.user_agent = user_agent.opera

        self.client = httpx.Client(headers={"User-Agent": self.user_agent})
        if not cookies == {}:
            print(f"[Zonatmo] using existing cookies")
            self.client.cookies.jar._cookies.update(cookies)
            

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
        headers={"User-Agent": self.user_agent, "Referer": "https://zonatmo.com/"}
        return headers, False
    

    def get_group_name(self):
        return self.group_code

    def get_chapters(self):
     
            # Get the series page
            page = self.client.get(url=self.url, follow_redirects=True)
            print(page.status_code)
            if page.status_code != 200:
                return 0
            
            soup = BeautifulSoup(page.content, "lxml")
            serie_name = soup.find('title').text.strip().split(" - ")[0]
            chapters_block = soup.find("ul",class_="list-group list-group-flush")

            chapters_info = chapters_block.find_all('li', class_="list-group-item p-0 bg-light upload-link")
            CHAPTERS = []            
            for chapter in reversed(chapters_info):
                chapter_name = chapter.find('a', class_="btn-collapse").text.strip()
                chapter_number = float(chapter_name.split(' ')[1])
                # Get available groups
                groups = chapter.find_all("li", class_="list-group-item")    
                for group in groups:
                    #print(" ".join(group.find('span', class_="").text))
                    group_name = " ".join(group.find('span', class_="").text.lower().strip().split()).split(',')
                    group_name = [name.strip() for name in group_name]
                    if self.group_code.lower() not in group_name:
                        continue
                    else:
                        chapter_url = group.find('a', class_="btn btn-default btn-sm").get('href')
                        CHAPTERS.append({
                        'volume': 0,
                        'chapter_number': chapter_number,
                        'chapter_url': chapter_url
                        })
                        break
                        
  
            CHAPTERS = sorted(CHAPTERS, key=itemgetter('chapter_number'))
            return serie_name, CHAPTERS
    

    def get_images_url(self, url: str):
        # FIRST :
        headers = {"User-Agent": self.user_agent, "Referer": self.url, "Alt-Used": "zonatmo.com"}
        r = self.client.get(url=url, headers=headers, follow_redirects=True)
        if r.status_code != 200:
            raise ValueError
        # SECOND - Challenge I think is useless but I will leave in case it breaks and need something
        # Get id
        soup = BeautifulSoup(r.content, "lxml")
        id = soup.select_one('body > script:nth-child(2)').get('src')
        chall_url = f"https://zonatmo.com{id}"
        chall_headers = {"User-Agent": self.user_agent, "Referer": str(r.url), "Accept": "*/*",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br, zstd",
                        "Sec-GPC": "1",
                        "Connection": "keep-alive",
                        "Sec-Fetch-Dest": "script",
                        "Sec-Fetch-Mode": "no-cors",
                        "Sec-Fetch-Site": "same-origin"}
        time.sleep(2)
        chall_r = self.client.get(url=chall_url, headers=chall_headers)
        
        time.sleep(0.20)
        # GET the cascaque
        new_url = str(r.url).replace("paginated", "cascade")
        headers_2 = {"User-Agent": self.user_agent, "Referer": str(r.url)}
        r2 = self.client.get(new_url, headers=headers_2)

        if r2.status_code != 200:
            raise ValueError
        
        soup = BeautifulSoup(r2.content, "lxml")
        images_block = soup.find("div", id="main-container")

        images_place = images_block.find_all('img', class_="viewer-img")

        images = [image.get('data-src') for image in images_place]

        return images
        


if __name__ == '__main__':
    pass