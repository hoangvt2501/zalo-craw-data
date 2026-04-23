"""Vietnamese location alias mapping for property matching.

Maps abbreviations and sub-regions (e.g., 'tuan chau') to canonical province/city names.
"""

from app.domain.text_utils import normalize_for_matching

_RAW_ALIASES = {
    # MIỀN BẮC 
    "ha noi": ["hn", "hanoi", "hà nội", "thủ đô","hai bà trưng", "long biên", "ba đình", "hoàn kiếm", "tây hồ", "đông anh", "mê linh", "sóc sơn", "thạch thất"],
    "hai phong": ["hp", "hải phòng", "cát bà", "đồ sơn", "thủy nguyên", "kiến thụy", "thành phố hoa phượng đỏ"],
    "quang ninh": ["hl", "hạ long", "halong", "bãi cháy", "vân đồn", "cô tô", "móng cái", "uông bí", "cẩm phả", "đông triều", "tuần châu"],
    "lao cai": ["lc", "lào cai", "sapa", "sa pa", "fansipan", "y tý", "bắc hà", "mường khương"],
    "ha giang": ["hg", "hà giang", "đồng văn", "mèo vạc", "lũng cú", "mã pí lèng", "hoàng su phì", "quản bạ"],
    "ninh binh": ["nb", "ninh bình", "tràng an", "bái đính", "tam cốc", "hang múa", "hoa lư", "phát diệm"],
    "cao bang": ["cb", "cao bằng", "thác bản giốc", "pác bó", "trùng khánh"],
    "yen bai": ["yb", "yên bái", "mù cang chải", "tú lệ", "trạm tấu", "nghĩa lộ"],
    "son la": ["sl", "sơn la", "mộc châu", "tà xùa", "mường la"],
    "bac ninh": ["bn", "bắc ninh", "từ sơn", "quế võ", "tiên du"],
    "hai duong": ["hd", "hải dương", "chí linh", "côn sơn kiếp bạc"],

    # MIỀN TRUNG
    "da nang": ["dn", "đà nẵng", "bà nà", "ba na hills", "bán đảo sơn trà", "ngũ hành sơn", "cầu rồng"],
    "thua thien hue": ["hue", "huế", "tth", "cố đô", "lăng cô", "phá tam giang", "nam đông"],
    "quang nam": ["qn", "quảng nam", "hội an", "hoian", "tam kỳ", "cù lao chàm", "thánh địa mỹ sơn"],
    "khanh hoa": ["nt", "nha trang", "cam ranh", "khánh hòa", "bình ba", "điệp sơn", "ninh hòa"],
    "lam dong": ["dl", "đà lạt", "dalat", "lâm đồng", "bảo lộc", "di linh", "langbiang", "tuyền lâm"],
    "binh thuan": ["pt", "phan thiết", "mũi né", "mui ne", "lagi", "đảo phú quý", "bàu trắng"],
    "binh dinh": ["qn", "quy nhơn", "quy nhon", "eo gió", "kỳ co", "cù lao xanh"],
    "phu yen": ["py", "phú yên", "tuy hòa", "ghềnh đá đĩa", "bãi xép", "vịnh vũng rô"],
    "dak lak": ["dlk", "đắk lắk", "buôn ma thuột", "bmt", "bản đôn", "hồ lắk"],
    "gia lai": ["gl", "gia lai", "pleiku", "biển hồ"],
    "kon tum": ["kt", "kon tum", "măng đen", "mang den", "ngã ba đông dương"],

    # MIỀN NAM
    "ho chi minh": ["hcm", "sg", "sài gòn", "tphcm", "thành phố thủ đức", "thủ đức", "cần giờ", "củ chi", "hóc môn", "nhà bè"],
    "ba ria vung tau": ["vt", "vũng tàu", "brvt", "hồ tràm", "long hải", "côn đảo", "con dao", "phú mỹ"],
    "kien giang": ["pq", "phú quốc", "phu quoc", "kiên giang", "rạch giá", "hà tiên", "nam du", "hòn sơn"],
    "an giang": ["ag", "an giang", "châu đốc", "long xuyên", "rừng tràm trà sư", "miếu bà chúa xứ"],
    "can tho": ["ct", "cần thơ", "ninh kiều", "chợ nổi cái răng", "tây đô"],
    "tay ninh": ["tn", "tây ninh", "núi bà đen", "tòa thánh tây ninh", "dầu tiếng"],
    "dong nai": ["dn", "đồng nai", "biên hòa", "long thành", "trị an", "nam cát tiên"],
    "binh duong": ["bd", "bình dương", "thủ dầu một", "dĩ an", "thuận an", "tân uyên"],
    "ca mau": ["cm", "cà mau", "đất mũi", "u minh hạ", "hòn khoai"],
    "dong thap": ["dt", "đồng tháp", "sa đéc", "cao lãnh", "tràm chim"],
    "long an": ["la", "long an", "tân an", "đức hòa"],
    "ben tre": ["bt", "bến tre", "xứ dừa", "mỏ cày"],
}

# Pre-normalize keys and values
LOCATION_ALIASES = {}
for canonical, aliases in _RAW_ALIASES.items():
    canon_norm = normalize_for_matching(canonical)
    norm_aliases = {normalize_for_matching(alias) for alias in aliases}
    LOCATION_ALIASES[canon_norm] = norm_aliases

def resolve_location(location: str | None) -> set[str]:
    """Returns a set of canonical and normalized variants for a given location string."""
    if not location:
        return set()
    norm = normalize_for_matching(location)
    results = {norm, norm.replace(" ", "")}
    
    for canonical, aliases in LOCATION_ALIASES.items():
        if norm == canonical or norm in aliases or norm.replace(" ", "") in aliases:
            results.add(canonical)
            results.add(canonical.replace(" ", ""))
            results.update(aliases)
    
    return {r for r in results if r}
