import httpx
import time
import json
from pathlib import Path
from operator import itemgetter


SITE = "mangadex" #same as url_pattern
WAIT = 10
DEBUG = False #later...
COOKIES = False

class Manga:

    URL_PATTERN = r"^https?://(www\.)?mangadex\.org/"
    def __init__(self, url, **kwargs) -> None:
        if "mangadex" in kwargs['group_code']:
            self.group_code = kwargs['group_code'].split("/")[4]
        else:
            self.group_code = kwargs['group_code']  
        self.url = url.split('/')[4]
    

    def set_client(self, **kwargs):
        self.user_agent = kwargs['user_agent']
        self.client = httpx.Client(headers={"User-Agent": kwargs['user_agent'], "Origin": "https://mangadex.org", "Referer": "https://mangadex.org/"})


    def wait(self):
        return WAIT


    def cookies(self):
        return COOKIES
        

    def debug(self, content):#used figure out what is the response.content when needed
        try:
            htm = (Path(__file__).parent.parent.resolve() / 'debug' / f'{SITE}.json')
            with open(htm, "w") as f:
                json.dump(dict(content), f, indent=4)
        except:
            htm = (Path(__file__).parent.parent.resolve() / 'debug' / f'{SITE}.txt')
            with open(htm, "w") as f:
                f.write(str(content))
    

    def get_group_lang(self):
        url = f"https://api.mangadex.org/group/{self.group_code}?includes[]=leader&includes[]=member"
        response = self.client.get(url)
        language = response.json()['data']['attributes']['focusedLanguages'][0]
        return language
    
    
    def get_group_name(self):
        url = f"https://api.mangadex.org/group/{self.group_code}?includes[]=leader&includes[]=member"
        response = self.client.get(url)
        #self.debug(response.text)
        group_name = response.json()['data']['attributes']['name']
        return group_name
    
    
    def is_the_group(self, code, desire_group):
        #print("is the group?")
        url = f"https://api.mangadex.org/chapter/{code}?includes[]=scanlation_group&includes[]=manga&includes[]=user"
        response = self.client.get(url)
        number = len(response.json()['data']['relationships'])
        #print(f"number: {number}")
        for i in range(number):
            group_name = response.json()['data']['relationships'][i]['id']
            if group_name == desire_group:
                return True
        return False

    
    def clean_chapters(self, chapters, limit, start_chapter, end_chapter):
        new_chapters = []
        for chapter in chapters:
            if limit:
                if int(chapter['chapter_number']) < start_chapter:
                    continue
                if int(chapter['chapter_number']) > end_chapter:
                    continue
            #
            try:
                chapter_group = self.is_the_group(chapter['chapter_url'], self.group_code)
                if chapter_group:
                    print(f"Found chapter {chapter['chapter_number']}")
                    new_chapters.append(chapter)
                else:
                    pass
            except:
                pass
                
            time.sleep(0.5)
        return new_chapters
            
    
    def get_chapters(self):
        lang = self.get_group_lang()
        serie_url = f"https://api.mangadex.org/manga/{self.url}/aggregate?translatedLanguage[]={lang}&groups[]={self.group_code}"
        # Get the series page
        page = self.client.get(url=serie_url)
        if page.status_code != 200:
            raise ValueError
        
        #Get the serie name
        a = self.client.get(f"https://api.mangadex.org/manga/{self.url}")
        serie_name = a.json()['data']['attributes']['title']['en']
        
        # Get the chapters id
        response = page.json()
        CHAPTERS = []
        for volume_number, value in response['volumes'].items():
            for chapter_number, chapter_info in value.get("chapters").items():
                chapter_id = chapter_info['id']
                try:
                    volume_number = int(volume_number)
                except:
                    volume_number = 0
                CHAPTERS.append({
                    'volume': volume_number,
                    'chapter_number': float(chapter_number),
                    'chapter_url': chapter_id
                })

        #print(CHAPTERS)
        CHAPTERS = sorted(CHAPTERS, key=itemgetter('chapter_number'))      
        return serie_name, CHAPTERS

    
    def get_image_headers(self, **kwargs):
        headers={"User-Agent": self.user_agent, "Origin": "https://mangadex.org", "Referer": "https://mangadex.org/"}
        return headers
    

    def get_images_url(self, code: str):
        url = f"https://api.mangadex.org/at-home/server/{code}?forcePort443=false"
        r = self.client.get(url=url)
        if r.status_code != 200:
            raise ValueError
        
        response = r.json()

        base_url = response['baseUrl']
        images_l = response['chapter']['data']
        hash =  response['chapter']['hash']
        base = f"{base_url}/data/{hash}/"

        images = [base+image for image in images_l] 

        return images
        


if __name__ == '__main__':
    pass