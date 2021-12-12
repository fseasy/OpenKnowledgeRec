# -*- coding: utf-8 -*-
import logging

import parse_text

def test_extract_category():
    s = """
{{维基百科:上载纪录/存档}}
[[Category:中文維基百科上載日誌存檔]]
    """
    cats = parse_text.extract_categories(s)
    assert cats == ["中文維基百科上載日誌存檔"]

    s = """
[[Category:戏剧| ]]
[[Category:表演藝術]]
    """
    cats = parse_text.extract_categories(s)
    assert cats == ["戏剧", "表演藝術"]


def test_extract_summary():
    text = """
    {{disputed|time=2015-12-10T10:29:53+00:00}}
{{noteTA
|1=zh-hans:经院哲学;zh-hant:經院哲學;zh-tw:士林哲學;
}}

{{Philosophy-sidebar}}
[[File:David - The Death of Socrates.jpg|thumb|350px|[[蘇格拉底]]之死，由[[雅克·路易·大卫]]所繪（1787年）]]
'''哲學'''（{{lang-en|philosophy}}）是研究普遍的、基本问题的学科，包括[[存在]]、[[知识]]、[[价值]]、[[理智]]、[[心灵]]、[[语言]]等领域&lt;ref name=&quot;philosophy&quot;/&gt;&lt;ref name=&quot;philosophical&quot;/&gt;。哲学与其他学科不同之處在於哲學有獨特之思考方式，例如[[批判性思维|批判]]的方式、通常是系统化的[[方法]]，并以理性[[论证]]為基礎&lt;ref name=&quot;justification&quot;/&gt;。在日常用语中，哲學可被引申为个人或团体的最基本[[信仰]]、[[概念]]或[[態度 (心理學)|态度]]&lt;ref name =Webster/&gt;，不过此处并非此定义。
== 简介 ==
英語詞語{{lang|en|Philosophy}}（{{Lang-la|philosophia}}）源于[[古希臘語]]中的{{lang|grc|φιλοσοφία}}，意思為「愛智慧」，有时也译为「智慧的朋友」&lt;ref name=&quot;Online Etymology Dictionary&quot;/&gt;&lt;ref name=&quot;Webster's New World Dictionary&quot;/&gt;，该词由{{lang|grc|φίλος}}（philos，爱）的派生词{{lang|grc|φιλεῖν}}（Philein，去爱）和{{lang|grc|σοφία}}（Sophia，智慧）组合而成。一般认为，[[古希腊]]思想家[[毕达哥拉斯]]最先在著作中引入“[[哲学家]]”和“哲学”这两个[[术语]]&lt;ref name=&quot;tufts1&quot;/&gt;。
    """
    title = "哲學"
    target_summary = "哲學（philosophy）是研究普遍的、基本问题的学科，包括存在、知识、价值、理智、心灵、语言等领域。"
    actual_summary = parse_text._SummaryExtractor()(text, title)
    assert target_summary == actual_summary

    text = """

    {{disputed|time=2015-12-10T10:29:53+00:00}}
{{noteTA
|1=zh-hans:经院哲学;zh-hant:經院哲學;zh-tw:士林哲學;
}}

{{Philosophy-sidebar}}
[[File:David - The Death of Socrates.jpg|thumb|350px|[[蘇格拉底]]之死，由[[雅克·路易·大卫]]所繪（1787年）]]
== 简介 ==
英語詞語{{lang|en|Philosophy}}（{{Lang-la|philosophia}}）源于[[古希臘語]]中的{{lang|grc|φιλοσοφία}}，意思為「愛智慧」，有时也译为「智慧的朋友」&lt;ref name=&quot;Online Etymology Dictionary&quot;/&gt;&lt;ref name=&quot;Webster's New World Dictionary&quot;/&gt;，该词由{{lang|grc|φίλος}}（philos，爱）的派生词{{lang|grc|φιλεῖν}}（Philein，去爱）和{{lang|grc|σοφία}}（Sophia，智慧）组合而成。一般认为，[[古希腊]]思想家[[毕达哥拉斯]]最先在著作中引入“[[哲学家]]”和“哲学”这两个[[术语]]&lt;ref name=&quot;tufts1&quot;/&gt;。
    """
    target_summary = "英語詞語 Philosophy 源于古希臘語中的 φιλοσοφία ，意思為「愛智慧」，有时也译为「智慧的朋友」，该词由 φίλος 的派生词 φιλεῖν 和 σοφία 组合而成。"
    actual_summary = parse_text._SummaryExtractor()(text, title)
    assert target_summary == actual_summary


def _test_main():
    """test for convenient debug"""
    logging.basicConfig(level=logging.DEBUG)
    test_extract_summary()

if __name__ == "__main__":
    _test_main()