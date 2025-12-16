import httpx
import time
import re
import pickle

from http.cookiejar import Cookie, CookieJar
from bs4 import BeautifulSoup
from operator import itemgetter
from playwright.sync_api import sync_playwright


SITE = "mangasnosekai" #same as url_pattern
WAIT = 8
COOKIES = True
GROUP = "Mangas no Sekai"

def clean_filename(name: str, replacement: str = "") -> str:
    illegal_chars = r'[<>:"/\\|?*\x00]'
    cleaned_name = re.sub(illegal_chars, replacement, name)
    cleaned_name = cleaned_name.strip()


    return cleaned_name

class Manga:

    URL_PATTERN = r"^https?://(www\.)?mangasnosekai\.com/"
    def __init__(self, url) -> None:
        self.url = url 
    

    def test_cookies(self, cookies, user_agent):
        cookies = httpx.Cookies(cookies)
        client = httpx.Client( headers={"User-Agent": user_agent, "Referer": "https://mangasnosekai.com"})
        client.cookies.jar._cookies.update(cookies)
        test = client.get(url="https://mangasnosekai.com")
        print(test.status_code)
        if test.status_code == 200: 
            print("[Valid cookies]")
            return True, client
        return False
    

    def set_client(self, cookies, user_agent):
        # Test existing cookies
        agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        valid_cookies, client = self.test_cookies(cookies, agent)
        if not valid_cookies:
            cookies, agent = self.get_session_cookies()
            self.client = httpx.Client(headers={"User-Agent": agent, "Referer": "https://mangasnosekai.com"}, cookies=cookies)            
        if valid_cookies:
            self.client = client
        self.user_agent = agent
        #print(f"\nCOokies: {cookies2}")
        #print("")
        #print(f"self.user_agent: {self.user_agent}")

        

    def get_session_cookies(self):
        """
        Opens a URL using Playwright, waits for cookies to be set for the domain,
        and returns them in 'httpx' format along with the User-Agent string.

        Args:
            url: The URL to navigate to (e.g., "https://www.example.com").

        Returns:
            A tuple containing:
            1. cookies_for_httpx (dict): A dictionary of cookies formatted for httpx
            (e.g., {'cookie_name': 'cookie_value'}).
            2. user_agent (str): The User-Agent string used by the browser.
            Returns (None, None) if no cookies are found.
        """
        # Thanks Gemini
        # 1. Initialize Playwright and Browser
        url = "https://mangasnosekai.com"
        jar = httpx.Cookies()
        with sync_playwright() as p:
            # Use a Chromium browser instance
            browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'],
                                        executable_path="/usr/bin/google-chrome-stable") 
            
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
        headers = headers={"User-Agent": self.user_agent, "Referer": "https://mangasnosekai.com/"}
        return headers, True
    

    def get_chapters(self):
        
        # Get the series page
        page = self.client.get(url=self.url, follow_redirects=True)
        if page.status_code != 200:
            raise ValueError("NOT 200 code. cookies probably")
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
