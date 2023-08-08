import webbrowser
import time
import urllib.parse

import re
from PyPDF2 import PdfReader

import click


KALX_FILE = 'c:\\Users\\AshleyShultz\\Downloads\\8.7.23-8.13.23.pdf'


webbrowser.register(
    'chrome',
    None,
    webbrowser.BackgroundBrowser("C:\Program Files\Google\Chrome\Application\chrome.exe")
    # webbrowser.BackgroundBrowser("/usr/bin/google-chrome")
)


def extract_information(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PdfReader(f)
        # print(pdf)

        text = ''
        for page in pdf.pages:
            text += page.extract_text() + "\n"

        print(text)

        out = re.findall(r'Day: (.*?)(East Bay.*?\n)(San Francisco.*?)\nSee events', text, flags=re.DOTALL)

        for concerts in out:
            day = concerts[0]
            east_bay = concerts[1]
            sf = concerts[2]

            open_videos = click.confirm(
                f'Do you want to open music for day {day}?',
                default=True,
            )

            if not open_videos:
                continue

            print('\n###########################################')
            print('day:', day)
            print('east_bay:', east_bay)
            print('sf:', sf)
            print()

            regions = {
                'east bay': east_bay,
                'sf': sf,
            }

            for region_name, region_data in regions.items():
                open_region = click.confirm(
                    f'Do you want to open music for {region_name}?',
                    default=True,
                )

                if not open_region:
                    continue

                res = re.findall(r'\n([^:\n]+):\s([^:\n]+)', region_data )

                for show in res:
                    venue = show[0].strip()
                    bands = [_.strip() for _ in show[1].split(',')]
                    print('venue: ', venue)
                    print('bands: ', bands)
                    for band in bands:
                        if 'and more' in band.lower():
                            continue
                        band_query = urllib.parse.quote_plus(band + ' band')
                        you_tube_url = f'https://www.youtube.com/results?search_query={band_query}'
                        webbrowser.get('chrome').open_new(you_tube_url)
                        time.sleep(.1)
                print()
        exit()


if __name__ == '__main__':
    path = KALX_FILE
    extract_information(path)
