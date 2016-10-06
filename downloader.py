import urllib
from config import DIARY_PAGE_ENCODING

oldV = 0
step = 256


def reporthook(blocknum, blocksize, totalsize):
    global oldV
    readsofar = blocknum * blocksize / 1024
    if (readsofar >= oldV + step):
        print("Downloaded ", readsofar, "kb")
        oldV = readsofar


class PostDownloader:

    def __init__(self, login, password):
        self.encoding = DIARY_PAGE_ENCODING
        self.payload = {'user_login': login, 'user_pass': password}
        self.openerData = urllib.parse.urlencode(self.payload).encode(self.encoding)

    def SavePost(self, postNum, fname):
        urllib.request.urlretrieve(self.postInfoTable[postNum][2], fname, data=self.openerData, reporthook=reporthook)

    def SaveURL(self, page, fname):
        global oldV
        oldV = 0
        urllib.request.urlretrieve(page, fname, data=self.openerData, reporthook=reporthook)

    def GetPageAsString(self, page):
        global oldV
        oldV = 0
        req = urllib.request.Request(page, self.openerData)
        resp = urllib.request.urlopen(req)
        return resp.read()
