#!python3
# -*- coding: utf-8 -*-
"""Extract basic fields from wikpedia pages, like `zhwiki-20210720-pages-articles-multistream.xml.bz2`
"""
import argparse
import copy
import logging
from typing import Callable, Optional, Iterable
import xml.etree.ElementTree as ET

import parse_text

import tqdm

logger = logging.getLogger("wiki_extract")

class RawPageData(object):
    """raw page data"""
    def __init__(self):
        """init attr"""
        self.clear()
    
    def clear(self):
        """clear(or re-set) attr"""
        self.title = None
        self.id = None
        self.redirect = None
        self.text = None

    def is_valid(self) -> bool:
        """whether data is valid"""
        return not (self.title is None or self.id is None or self.text is None)

    def __str__(self):
        text_head = self.text[:20].replace("\n", " ") if self.text else None
        return f"T={self.title} | I={self.id} | R={self.redirect} | T={text_head}"


class RawPageDataGen(object):
    """raw page data generator. 
    Read wikipedia page xml data, generating RawPageData
    """
    def __call__(self, fpath: str) -> Iterable[RawPageData]:
        """gen generator
        write like `https://github.com/jeffheaton/article-code/blob/master/python/wikipedia/wiki-basic-stream.py`
        it's not elegant, but straightforward
        """
        parser = PageXmlStreamParser()
        with self._get_open_fn(fpath)() as stream:
            for (event, elem) in ET.iterparse(stream, events=["start", "end"]):
                d = parser.inc_parse(event, elem)
                if d is not None:
                    yield d
                if event == "end":
                    # clear element to avoid memory cost. only when `end`(data has parse and saved.)
                    elem.clear()

    def _get_open_fn(self, fpath: str) -> Callable:
        if fpath.endswith(".bz2"):
            import bz2
            return lambda: bz2.open(fpath)
        elif fpath.endswith(".xml"):
            return lambda: open(fpath)
        else:
            raise NotImplementedError("unknow wikipedia page file format for [{fpath}]. please Impl it.")


class PageXmlStreamParser(object):
    """page xml stream parser"""
    def __init__(self):
        self._start_page_ns = False
        self._start_revision_ns = False
        self._page = RawPageData()

    def inc_parse(self, event, elem) -> Optional[RawPageData]:
        """given etree iterparse result (event, elem), do incremental parse.
        if parse done 1 data, release it. else return None
        
        Returns
        =========
        RasePageData/None
        """
        # `elem.tag` has a namespace! e.g.: {http://www.mediawiki.org/xml/export-0.10/}text
        # we need use "}" to split the str and get the lat term. here use `rpartition` as stackoverflow.
        tag = elem.tag.rpartition("}")[-1]
        if tag == "page":
            if event == "start":
                self._start_page_ns = True
                self._page.clear()
            elif event == "end":
                self._start_page_ns = False
                data = copy.copy(self._page)
                # clear when start/end to avoid ill-formated data.
                self._page.clear()
                # return the filled data!
                return data
        if not self._start_page_ns:
            return None
        # all in `page` ns
        if tag == "title" and event == "end":
            self._page.title = elem.text
            return None
        if tag == "id" and event == "end" and not self._start_revision_ns:
            self._page.id = elem.text
            return None
        if tag == "redirect" and event == "end":
            self._page.redirect = elem.attrib("title")
            return None
        if tag == "revision":
            self._start_revision_ns = True if event == "start" else False
            return None
        if tag == "text" and event == "end":
            self._page.text = elem.text
            return None
        return None


class TargetPageData(object):
    """target page data, used for storing"""
    def __init__(self):
        self.title = None
        self.id = None
        self.categories = None
        self.redirect = None
        self.summary = None

    def __str__(self):
        return "|".join(f"{k}={v}" for k, v in self.__dict__.items())

    @classmethod
    def from_raw_data(cls, raw: RawPageData) -> 'TargetPageData':
        d = cls()
        d.title = raw.title
        d.id = raw.id
        d.categoties = parse_text.extract_categories(raw.text)
        d.redirect = raw.redirect
        d.summary = parse_text.extract_summary(raw.text, raw.title)
        return d



def main():
    """extract key fields from wikipedia pages data.
    """
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Extract fields from wikipedia pages")
    parser.add_argument("--input", "-i", help="path to wikipedia pages xml, support [.bz2, .xml] format", 
        required=True)
    args = parser.parse_args()

    for page in tqdm.tqdm(RawPageDataGen()(args.input)):
        if not page.is_valid():
            logger.warning("got invalid page: %s", page)
            continue
        page = TargetPageData.from_raw_data(page)
        print(page)

if __name__ == "__main__":
    main()