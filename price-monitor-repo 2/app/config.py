# 表里的 Product Name -> Mi-Store 页面上的商品型号(精确写法) 和 分类页网址。
# 已用 mistore_catalog.csv 核对过；没写的型号脚本会标"未配置"，绝不模糊猜。
BASE = "https://mi-store.pl/"
S, T = "pol_m_Smartfony_", "pol_m_Tablety_"
MISTORE = {
    "Redmi A7 pro":        {"model": "Xiaomi Redmi A7 Pro",            "page": S + "Redmi-A7-Pro-1016.html"},
    "Redmi 17":            {"model": "Xiaomi Redmi 17",                "page": S + "Redmi-17-1042.html"},
    "Xiaomi 17T 5G":       {"model": "Xiaomi 17T",                     "page": S + "Xiaomi-17T-1035.html"},
    "Xiaomi 17T Pro 5G":   {"model": "Xiaomi 17T Pro",                 "page": S + "Xiaomi-17T-Pro-1036.html"},
    "Xiaomi 17":           {"model": "Xiaomi 17",                      "page": S + "Xiaomi-17-1006.html"},
    "Xiaomi 17 Ultra":     {"model": "Xiaomi 17 Ultra",                "page": S + "Xiaomi-17-Ultra-1007.html"},
    "Redmi Note 17":       {"model": "Xiaomi Redmi Note 17",           "page": S + "Redmi-Note-17-1047.html"},
    "Redmi Note 17 5G":    {"model": "Xiaomi Redmi Note 17 5G",        "page": S + "Redmi-Note-17-1047.html"},
    "Redmi Note 17 Pro 5G":     {"model": "Xiaomi Redmi Note 17 Pro 5G",     "page": S + "Redmi-Note-17-Pro-1048.html"},
    "Redmi Note 17 Pro Max 5G": {"model": "Xiaomi Redmi Note 17 Pro Max 5G", "page": S + "Redmi-Note-17-Pro-Max-1049.html"},
    "POCO M8 5G":          {"model": "Xiaomi POCO M8 5G",              "page": S + "POCO-M8-985.html"},
    "POCO M8 Pro 5G":      {"model": "Xiaomi POCO M8 Pro 5G",          "page": S + "POCO-M8-Pro-986.html"},
    "POCO X8":             {"model": "Xiaomi POCO X8",                 "page": S + "POCO-X8-1069.html"},
    "POCO X8 Pro":         {"model": "Xiaomi POCO X8 Pro 5G",          "page": S + "POCO-X8-Pro-5G-1013.html"},
    "POCO X8 Pro Max":     {"model": "Xiaomi POCO X8 Pro Max 5G",      "page": S + "POCO-X8-Pro-Max-5G-1014.html"},
    "POCO C95 Pro":        {"model": "Xiaomi POCO C95 Pro",            "page": S + "POCO-C95-Pro-1068.html"},
    "Xiaomi Pad 8 Pro":    {"model": "Xiaomi Pad 8 Pro",               "page": T + "Xiaomi-Pad-8-Pro-1010.html"},
    "Xiaomi Pad 8":        {"model": "Xiaomi Pad 8",                   "page": T + "Xiaomi-Pad-8-1009.html"},
    "Redmi Pad 2":         {"model": ("Redmi Pad 2", "Redmi Pad 2 4G"), "page": T + "Redmi-Pad-2-880.html"},   # 已确认: Wi-Fi 版和 4G 版不区分，都参与比价
    "Redmi Pad 2 Pro 5G":  {"model": "Redmi Pad 2 Pro 5G",             "page": T + "Redmi-Pad-2-Pro-917.html"},
    "Redmi Pad 2 Pro":     {"model": "Redmi Pad 2 Pro",                "page": T + "Redmi-Pad-2-Pro-917.html"},
    "Redmi Pad 2 9.7":     {"model": "Redmi Pad 2 9.7",                "page": T + "Redmi-Pad-2-880.html"},
    # 'Redmi Pad 2 9,7" with cover' 未配置: Mi-Store 上没有对应的带保护套单品，需你确认
}


# mi.com/pl 官网: 表里的型号名 -> mi.com 商品标识(链接 /pl/product/<标识>/ 里的那段)。
# 值以 search: 开头 = 给的是搜索页链接，运行时在搜索结果里找到商品标识。已确认的链接: Redmi Pad 2 .../product/redmi-pad-2/buy/ , Redmi Pad 2 Pro .../product/redmi-pad-2-pro/buy/ 。
# 找不到商品 -> "mi.com 未上架"；表里没有的型号 -> "未配置"。
MICOM = {
    "Redmi A7 pro": "search:https://www.mi.com/pl/search/REDMI%20A7%20Pro?tab=product", "Redmi 17": "redmi-17",
    "Xiaomi 17T 5G": "xiaomi-17t", "Xiaomi 17T Pro 5G": "xiaomi-17t-pro",
    "Xiaomi 17": "search:https://www.mi.com/pl/search/Xiaomi%2017?tab=product", "Xiaomi 17 Ultra": "xiaomi-17-ultra",
    "Redmi Note 17": "redmi-note-17", "Redmi Note 17 5G": "redmi-note-17-5g",
    "Redmi Note 17 Pro 5G": "redmi-note-17-pro-5g", "Redmi Note 17 Pro Max 5G": "redmi-note-17-pro-max-5g",
    "POCO M8 5G": "poco-m8-5g", "POCO M8 Pro 5G": "poco-m8-pro-5g", "POCO X8": "poco-x8",
    "POCO X8 Pro": "poco-x8-pro", "POCO X8 Pro Max": "poco-x8-pro-max", "POCO C95 Pro": "poco-c95-pro",
    "Xiaomi Pad 8 Pro": "xiaomi-pad-8-pro", "Xiaomi Pad 8": "xiaomi-pad-8",
    "Redmi Pad 2": "redmi-pad-2", "Redmi Pad 2 Pro 5G": "redmi-pad-2-pro-5g", "Redmi Pad 2 Pro": "redmi-pad-2-pro",
    "Redmi Pad 2 9.7": "redmi-pad-2-9-7-inch",
}
