# webcrawler
A Python webcrawler script to identify dead links on my internet page
(mini project suggested in the FUN Python MOOC)

usage: webcrawler.py [-h] initial_page page_filter [page_filter ...]

crawl from url initial_page with filter page_filter

positional arguments:
  initial_page
  page_filter   filter words to add as a list

optional arguments:
  -h, --help    show this help message and exit
  
example call: python webcrawler.py "http://coberson.free.fr/" "Oberson" "Chantal"

set the filter,
create an instance of HTMLpage for the initial page,
begin crawling the pages from the initial page, 
list the links in the pages containing one of the words in the filter,
and so on...

This script was written as an exercise and is not efficient! (See "Scrapy" for efficiency)

