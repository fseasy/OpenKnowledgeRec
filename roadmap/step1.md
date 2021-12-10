# STEP1: 基于维基百科的最小推荐系统

## 1. 获取维基百科数据

从 https://dumps.wikimedia.org/zhwiki/20210720/ 可以找到最近的中文维基百科dump；

里面挺多dump文件的； 大概结合网上的一些分析，`pages-articles-multistream.xml.bz2` 这种大概是全文，先下下来吧（慢，拿banwagon下……）

这个文件显然是一个xml原始文件，网上有一些解析的工具. 

1. gensim.corpora.wikicorpus

    看起来这个主要是提取提取文字的，我们还是要更完整的信息

2. https://github.com/attardi/wikiextractor

    看起来主要也是抽文本。

有一个问题要想清楚，就是我们究竟要做什么？ 是把数据放到我们本地，还是仅基于数据生成链接，用户自己从链接中获取原始数据？

理论上，后者适用更广，能够在未来避免版权问题？ 同时还可以节省空间。不过前者对wikipedia更友好一点（但理论上我们也可以中转来达到友好访问）。

综上，理论上提供服务时，只需要link就好了。

不过，要得到推荐结果，显然要有一些额外的信息。

1. zhwiki-20210720-abstract-zh-tw4.xml

    内容如下：

    ```
    <feed>
    <doc>
    <title>Wikipedia：芝加哥藝術博物館</title>
    <url>https://zh.wikipedia.org/wiki/%E8%8A%9D%E5%8A%A0%E5%93%A5%E8%97%9D%E8%A1%93%E5%8D%9A%E7%89%A9%E9%A4%A8</url>
    <abstract>|location      = 芝加哥</abstract>
    <links>
    <sublink linktype="nav"><anchor>參考資料</anchor><link>https://zh.wikipedia.org/wiki/%E8%8A%9D%E5%8A%A0%E5%93%A5%E8%97%9D%E8%A1%93%E5%8D%9A%E7%89%A9%E9%A4%A8#參考資料</link></sublink>
    </links>
    </doc>
    <doc>...</doc>
    ...
    </feed>
    ```

    结构还是简单，还有url和次级标题+链接；可惜 `abstract` 抽取得不算太好。也没有期望的词条所属 `category` 啊。
    此外可以看到，词条都是繁体的（看到那个 `tw4` 后缀）

2. zhwiki-20210720-category.sql

    是一个 sql dump，内容大概为

    ```
    CREATE TABLE `category` (
    `cat_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
    `cat_title` varbinary(255) NOT NULL DEFAULT '',
    `cat_pages` int(11) NOT NULL DEFAULT 0,
    `cat_subcats` int(11) NOT NULL DEFAULT 0,
    `cat_files` int(11) NOT NULL DEFAULT 0,
    PRIMARY KEY (`cat_id`),
    UNIQUE KEY `cat_title` (`cat_title`),
    KEY `cat_pages` (`cat_pages`)
    ) ENGINE=InnoDB AUTO_INCREMENT=44732069 DEFAULT CHARSET=binary ROW_FORMAT=COMPRESSED;

    INSERT INTO `category` VALUES (1,'達拉斯',24,6,0),(2,'科索沃行政区划',10,0,0), ...
    ```

    `cat_id`, `cat_title` 这个好理解，后面 3 个具体表达什么含义、如何对应就不时特别清楚了。

3. zhwiki-20210720-siteinfo-namespaces.json

    应该是记录页面本地化的名词。没啥用

4. zhwiki-20210720-pages-articles-multistream.xml.bz2

    用 bzcat 看了下，format和上面的abstract有一定类似

    ```
    <mediawiki ... xml:lang="zh">
    <siteinfo>...</siteinfo>
    <page> 
        <title>哲学</title>
        <ns>0</ns> // page的namespace
        <id>18</id> // page的id
        <redirect title="Computer accessibility" /> // 可能有
        <revision>
            <id>66014900</id>
            <parentid>65755763</parentid>
            <timestamp>2021-06-10T05:03:29Z</timestamp>
            <contributor>
                <username>Tx9032f99</username>
                <id>2327111</id>
            </contributor>
            <minor />
            <comment>/* 中世纪哲学（5-16世纪） */</comment>
            <model>wikitext</model>
            <format>text/x-wiki</format>
            <text bytes="96206" xml:space="preserve">
                [[File:Euclid.jpg|right|thumb|200px|[[歐幾里得]]... ]] // 图片+注释
                {{科学}} // 大图标
                '''林纳斯·班奈狄克·托瓦兹'''（{{lang-sv|Linus Benedict Torvalds}} // ''' 似乎是加粗/强调
                ...[[古埃及]]... // [[xxx]]词条链指
                == 詞源 == // 次级标题
                ...
                [[Category:維基百科版權]] // category
                [[Category:維基百科方針]]
                [[Category:数学| ]]
            </text>
            <sha1>7btnkbwkoa63i4pgijye2485rzd5bze</sha1>
        </revision>
    </page>
    <page>...</page>
    </mediawiki>
    ...
    ```
    
    如上，wikipedia的原文还是一种特殊的格式。这个格式的简单猜测如上所示。在 [从 dump 数据构建 Wikipedia 的 Category Hierarchy][1]

    另外发现维基百科原页的拼接规则似乎是 `https://zh.wikipedia.org/wiki/{$title}`，这样有了标题就可以得到链接了（也不用再额外存url字段了）

    根据前面的介绍，看起来对pages做简单处理即可拿到：

    1. title
    2. raw url
    3. categories and title <-> category
    4. summary (取第一句话即可)

    由上数据，基本就可以把维基百科的简单推荐做起来了。


