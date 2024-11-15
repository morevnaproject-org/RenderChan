__author__ = 'zelgadis'

import os
from urllib.error import HTTPError
from urllib.request import urlopen, Request
from html.parser import HTMLParser
from renderchan.metadata import RenderChanMetadata

class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.license = None
        self._license_block = False
    def handle_starttag(self, tag, attrs):
        if tag == 'a' :
            self._license_block = False
            for item in attrs:
                if item[0] == 'title' and item[1]=='Go to the full license text':
                    self._license_block = True
                elif self._license_block and item[0] == 'href':
                    value = item[1]
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

    def feed(self, data):
        HTMLParser.feed(self, str(data))
        if self.license == None:
            raise Exception("Can't detect license")

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
            error = e.code
            print("ERROR: Cannot fetch information for %s" % filename)


    if error==None:
        resp = f.read()
        f.close()


        parser = MyHTMLParser()
        artist_url = "http://www.freesound.org/people/%s/" % (user)
        try:
            parser.feed(resp)
            metadata.authors.append("%s ( %s )" % (user, artist_url))
            metadata.title=basename
            metadata.license=parser.license
            metadata.sources=['freesound']
        except:
            print("ERROR: Error parsing data from freesound! Looks like this sound was deleted...")
            metadata.authors.append("%s ( %s ) [DELETED!]" % (user, artist_url))
            metadata.title = basename
            metadata.license = "DELETED"
            metadata.sources = ['freesound']

    else:
        metadata.authors.append("UNKNOWN ( UNKNOWN )")
        metadata.title = "UNKNOWN"
        metadata.license = "UNKNOWN"
        metadata.sources = ['UNKNOWN']

    return metadata
