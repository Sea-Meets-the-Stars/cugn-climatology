""" Download the 2026 beta CUGN climatology NetCDF files.

Scrapes the Data Access section of the 2026 beta release page and downloads
every live (non-commented) NetCDF link into $OS_SPRAY/CUGN/Climatology/2026 beta.
The page also carries the old 30-file listing inside an HTML comment; comments
are stripped so only the current release (lt_* long-term and st_* short-term
files) is fetched.

Usage:
    python -m cugn_climatology.download_2026beta
"""

import os
import re
import urllib.request

BASE_URL = 'https://spraydata.ucsd.edu'
PAGE_URL = BASE_URL + '/products/cugn-climatology/new.php'


def grab_file_list() -> list:
    """ Return the live .nc URLs from the 2026 beta page, comments stripped. """
    with urllib.request.urlopen(PAGE_URL) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    # The old (pre-beta) file listing is commented out on the page; drop it.
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    paths = sorted(set(re.findall(r'href="([^"]*\.nc)"', html)))
    return [BASE_URL + p for p in paths]


def download_all(outdir: str = None, clobber: bool = False):
    """ Download every file to outdir (default: $OS_SPRAY/CUGN/Climatology/2026 beta). """
    if outdir is None:
        outdir = os.path.join(os.environ['OS_SPRAY'], 'CUGN',
                              'Climatology', '2026 beta')
    os.makedirs(outdir, exist_ok=True)

    urls = grab_file_list()
    print(f'{len(urls)} NetCDF files listed on {PAGE_URL}')

    for ii, url in enumerate(urls):
        outfile = os.path.join(outdir, os.path.basename(url))
        if os.path.exists(outfile) and not clobber:
            print(f'[{ii+1:3d}/{len(urls)}] Skipping (exists): {os.path.basename(outfile)}')
            continue
        print(f'[{ii+1:3d}/{len(urls)}] Downloading {os.path.basename(outfile)}')
        urllib.request.urlretrieve(url, outfile)

    print(f'Done. Files are in: {outdir}')


if __name__ == '__main__':
    download_all()
