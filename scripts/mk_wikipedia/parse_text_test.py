# -*- coding: utf-8 -*-

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