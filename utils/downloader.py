import httpx
import time
import asyncio

from pathlib import Path
from rich.progress import Progress
from utils.create_dirs import create_directory


def chapter_volumen_number(number):
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
    
    return new_number


def download_image(serie_name, volumen, chapter_number, chapter_images, series_path, headers, cookies, group_name):

    extension_mapping = {
                'image/jpeg': 'jpg',
                'image/png': 'png',
                'image/webp': 'webp',
                'image/avif': 'avif',
            }
    """Download a single image with error handling"""
    chapter_number = chapter_volumen_number(chapter_number)
    volumen = chapter_volumen_number(volumen)
    if volumen == "000":
        download_path = create_directory(Path(series_path, f"{serie_name} {chapter_number} ({group_name})"))
    else:
        download_path = create_directory(Path(series_path, f"{serie_name} v{volumen} ({group_name})"))
    
    # Download pretty
   
    with Progress() as progress:
        try:
            task = progress.add_task(f"[cyan]Downloading Chapter {chapter_number} :: {len(chapter_images)} images...", total=len(chapter_images))
            with httpx.Client(headers=headers,timeout=httpx.Timeout(30.0, read=60.0)) as client:
                if cookies != {}:
                    client.cookies.jar._cookies.update(cookies)

                async def download(i, image):
                    async with asyncio.Semaphore(5):
                        for _ in range(5):
                            try:
                                response = client.get(image)
                                response.raise_for_status()
                                content_type = response.headers.get('Content-Type')
                                extension = extension_mapping.get(content_type, 'bin')
                                image_path = Path(download_path, f"{serie_name} - Chapter {chapter_number}[{chapter_volumen_number(i)}].{extension}")
                                
                                if (not image_path.exists() 
                                    or image_path.stat().st_size != int(response.headers.get('content-length', 0))):  
                                    with open(image_path, 'wb') as file:
                                        file.write(response.content)
                                
                                progress.update(task, advance=1)
                                break  
                            except Exception as e:
                                print(f"Failed to download image: {str(e)}")
                                print(image_path.stem)
                                time.sleep(20)
                                continue    

                async def asyy():
                    tasks = [download(i, image) for i, image in enumerate(chapter_images)]
                    await asyncio.gather(*tasks)
                            
                asyncio.run(asyy())                
        except Exception as e:
            print(f"Not sure wat to do when get here {e}")
            return None
        finally:
            progress.update(task, visible=True) # Didn't work as I expected

