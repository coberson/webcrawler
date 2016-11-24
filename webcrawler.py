import urllib2
import re
import argparse

http = re.compile('http://')
https = re.compile('https://')
pattern_url = re.compile(r"(?i)(?P<proto>ftp|http|https|ssh)://((?P<user>\w+)(:(?P<password>[^:]+))?@)?(?P<hostname>[\w.-]+)(:(?P<port>[0-9]+))?/(?P<path>.+)?")
b1 = re.compile('/(?P<path>.+)')
b2 = re.compile('\./(?P<path>.+)')
hal_end = re.compile(r'.*hal\-[v0-9]+$')

bad_links_message = """\nPage contenant des liens defecteux : {}
------------------------------------------------------------------------------"""
one_link_message="""CODE HTTP {}\n{}"""
end_message = """=============================================================================="""

class Crawler(object):
    """list of HTML Pages to scan for urls"""
    def __init__(self):
        self.pages = [] #list of pages to crawl
        self.count = 0 #index for the list of pages
        self.checked_links = set() #set of already crawled urls
    def add_page(self,page):
        """add HTMLpage to crawler, to the pages to crawl"""
        self.pages.append(page)
    def __iter__(self):
        """return iterator for the pages to crawl"""
        return self
    def __next__():
        """return next element"""
        if self.count == len(self.pages):
            raise StopIteration
        self.count +=1
        return self.pages[self.count-1]
    def set_of_urls(self):
        """return urls of pages to crawl"""
        return {p.url for p in self.pages}
    def check_links(self):
        """entry point for the crawling action"""
        while self.pages:
            page = self.pages.pop()
            print 'Check', page, self
            page.check()
        print 'All links checked', self.checked_links
    def not_checked_yet(self, url):
        """tell if url checked"""
        mod = slightly_modify(url)
        for mod_url in mod:
            if mod_url in self.checked_links or mod_url in self.set_of_urls():
                return False
        return True
    def set_checked(self, url):
        """add url to checked urls"""
        self.checked_links.add(url)
    def __str__(self):
        """crawler simplified output as nb of links already checked, to check"""
        return "({},{})".format(len(self.checked_links),len(self.pages))
    
def slightly_modify(url):
    mod_urls = [url]
    mod_url = ""
    if 'http:' in url:
        mod_url = re.sub('http:','https:',url)
        mod_urls.append(mod_url)
    elif 'https:' in url:
        mod_url = re.sub('https:','http:',url)
        mod_urls.append(mod_url)
    if re.search(r'/$',url):
        mod_urls.append(url[:-1])
        if mod_url:
            mod_urls.append(mod_url[:-1])
    else:
        mod_urls.append(url+"/")
        if mod_url:
            mod_urls.append(url+"/")
    return mod_urls

class HTMLpage(object): #trop gourmand
    """HTML page"""
    crawler = Crawler() #static attribute, done only once
    def __init__(self,url):
        self.url = url.strip()
        try:
            site = urllib2.urlopen(self.url)
        except urllib2.HTTPError as e:
            self.code = e.code
        except urllib2.URLError:
            self.code = -1
        except Exception:
            self.code = -2
        else:
            self.code = site.getcode()
            self.links = None #list of url present in the html content
            self.bad_links = dict() #dictionnary of bad links urls
        if self.code<300 and self.code>199:
            self.links = self.make_list_of_links(site)
            if self.links:
                HTMLpage.crawler.add_page(self)
                print "\tAdded to crawler", self
                
            
    def check(self):
        """crawl page and print message for bad links"""
        HTMLpage.crawler.set_checked(self.url)
        self.actu_crawler()
        if self.bad_links:
            print bad_links_message.format(self.url)
            for bl in self.bad_links:
                print one_link_message.format(self.bad_links[bl], bl)
            print end_message
        
            
    def make_list_of_links(self,site):
        """make list of links on the page, in form of a generator"""
        html_content = ""
        for line in skip_comments(site):
            html_content += line
        if self.test_filter(self.url) or self.test_filter(html_content):
            print "*************", self.url
            p = re.compile('<a\s+.*?href\s*=\s*"(?P<ad>.*?)"') 
            iter_ref = (complete_url(self.url, ref.group('ad'))\
                    for ref in p.finditer(html_content)\
                    if test_url(ref.group('ad')))
            return [url for url in iter_ref if url and HTMLpage.crawler.not_checked_yet(url) and not hal_intern(url)] 
        else:
            return None
    
    @staticmethod
    def set_filter(filter_set):
        """set the filter to filter_set for the whole session"""
        HTMLpage.filter_set = filter_set
        
    
    def actu_crawler(self):
        """create new HTMLpage for every link in the list, 
        the HTMLpage is added to the crawler list in the call HTMLpage(),
        add dictionary entry if bad link"""
        if self.links:
            for one_url in self.links: 
                if one_url not in HTMLpage.crawler.set_of_urls():
                    #avoid inserting twice the same url
#                    print "*************", one_url
                    new_page = HTMLpage(one_url)
#                    print "*************", new_page
                    if new_page.code > 299 or new_page.code < 200:
                        self.bad_links[one_url] = new_page.code
                
    def test_filter(self, lines):
        for word in HTMLpage.filter_set:
            if word in lines:
                return True
        return False
    
    def __repr__(self):
        return "({},{})".format(self.url, self.code)
    
def complete_url(base, new):
    if b2.match(new): 
        if base[-1]=='/':
            return base + new[2:]
        else:
            return None
    if b1.match(new):
        base_split = base.split('/');
        return ('/').join(base_split[:-1])+new
    return new
                  
def test_url(url):
    m1 = pattern_url.match(url)
    m2 = b1.match(url)
    m3 = b2.match(url)
    path = ""
    if m1:
        path = m1.group('path')
        if not path:
            path = ""
    elif m2:
        path = m2.group('path')
    elif m3:
        path = m3.group('path')
    else:
        return False
    if '.' not in path:
        return True
    elif '.html' in path:
        return True
    return False

def hal_intern(url):
    return '//hal.' in url and not hal_end.match(url)

def skip_comments(file):
    in_body = 0
    for line in file:
        if '<body>' in line:
            in_body = 1
        if '</body>' in line:
            in_body = 0
        if in_body ==1 and not line.strip().startswith('<!--'):
            yield line
                        
    
def main():
    """parse the command line arguments
    using an instance of ArgumentParser;
    set the filter,
    create an instance of HTMLpage for the initial page,
    begin crawling the pages
    """
    parser = argparse.ArgumentParser(description='crawl from url initial_page with filter page_filter')
    parser.add_argument("initial_page")
    parser.add_argument("page_filter", help="filter words to add as a list", nargs="+")
    
    args = parser.parse_args()
    
    HTMLpage.set_filter(args.page_filter)
    HTMLpage(args.initial_page)
    HTMLpage.crawler.check_links()
    
if __name__ == '__main__':
    main()    
    