## 2. wikipedia pagess 数据解析

### 2.1 简单调研

如上，我们基于 `pages` 数据可以拿到我们需要的字段。现在面临的问题就是如何解析这个文件了。

对 dump 文件的解析，最著名的就是 [wiki-extractor](https://github.com/attardi/wikiextractor)， 看了点代码并跑了下：

1. 可以解析出每篇文档
2. 包含id， url，正文文本；其中正文文本可以用 HTML 格式输出； 但是在解析出的 HTML 中， category 被丢弃了

代码还是比较复杂的，基于此改动成本较高.

再搜索了下， 在 [从 dump 数据构建 Wikipedia 的 Category Hierarchy][1] 中比较详细介绍了如何拿到 Category 及构建层次化的Cateogry，
非常有价值。具体地，

1. 可以从 `pages` 中解析出Category
2. 普通page，存在 `词条 -> Category` 映射 （1对多）； 
3. 存在特殊的 `Category` page (如`Category:数学术语`); 
    
    人工查看了一个category类具体页面。 发现页面的头部有全部的分类链（多条）；此外，在页面的尾部，同样有 `cagetory` 标签。
    这个标签和上面直接显示的分类链不完全相同，但似乎差距不大（上面显示的，应该是从 root -> 当前类别的全部路径，而下面显示的仅是父节点）
    我试着沿着父节点不断往上点，找到了 `Category:总览` 词条，它再没有 `category` 词条。这说明递归是可以构建层次化category的。
    而且这个递归并不需要特别处理 `Category` 类的页面。

4. 构建层次化 cateogry 时， 要考虑 `redirect` 逻辑，一个类别没有父节点，不代表它的redirect类目没有父节点（也就是需要链接到唯一的实体）
5. 层次化 category 不是一个树状结构，而是一个图。

    但根据前面回溯的逻辑，理论上应该是有 root 节点的。


我们初期应该就是基于 Category 做推荐，暂时不需要完整的层次化结构，只需要中间层次的 Category 做兴趣冷启动选择就好 —— 
太泛可能不好选择，太细又容易狭窄。到时基于叶子节点往上回溯找到合适的层次即可，应该还好。

回到正题，关于解析 pages 数据，又找到一篇 [Reading Wikipedia XML Dumps with Python][2], 就是直接拿 `xml.etree` 解析就完事。
想想就这么干吧。

> 从上面了解的信息：`<ns>` 是 namespace, 其中 ns == 10 是模板也，对我们应该是没啥用的。 

有点犹豫要不要手写解析，因为显然自己解析会遇到错漏的情况。但目前开源的工具不满足需求，同时获得一个勉强的结果应该是简单的，那就直接干吧。
有错误没啥问题。

### 2.2 实施

目标解析字段：

```
- page
    - title
    - id
    - catetory
    - redirect (redict title, if has)
    - summary (extract from page text)
```

[1]: https://libzx.so/chn/2017/08/20/wikipedia-category-hierarchy.html "从 dump 数据构建 Wikipedia 的 Category Hierarchy"
[2]: https://www.heatonresearch.com/2017/03/03/python-basic-wikipedia-parsing.html "Reading Wikipedia XML Dumps with Python "