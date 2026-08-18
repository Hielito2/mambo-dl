import httpx
import time
import asyncio

from pathlib import Path
from rich.progress import Progress
from utils.create_dirs import create_directory, extension_mapping





def chapter_volumen_number(number, vol=False):
    # Split the number into integer and decimal parts
    if isinstance(number, str):
        integer_part, *decimal_part = number.split('.')
    else:
        integer_part, *decimal_part = str(number).split('.')
    
    # Pad the integer part with leading zeros
    if int(integer_part) < 10:
        new_number = '00' + integer_part
    elif int(integer_part) < 100:
        new_number = '0' + integer_part
    else:
        new_number = integer_part
    
    # Add the decimal part back if it exists
    if decimal_part:
        new_number += '.' + decimal_part[0]

    if not vol:
        if "." in new_number:
            dot_split = new_number.split('.')
            if len(dot_split[1]) < 2:
                new_number = new_number + "0"
        else:
            new_number += ".00"
        
    return new_number


def get_image_ext(headears, image):
    content_type = headears.get('Content-Type', 'bin')
    if content_type not in extension_mapping.keys():
        url_extension = str(image).split('.')[-1]
        if url_extension in extension_mapping.values():
            extension = url_extension
        else:
            extension = "bin"
    else:
        extension = extension_mapping[content_type]
    
    return extension
    


def download_image(serie_name, volumen, chapter_number, chapter_images, series_path, headers, cookies, group_name):
    chapter_number = chapter_volumen_number(chapter_number)
    
    volumen = chapter_volumen_number(volumen, vol=True)
    if volumen == "000":
        download_path = create_directory(Path(series_path, f"{serie_name} {chapter_number} ({group_name})"))
    else:
        download_path = create_directory(Path(series_path, f"{serie_name} v{volumen} ({group_name})"))
    
    MISSING = {}
    with Progress() as progress:
        task = progress.add_task(f"[cyan]Downloading Chapter {chapter_number} :: {len(chapter_images)} images...", total=len(chapter_images))

        client = httpx.Client(headers=headers)
        if cookies != {}:
            client.cookies.jar._cookies.update(cookies)

        for i, image in enumerate(chapter_images):
            tries = 0
        
            while tries < 3:
                try:
                    response = client.get(image, follow_redirects=True)
                    if response.status_code == 200:
                        tries = 4
                    elif response.status_code == 404:
                        tries += 1
                        time.sleep(2)
                except:
                    tries += 1
                    time.sleep(2)
            
            
            if response.status_code == 404:
                temp = chapter_number.split('.')[0]
                if not temp in MISSING:
                    MISSING[temp] = [i]
                else:
                    MISSING[temp].append(i)
                continue


            extension = get_image_ext(response.headers, image)
                    
            image_path = Path(download_path, f"{serie_name} - Chapter {chapter_number}[{f"{i:03d}"}].{extension}")
            
            if (not image_path.exists() 
                or image_path.stat().st_size != int(response.headers.get('content-length', 0))):  
                with open(image_path, 'wb') as file:
                    file.write(response.content)
            
            progress.update(task, advance=1)
    
    if len(MISSING) >= 1:
        print(MISSING)


