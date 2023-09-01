import webbrowser
import time
import urllib.parse
import re
import sys
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, TypedDict
from itertools import chain

import click
from PyPDF2 import PdfReader

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

logging.getLogger("PyPDF2").setLevel(logging.ERROR)

# this google drive contains the weekly pdfs of bay area shows
KALX_G_DRIVE_URL = 'https://drive.google.com/drive/folders/1UkAPNVPC-dTMboF4b8r42jNhdH3mm5K6'



def open_upcoming_acts():
    """Get the upcoming acts from the KALX sheet, and open them in Chrome."""
    chrome_browser = get_chrome_browser()
    schedule_pdf_file_name = get_schedule_pdf_file_name()
    upcoming_shows_data = get_file_data(chrome_browser, schedule_pdf_file_name)
    parsed_show_data = extract_show_information(upcoming_shows_data)
    display_data_to_user(parsed_show_data)


def get_chrome_browser() -> webbrowser.Chrome:
    """Get instantiated webbrowser.Chrome class for appropriate os."""
    if sys.platform == "win32":
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    elif sys.platform == "linux":
        chrome_path = "/usr/bin/google-chrome"

    webbrowser.register(
        'chrome',
        None,
        webbrowser.BackgroundBrowser(chrome_path)
    )

    return webbrowser.get('chrome')


def get_schedule_pdf_file_name(today: Optional[datetime]=None) -> str:
    """Get the name of the weekly pdf file, based on "today."
    
    >>> today = datetime(2023, 9, 2)
    >>> get_schedule_pdf_file_name(today)
    '8.28.23-9.3.23.pdf'

    This name is generated based on the date, may be brittle if KALX changes
    their formatting for some reason.
    """

    if not today:
        today = datetime.today()
    
    # Calculate the start and end of the week (assuming weeks start on Monday)
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Format the dates ensuring no leading zeros for the month
    def custom_format(date):
        return f"{date.month}.{date.day}.{date.strftime('%y')}"
    
    start_string = custom_format(start_of_week)
    end_string = custom_format(end_of_week)
    
    return f"{start_string}-{end_string}.pdf"


def get_file_data(
        chrome_browser: webbrowser.Chrome, 
        schedule_pdf_file_name: str,
    ) -> str:
    """Get data from pdf file as a line separated string."""
    output_path = Path(__file__).parent / 'schedules' / schedule_pdf_file_name

    download_file_if_necessary(chrome_browser, output_path)

    with open(output_path, 'rb') as f:
        pdf = PdfReader(f)
        
        lines = chain.from_iterable(
            (page.extract_text() or '').split('\n')
            for page in pdf.pages
        )
        
        return '\n'.join(line.strip() for line in lines)


def download_file_if_necessary(
        chrome_browser: webbrowser.Chrome, 
        output_path: Path,
    ):
    """Check if the file is already downloaded. If not, open a browser to download.
    
    Google Drive doesn't let you download programatically with only the filename,
    hence the manual browser workflow.
    """

    if not output_path.exists():
        logger.info(f'Unable to find concerts file {output_path.name}, please download now.')
        
        chrome_browser.open_new(KALX_G_DRIVE_URL)

        click.confirm(f'Hit enter when you have downloaded the file')

        output_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy(get_downloads_folder() / output_path.name, output_path)


def get_downloads_folder() -> Path:
    """Get path to find pdf file downloaded from Chrome."""
    if sys.platform == "win32":
        return Path(os.path.expanduser("~")) / "Downloads"
    elif sys.platform == "linux":
        return Path.home() / "Downloads"


ShowData = TypedDict('ShowData', {
    'day': str,
    'East Bay': list,
    'San Francisco': list,
})



def extract_show_information(upcoming_shows_data: str) -> ShowData:
    """Accept show data as string.
    
    upcoming_shows_data looks like the following:
    KALX Entertainment Calendar
    3:30 pm/6:30 pm
    Day: Monday Date: 28-Aug
    East Bay
    Cornerstone: Batushka, Swallow The Sun, Stormruler, Almost Dead
    San Francisco
    Bottom of the Hill: J.lately, Rocky G, Ill Sugi & Brycon, Oddity

    [
        {
            'day': 'Monday',
            'East Bay': {
                'Cornerstone': ['Batushka', 'Swallow The Sun']
            },
            'San Francisco': {
                'Bottom of the Hill': ['J.lately', 'Rocky G']
            }
        }
    ]
    """

    parsed_week_data = re.findall(
        r'Day: (.*?)(East Bay.*?\n)(San Francisco.*?)\nSee events', 
        upcoming_shows_data, 
        flags=re.DOTALL,
    )

    week_data = []

    for concerts in parsed_week_data:
        day = concerts[0]
        east_bay = concerts[1]
        sf = concerts[2]

        regions = {
            'East Bay': east_bay,
            'San Francisco': sf,
        }

        day_data = {
            'day': day,
            'regions': {r: {} for r in regions.keys()}
        }

        for region_name, region_data in regions.items():
            res = re.findall(r'\n([^:\n]+):\s([^:\n]+)', region_data)

            for show in res:
                venue = show[0].strip()
                bands = [
                    band.strip()
                    for band in show[1].split(',') 
                    if 'and more' not in band.lower()
                ]
                day_data['regions'][region_name][venue] = bands

        week_data.append(day_data)

    return week_data
        

def display_data_to_user(show_data: ShowData):
    """Open YouTube page for each act at each venue if the user wants to see it."""
    for concerts in show_data:
        day = concerts['day']
        regions = concerts['regions']

        open_videos = click.confirm(
            f'Do you want to open music for day {day}?',
            default=True,
        )

        if not open_videos:
            continue

        print('\n###########################################')
        print('day:', day)
        for region_name, region_data in regions.items():
            print(region_name, list(region_data.keys()))

        for region_name, region_data in regions.items():
            open_region = click.confirm(
                f'Do you want to open music for {region_name}?',
                default=True,
            )

            if not open_region:
                continue

            for venue, bands in region_data.items():
                print('venue: ', venue)
                print('bands: ', bands)
                for band in bands:
                    band_query = urllib.parse.quote_plus(band + ' band')
                    you_tube_url = f'https://www.youtube.com/results?search_query={band_query}'
                    webbrowser.get('chrome').open_new(you_tube_url)
                    time.sleep(.1)
            print()
    exit()


if __name__ == '__main__':
    open_upcoming_acts()
