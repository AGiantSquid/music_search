import webbrowser
import urllib.parse

import re
from PyPDF2 import PdfReader


webbrowser.register(
    'chrome',
	None,
	webbrowser.BackgroundBrowser("C:\Program Files\Google\Chrome\Application\chrome.exe")
	# webbrowser.BackgroundBrowser("/usr/bin/google-chrome")
)



def extract_information(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PdfReader(f)
        print(pdf)

        text = ''
        for page in pdf.pages:
            text += page.extract_text() + "\n"

        print(text)

        out = re.findall(r'Day: (.*?)(East Bay.*?\n)(San Francisco.*?)\nSee events', text, flags=re.DOTALL)

        for concerts in out:
            day = concerts[0]
            east_bay = concerts[1]
            sf = concerts[2]

            print('day:', day)
            print('east_bay:', east_bay)
            print('sf:', sf)

            res = re.findall(r'\n([^:\n]+):\s([^:\n]+)\n', sf)

            if 'thur' not in day.lower():
                continue
            for show in res:
                venue = show[0].strip()
                bands = [_.strip() for _ in show[1].split(',')]
                print('venue: ', venue)
                print('bands: ', bands)
                for band in bands:
                    if 'and more' in band.lower():
                        continue
                    print(band)
                    band_query = urllib.parse.quote_plus(band + ' band')
                    you_tube_url = f'https://www.youtube.com/results?search_query={band_query}'
                    webbrowser.get('chrome').open_new(you_tube_url)
        exit()


if __name__ == '__main__':
    path = 'c:\\Users\\AshleyShultz\\Downloads\\6.12.23-6.18.23.pdf'
    extract_information(path)


