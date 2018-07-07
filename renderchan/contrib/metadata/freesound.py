__author__ = 'zelgadis'

import os
from urllib.error import HTTPError
from urllib.request import urlopen, Request
from html.parser import HTMLParser
from renderchan.metadata import RenderChanMetadata

class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.artist = None
        self.title = None
        self.license = None
        self._license_block = False
    def handle_starttag(self, tag, attrs):
        if (tag == 'meta'):
            if attrs[0][0] == 'property' and attrs[0][1] == 'og:audio:artist' and attrs[1][0] == 'content':
                self.artist = attrs[1][1]
            if attrs[0][0] == 'property' and attrs[0][1] == 'og:audio:title' and attrs[1][0] == 'content':
                self.title = attrs[1][1]
        if (self._license_block and tag == 'a'):
            if attrs[0][0] == 'href':
                value = attrs[0][1]
                if value.startswith("http://creativecommons.org/publicdomain/zero/"):
                    self.license = "cc-0"
                elif value.startswith("http://creativecommons.org/licenses/by/"):
                    self.license = "cc-by"
                elif value.startswith("http://creativecommons.org/licenses/by-nc"):
                    self.license = "cc-by-nc"
                elif value.startswith("http://creativecommons.org/licenses/sampling+"):
                    self.license = "cc-sampling+"
                else:
                    print("Error: Unknown license - %s" % value)
            self._license_block = False
        if (tag == 'div'):
            if attrs[0][0] == 'id' and attrs[0][1] == 'sound_license':
                self._license_block = True
    def feed(self, data):
        HTMLParser.feed(self, str(data))
        if self.artist == None or self.title == None or self.license == None:
            raise Exception("Error parsing data from freesound!")

def parse(filename):

    metadata = RenderChanMetadata()

    basename = os.path.basename(filename)
    a=basename.split("__")
    if len(a) < 2:
        return metadata

    sound_id = a[0]
    # This is actually a dirty hack. Need to figure out a way to properly use Freesound's API
    user = a[1].replace("-","_")
    user_alt = a[1].replace("-","%20")
    user_alt2 = a[1].replace("-",".")
    user_alt3 = a[1]
    user_alt4 = a[1].replace("-",".")+"."

    if True:
        url = "http://www.freesound.org/people/%s/sounds/%s/" % (user, sound_id)
        print("Fetching data from %s ..." % url)
        error = None
        req = Request(url)
        try:
            f = urlopen(req)
        except HTTPError as e:
            error = e.code

    if error!=None:
        user = user_alt
        url = "http://www.freesound.org/people/%s/sounds/%s/" % (user, sound_id)
        print("Fetching data from %s ..." % url)
        error = None
        req = Request(url)
        try:
            f = urlopen(req)
        except HTTPError as e:
            error = e.code
    
    if error!=None:
        user = user_alt2
        url = "http://www.freesound.org/people/%s/sounds/%s/" % (user, sound_id)
        print("Fetching data from %s ..." % url)
        error = None
        req = Request(url)
        try:
            f = urlopen(req)
        except HTTPError as e:
            error = e.code
            
            
    if error!=None:
        user = user_alt3
        url = "http://www.freesound.org/people/%s/sounds/%s/" % (user, sound_id)
        print("Fetching data from %s ..." % url)
        error = None
        req = Request(url)
        try:
            f = urlopen(req)
        except HTTPError as e:
            error = e.code
            
    if error!=None:
        user = user_alt4
        url = "http://www.freesound.org/people/%s/sounds/%s/" % (user, sound_id)
        print("Fetching data from %s ..." % url)
        error = None
        req = Request(url)
        try:
            f = urlopen(req)
        except HTTPError as e:
            raise Exception(e.code)

    resp = f.read()
    f.close()


    parser = MyHTMLParser()
    parser.feed(resp)
    artist_url = "http://www.freesound.org/people/%s/" % (user)
    metadata.authors.append("%s ( %s )" % (parser.artist, artist_url))
    metadata.title=parser.title
    metadata.license=parser.license
    metadata.sources=['freesound']

    return metadata
