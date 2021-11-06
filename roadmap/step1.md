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