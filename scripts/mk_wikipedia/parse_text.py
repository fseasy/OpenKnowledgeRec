# -*- coding: utf-8 -*-
"""parse text key fields.
"""
import re
import logging

from typing import List

logger = logging.getLogger("wiki_extract")

def extract_categories(text: str) -> List[str]:
    """from page text => category
    has format: 
        [[Category:戏剧| ]]
        [[Category:表演藝術]]
    """
    raw_cats = re.findall(r"\[\[Category:(.*)?\]\]", text)
    return [c.split("|", 1)[0].strip() for c in raw_cats]

def extract_summary(text: str, title: str) -> List[str]:
    """extract summary
    given title, will try to find the first line which title leading.
    else, just get the first line.
    """
    return _SummaryExtractor()(text, title)


class _SummaryExtractor(object):
    
    END_DELIM_RE = re.compile(r"""(?:\.|。|！|\n)[\n'"”]?""")
    SPECIAL_STARTS_RE = re.compile(r"^" + "|".join(
        re.escape(t) for t in [
            "{{", "[[", "==", "|", "}}", "]]", "{|", "!", "#", "*"
        ])
    )

    def __call__(self, text, title):
        _summary_gen_fns = [
            self._quote_hint,
            self._first_normal_line,
            lambda t, _: t[:20] if isinstance(text, str) else ""
        ]
        
        for fn in _summary_gen_fns:
            summary = fn(text, title)
            if summary is not None:
                break
        summary = self._clean_text(summary)
        return summary

    def _quote_hint(self, text, title):
        """by quote hint, like:
        '''戏剧'''（{{lang-en|drama}}）是[[演員]]將某個[[故事]]或情境        
        """
        hint = f"'''{title}'''"
        if (pos := text.find(hint)) == -1:
            return None
        # now find next end delim.
        text = text[pos:]
        if not (m := self.END_DELIM_RE.search(text)):
            logging.warning("this should impossible")
            return None
        text = text[: m.endpos]
        return text

    def _first_normal_line(self, text, _):
        spos = 0

        def _is_normal_line(s):
            return self.SPECIAL_STARTS_RE.match(s) is None

        for m in self.END_DELIM_RE.finditer(text):
            epos = m.endpos
            line = text[spos: epos]
            if _is_normal_line(line):
                return line
        return None

    def _clean_text(self, text):
        """
        clean like:
            '''xxx''' -> xxx
            [[莱昂内尔·罗宾斯|羅賓斯爵士]] => 莱昂内尔·罗宾斯
        """
        def _remove_quote(m):
            return m.group().strip("'''")

        def _extract_link_text(m):
            t = m.group()
            return t.lstrip("[[").split("|", 1)[0]

        patterns = [
            r"'''[^']+'''",
            r"\[\[.+?\]\]"
        ]
        re_pattern = "|".join(patterns)

        def _mapping(m):
            text = m.group()
            if text.startswith("'''"):
                return _remove_quote(m)
            elif text.startswith("[["):
                return _extract_link_text(m)
            else:
                raise ValueError("unknow pattern")

        return re.sub(re_pattern, _mapping, text)