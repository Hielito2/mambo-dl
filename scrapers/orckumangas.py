import httpx
import time
import re
import pickle

from http.cookiejar import Cookie, CookieJar
from bs4 import BeautifulSoup
from operator import itemgetter
from playwright.sync_api import sync_playwright
from pathlib import Path


SITE = "orckumangas" #same as url_pattern
WAIT = 8
COOKIES = True
GROUP = "orckumangas"
DEBUG = True

agent_file = Path(__file__).parent.parent.resolve() / 'cookies' / f'AGENT.txt'

def clean_filename(name: str, replacement: str = "") -> str:
    illegal_chars = r'[<>:"/\\|?*\x00]'
    cleaned_name = re.sub(illegal_chars, replacement, name)
    cleaned_name = cleaned_name.strip()


    return cleaned_name

class Manga:

    URL_PATTERN = r"^https?://(www\.)?orckumangas\.com/"
    def __init__(self, url) -> None:
        self.url = url 

    
    def save_agent(self, user_agent):
        with open(agent_file, "w") as f:
            f.write(user_agent)

    
    def read_agent(self):
        try:
            with open(agent_file, "r") as f:
                return f.read().strip()
        except:
            return None


    def test_cookies(self, cookies, user_agent):
        if cookies:
            try:
                # Create a CookieJar from your dict
                cookie_jar = CookieJar()
                for domain, paths in cookies.items():
                    for path, cookies in paths.items():
                        for cookie_name, cookie_obj in cookies.items():
                            cookie_jar.set_cookie(cookie_obj)
            except:
                cookie_jar = cookies


        headers={"User-Agent": user_agent, "Referer": "https://orckumangas.com/index.php", "Alt-Used": "mangasnosekai.com"}
        client = httpx.Client(headers=headers, cookies=cookie_jar)

        
        test = client.get(url="https://orckumangas.com/index.php")

        if DEBUG:
            print(test.status_code)

        return test.status_code == 200, client
    

    def set_client(self, cookies, user_agent):
        # Test existing cookies
        agent = self.read_agent()
        if agent:
            valid_cookies, client = self.test_cookies(cookies, agent)
        else:
            print("[Not agent]")
            valid_cookies = False
        try:
            while not valid_cookies:
                cookies, agent = self.get_session_cookies()
                self.save_agent(agent)
                valid_cookies, client = self.test_cookies(cookies, agent)   
        except Exception as e:
            raise ValueError(e)
        
        self.client = client
        self.user_agent = agent
        #print(f"\nCOokies: {cookies2}")
        #print("")
        #print(f"self.user_agent: {self.user_agent}")

        

    def get_session_cookies(self):
        url = "https://orckumangas.com/index.php"
        jar = httpx.Cookies()
        with sync_playwright() as p:
            # Use a Chromium browser instance
            browser = p.chromium.launch(headless=False, channel="chromium",
                                        args=['--disable-blink-features=AutomationControlled'],

            ) 
            
            # Create a new context (like a fresh browser session)
            context = browser.new_context()
            
            # Get the default User-Agent string for the context
            
            
            # 2. Navigate to the URL
            try:
                page = context.new_page()
                # Navigate and wait until the 'load' event (when the page is fully loaded)
                page.goto(url)
                user_agent = page.evaluate("navigator.userAgent")
            except Exception as e:
                print(f"Error navigating to {url}: {e}")
                browser.close()
                return None, None
                
            # 3. Wait for Cookies and Format
            
            # We'll wait a brief moment for the site to set cookies, if they're 
            # set via client-side JavaScript. For most sites, the cookies are
            # set upon initial request and are immediately available.
            # This explicit wait is a safeguard.
            page.wait_for_timeout(3000) # Wait for 3 seconds max

            # Get all cookies for the current context (which includes cookies for the navigated domain)
            playwright_cookies = context.cookies()
            
            # Check if any cookies were found
            while len(playwright_cookies) < 2:
                # 4. Format Cookies for httpx
                # httpx expects cookies as a simple dictionary: {'name': 'value', ...}    
                playwright_cookies = context.cookies()
                time.sleep(3)

            #print("playwright_cookies: \n")
            #print(playwright_cookies)
            jar = CookieJar()

            playwright_cookies = context.cookies()
        
            for pc in playwright_cookies:
                # Construct the Cookie object correctly
                c = Cookie(
                    version=0,
                    name=pc['name'],
                    value=pc['value'],
                    port=None,
                    port_specified=False,
                    domain=pc['domain'],
                    domain_specified=True,
                    domain_initial_dot=pc['domain'].startswith('.'),
                    path=pc['path'],
                    path_specified=True,
                    secure=pc['secure'],
                    expires=int(pc['expires']) if pc.get('expires') and pc['expires'] != -1 else None,
                    discard=False if pc.get('expires') and pc['expires'] != -1 else True,
                    comment=None,
                    comment_url=None,
                    rest={'HttpOnly': str(pc.get('httpOnly', False))},
                    rfc2109=False,
                )
                jar.set_cookie(c)
                # 5. Clean up and Return
            #browser.close()
            
            # 3. Wrap the standard jar into httpx.Cookies
            #print("httpx_cookies: ", jar)
            
            return jar, user_agent


    def get_group_name(self):
        return GROUP
    

    def use_cookies(self):
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
        return headers, True
    

    def get_page_chapters(self, page_url):
        request = self.client.get(url=f"https://orckumangas.com/ficha.php{page_url}")
        request.raise_for_status()

        soup = BeautifulSoup(request.content, "lxml")
        chapters = []
        all_chapters = soup.find('div', class_="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3").find_all('a')
        for chapter in all_chapters:
            data = {}
            data['number'] = chapter.text.split(' ')[1]
            data['link'] = f"https://orckumangas.com/{chapter.get('href')}"
            chapters.append(data)

        return chapters

    def get_chapters(self):
        from rich.progress import Progress
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError("NOT 200 code. cookies probably")
        soup = BeautifulSoup(page.content, "lxml")
        
        #self.debug(page.text)
        
        serie_name = clean_filename(soup.find('div', class_="flex-1").find('h1').text)

        if DEBUG:
            print('Serie Name: ', serie_name)
        
        if not serie_name:
            print(f'[{GROUP}] No serie name ??[!]?')
            return None
        
        # Get many pages the series has
        serie_pages = soup.find('div', class_="flex flex-wrap justify-center gap-2 mt-6").find_all('a')

        
        # Get the links of the pages
        serie_pages_urls = [url.get('href') for url in serie_pages]

        if DEBUG:
            print("Pages: ", len(serie_pages))
            print('Series urls: ', serie_pages_urls)

        

        
        CHAPTERS = []
        with Progress() as progress:
            task = progress.add_task(f"[Get Chapters] Getting the chapters", total=len(serie_pages_urls))
            for page_url in serie_pages_urls:
                data = self.get_page_chapters(page_url)
                for chapter in data:
                    chapter_number = float(chapter['number'])
                    chapter_url = chapter['link']
                    CHAPTERS.append({
                        'volume': 0,
                        'chapter_number': chapter_number,
                        'chapter_url': chapter_url
                    })

                time.sleep(2)
                progress.update(task, advance=1)

        CHAPTERS = sorted(CHAPTERS, key=itemgetter('chapter_number'))

        return serie_name, CHAPTERS
    

    def get_images_url(self, url: str):
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError
        if True:
            self.debug(r.text)

        soup = BeautifulSoup(r.content, "lxml")
        images_block = soup.find("div", class_="chapter-images").find_all("img")
        images = [f"https://orckumangas.com/{image.get("src").strip()}" for image in images_block] 

        return images
        


if __name__ == '__main__':
    pass
