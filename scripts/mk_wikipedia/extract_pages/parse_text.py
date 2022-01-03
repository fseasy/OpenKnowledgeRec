# -*- coding: utf-8 -*-
"""parse text key fields.
"""
import re
import html
import logging

from typing import List

logger = logging.getLogger("wiki_extract")

def extract_categories(text: str) -> List[str]:
    """from page text => category
    has format: 
        [[Category:戏剧| ]]
        [[Category:表演藝術]]
        [[分類:天文學|天文學]]
    """
    raw_cats = re.findall(r"\[\[(?:Category|分類|分类):(.*)?\]\]", text)
    return list(set([c.split("|", 1)[0].strip() for c in raw_cats]))


def extract_summary(text: str, title: str) -> List[str]:
    """extract summary
    given title, will try to find the first line which title leading.
    else, just get the first line.
    """
    return _SummaryExtractor()(text, title)


class _SummaryExtractor(object):
    # don't english `.`, `'` because it cause may cases
    END_DELIM_RE = re.compile(r"""(?:。|！|\n)[\n”]?""")
    _SPECIAL_START_PATTERN = "|".join(
        re.escape(t) for t in [
            "{{", "[[", "==", "|", "}}", "]]", "{|", "!", "#", "*", "<"
        ])
    SPECIAL_STARTS_RE = re.compile(fr"^(?:{_SPECIAL_START_PATTERN})")
    MAX_LEN = 275

    def __call__(self, text, title):
        _summary_gen_fns = [
            self._quote_hint,
            self._first_normal_line,
            self._truncate_max_len
        ]
        
        for fn in _summary_gen_fns:
            summary = fn(text, title)
            logger.debug("fn = %s, summary = %s", fn, summary)
            if summary is not None:
                break
        summary = self._clean_text(summary)
        return summary[: self.MAX_LEN]

    def _quote_hint(self, text, title):
        """by quote hint, like:
        '''戏剧'''（{{lang-en|drama}}）是[[演員]]將某個[[故事]]或情境        
        """
        hint_str = f"'''{title}'''"
        # we first try every paragraph's first sentence.
        for para in self._paragraph_gen(text):
            para = para.strip()
            if not para:
                continue
            if self.SPECIAL_STARTS_RE.match(para):
                continue
            if (hit_pos := para.find(hint_str)) == -1:
                continue
            # just start from hit-str
            para = para[hit_pos: ]
            return self._extract_first_sentence(para)
        return None

    def _first_normal_line(self, text, _):
        # we try every paragraph's first sentence.
        for para in self._paragraph_gen(text):
            para = para.strip()
            if not para:
                continue
            if self.SPECIAL_STARTS_RE.match(para):
                continue
            # ok. let's find the end
            return self._extract_first_sentence(para)
        return None


    def _truncate_max_len(self, text, _):
        if not isinstance(text, str):
            return ""
        text = text[: self.MAX_LEN]
        return re.sub(r"\s+", " ", text)

    def _extract_first_sentence(self, text):
        if not (m := self.END_DELIM_RE.search(text)):
            return text
        return text[: m.span()[1]]

    def _paragraph_gen(self, text):
        spos = 0
        while (pos := text.find("\n", spos)) != -1:
            epos = pos + 1
            para = text[spos: epos]
            yield para
            spos = epos
        return None

    def _clean_text(self, text):
        text = html.unescape(text)

        def _remove_quote(m):
            return m.group().strip("'''")

        def _extract_link_text(m):
            t = m.group()
            return t.strip("[]").split("|", 1)[0]

        def _remove_lang_bracket(m):
            lang = m.group(1)
            return f"（{lang}）"

        def _extract_lang(m):
            text = m.group().strip("{}").split("|")[-1]
            return f" {text} "

        def _remove_pattern(_):
            return ""

        patterns = [
            # '''xxx''' -> xxx
            r"'''[^']+'''",
            # [[莱昂内尔·罗宾斯|羅賓斯爵士]] => 莱昂内尔·罗宾斯
            r"\[\[.+?\]\]",
            # （{{lang-en|philosophy}}） => （philosophy）
            # complex example: （{{lang-en|computer science}}，有时[[缩写]]为{{lang|en|CS}}）
            r"（\{\{lang-\w+\|([^}]+)?\}\}.*）",
            # {{lang|en|Philosophy}} => Philosophy
            r"\{\{lang\|.+?\}\}",
            # removes
            ## （.{5,}?） => ""
            r"（.{5,}?）", # ATTENTION. this pattern inlude previous, so it in latter, and RE can keep order!
            ## {{xxxx}} => ""
            r"\{\{.*?\}\}",
            ## <xxx> => ""
            r"<.*?>"
        ]
        re_pattern = "|".join(patterns)

        def _mapping(m):
            text = m.group()
            if text.startswith("'''"):
                return _remove_quote(m)
            elif text.startswith("[["):
                return _extract_link_text(m)
            elif text.startswith("（{{lang-"):
                return _remove_lang_bracket(m)
            elif text.startswith("{{lang|"):
                return _extract_lang(m)
            else:
                return _remove_pattern(m)

        return re.sub(re_pattern, _mapping, text).strip()