#!python3
# -*- coding: utf-8 -*-
"""Extract basic fields from wikpedia pages, like `zhwiki-20210720-pages-articles-multistream.xml.bz2`
"""
import copy
from collections.abc import Iterable
from typing import Callable, Optional
import xml.etree.ElementTree as ET


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
                elem.clear()
                if d is not None:
                    yield d

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
        tag = elem.tag
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
            self._page.text = tag.text
            return None
        return None