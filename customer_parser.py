import re
from datetime import datetime
from zoneinfo import ZoneInfo
from pypinyin import lazy_pinyin


# =========================
# 基础清洗
# =========================

CHINESE_NUM_MAP = {
    "零": "0",
    "〇": "0",
    "一": "1",
    "二": "2",
    "两": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "七": "7",
    "八": "8",
    "九": "9",
}


def clean_text(text):
    """
    只清理空格和换行，不修改中文内容。
    地址提取、姓名提取、邮箱、电话、邮编都用这个。
    """
    if not text:
        return ""

    text = str(text)
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    return text.strip()


def normalize_box_text(text):
    """
    只用于路线和箱型识别。
    会把中文数字转成阿拉伯数字。
    """
    text = clean_text(text)

    for cn, num in CHINESE_NUM_MAP.items():
        text = text.replace(cn, num)

    return text


# =========================
# 通用字段提取
# =========================

def extract_field_after_keywords(text, keywords):
    """
    通用字段提取函数。
    支持：
    邮箱：abc@qq.com
    邮箱 abc@qq.com
    邮箱
    abc@qq.com
    """
    if not text:
        return None

    text = clean_text(text)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        for keyword in keywords:
            if keyword in line:
                value = line.split(keyword, 1)[-1]
                value = re.sub(r"^[：:\s]+", "", value).strip()

                if value:
                    return value

                if i + 1 < len(lines):
                    return lines[i + 1].strip()

    return None


# =========================
# 姓名
# =========================

SURNAME_PINYIN_FIX = {
    "吕": "Lyu",
}


def extract_recipient_name_cn(text):
    """
    提取收件人中文姓名。
    支持：
    1. 同行有冒号
    2. 同行无冒号
    3. 姓名在下一行
    4. 只提供中文姓名
    5. 中文名 + 英文名
    """
    if not text:
        return None

    text = clean_text(text)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    stop_keywords = [
        "中国地址",
        "国内电话",
        "国内邮编",
        "邮箱",
        "得知渠道",
        "到达中国大陆日期",
        "回国日期",
        "箱子数量",
        "标准尺寸",
        "运单打印",
        "中国国籍",
        "注意事项",
    ]

    noise_words = [
        "收件人姓名",
        "收件人",
        "姓名",
        "与回国本人",
        "护照格式",
        "一致",
    ]

    for i, line in enumerate(lines):
        if "收件人姓名" in line or "收件人" in line:

            value = line

            for noise in noise_words:
                value = value.replace(noise, " ")

            value = re.sub(r"[：:/／,，\s]+", " ", value).strip()

            match = re.search(r"[\u4e00-\u9fff]{2,4}", value)
            if match:
                return match.group(0)

            for next_line in lines[i + 1:]:
                if any(stop in next_line for stop in stop_keywords):
                    break

                next_value = next_line

                for noise in noise_words:
                    next_value = next_value.replace(noise, " ")

                next_value = re.sub(r"[：:/／,，\s]+", " ", next_value).strip()

                match = re.search(r"[\u4e00-\u9fff]{2,4}", next_value)
                if match:
                    return match.group(0)

    return None


def convert_cn_name_to_pinyin(name_cn):
    """
    中文姓名转英文拼音。
    格式：Given Name + Family Name
    陈盈 -> Ying Chen
    吕玥潼 -> Yuetong Lyu
    """
    if not name_cn:
        return None

    pinyin_list = lazy_pinyin(name_cn)

    if len(pinyin_list) < 2:
        return " ".join([p.capitalize() for p in pinyin_list])

    family_char = name_cn[0]
    family_name = SURNAME_PINYIN_FIX.get(
        family_char,
        pinyin_list[0].capitalize()
    )

    given_name = "".join(pinyin_list[1:]).capitalize()

    return f"{given_name} {family_name}"


# =========================
# 电话 / 邮箱 / 邮编
# =========================

def extract_cn_phone(text):
    """
    提取中国手机号。
    +86 15868155998 -> 15868155998
    """
    if not text:
        return None

    cleaned = re.sub(r"\s+", "", text)

    match = re.search(
        r"(?:\+?86)?(1\d{10})",
        cleaned
    )

    if match:
        return match.group(1)

    return None


def extract_us_phone(text):
    """
    提取美国电话。
    只识别美国电话/取件电话相关字段，避免误抓中国手机号。
    """
    if not text:
        return None

    text = clean_text(text)

    value = extract_field_after_keywords(
        text,
        [
            "美国取件电话",
            "寄件人美国电话",
            "美国电话",
            "取件电话",
        ]
    )

    if not value:
        return None

    match = re.search(
        r"(\+?1[\s\-]?)?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{4})",
        value
    )

    if match:
        return f"{match.group(2)}{match.group(3)}{match.group(4)}"

    return None


def extract_email(text):
    """
    提取邮箱。
    """
    if not text:
        return None

    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    if match:
        return match.group(0)

    return None


def extract_cn_postal_code(text):
    """
    提取中国6位邮编。
    """
    if not text:
        return None

    match = re.search(r"(?<!\d)(\d{6})(?!\d)", text)

    if match:
        return match.group(1)

    return None


# =========================
# 地址
# =========================

def extract_cn_address(text):
    """
    只提取中国地址，避免抓到美国取件地址。
    """
    if not text:
        return None

    text = clean_text(text)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    address_keywords = [
        "中国地址",
        "国内地址",
        "收件地址",
    ]

    stop_keywords = [
        "国内电话",
        "电话",
        "国内邮编",
        "邮编",
        "邮箱",
        "得知渠道",
        "到达中国大陆日期",
        "回国日期",
        "箱子数量",
        "标准尺寸",
        "运单打印",
        "中国国籍",
        "注意事项",
        "国际",
        "代清关",
    ]

    for i, line in enumerate(lines):
        if any(keyword in line for keyword in address_keywords):
            value = re.sub(
                r"^(中国地址|国内地址|收件地址)[：:\s]*",
                "",
                line
            ).strip()

            address_parts = []

            if value:
                address_parts.append(value)

            for next_line in lines[i + 1:]:
                if any(stop in next_line for stop in stop_keywords):
                    break

                address_parts.append(next_line)

            if address_parts:
                return " ".join(address_parts).strip()

    return None


def extract_us_address(text):
    """
    提取美国取件地址。
    支持：
    美国取件地址/邮编 请具体到房间号
    Unit 648, 17600 Cartwright Rd
    Irvine, CA 92614
    """
    if not text:
        return None

    text = clean_text(text)
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    address_keywords = [
        "美国取件地址",
        "美国地址",
        "取件地址",
    ]

    stop_keywords = [
        "收件人姓名",
        "中国地址",
        "国内电话",
        "国内邮编",
        "邮箱",
        "得知渠道",
        "到达中国大陆日期",
        "回国日期",
        "箱子数量",
    ]

    for i, line in enumerate(lines):
        if any(keyword in line for keyword in address_keywords):

            collected = []

            value = re.split(r"[：:]", line, maxsplit=1)[-1].strip()

            if value != line:
                collected.append(value)

            for next_line in lines[i + 1:]:
                if any(stop in next_line for stop in stop_keywords):
                    break

                collected.append(next_line)

            if collected:
                return " ".join(collected)

    return None


# =========================
# 路线 / 箱型
# =========================

def extract_shipping_route(text):
    """
    识别路线：
    国际
    代清关
    """
    if not text:
        return None

    text = normalize_box_text(text)

    if "代清关" in text:
        return "代清关"

    if re.search(r"代\s*\d*[大小中]", text):
        return "代清关"

    if "国际" in text:
        return "国际"

    return None


def extract_box_counts(text):
    """
    提取箱子数量。
    支持：
    国际4大2中1小
    国际四大二中一小
    代3大
    2 large box 国际
    large box * 2
    大箱*2，小箱*1
    2个大箱，1个小箱
    """

    text = normalize_box_text(text).lower()

    large = 0
    medium = 0
    small = 0

    # =========================
    # 中文简写：2大 / 2中 / 1小
    # =========================

    m = re.search(r"(\d+)\s*大", text)
    if m:
        large = int(m.group(1))

    m = re.search(r"(\d+)\s*中", text)
    if m:
        medium = int(m.group(1))

    m = re.search(r"(\d+)\s*小", text)
    if m:
        small = int(m.group(1))

    # =========================
    # 中文完整：2个大箱 / 2大箱
    # =========================

    m = re.search(r"(\d+)\s*个?\s*大箱", text)
    if m:
        large = int(m.group(1))

    m = re.search(r"(\d+)\s*个?\s*中箱", text)
    if m:
        medium = int(m.group(1))

    m = re.search(r"(\d+)\s*个?\s*小箱", text)
    if m:
        small = int(m.group(1))

    # =========================
    # 中文反向：大箱*2 / 大箱x2 / 大箱×2
    # =========================

    m = re.search(r"大箱\s*[*x×]?\s*(\d+)", text)
    if m:
        large = int(m.group(1))

    m = re.search(r"中箱\s*[*x×]?\s*(\d+)", text)
    if m:
        medium = int(m.group(1))

    m = re.search(r"小箱\s*[*x×]?\s*(\d+)", text)
    if m:
        small = int(m.group(1))

    # =========================
    # 英文正向：2 large box / 2 medium boxes
    # =========================

    m = re.search(r"(\d+)\s*(large|big)\s*(box|boxes)?", text)
    if m:
        large = int(m.group(1))

    m = re.search(r"(\d+)\s*(medium|middle)\s*(box|boxes)?", text)
    if m:
        medium = int(m.group(1))

    m = re.search(r"(\d+)\s*small\s*(box|boxes)?", text)
    if m:
        small = int(m.group(1))

    # =========================
    # 英文反向：large box * 2 / small box x1
    # =========================

    m = re.search(r"(large|big)\s*(box|boxes)?\s*[*x×]?\s*(\d+)", text)
    if m:
        large = int(m.group(3))

    m = re.search(r"(medium|middle)\s*(box|boxes)?\s*[*x×]?\s*(\d+)", text)
    if m:
        medium = int(m.group(3))

    m = re.search(r"small\s*(box|boxes)?\s*[*x×]?\s*(\d+)", text)
    if m:
        small = int(m.group(2))

    return {
        "large": large,
        "medium": medium,
        "small": small,
    }


def build_box_summary(box_counts):
    """
    {'large': 3, 'medium': 2, 'small': 1}
    -> 3大2中1小
    """
    parts = []

    if box_counts["large"] > 0:
        parts.append(f'{box_counts["large"]}大')

    if box_counts["medium"] > 0:
        parts.append(f'{box_counts["medium"]}中')

    if box_counts["small"] > 0:
        parts.append(f'{box_counts["small"]}小')

    return "".join(parts)


def build_route_summary(text):
    """
    国际四大二中一小
    -> 国际4大2中1小
    """
    route = extract_shipping_route(text)
    box_counts = extract_box_counts(text)
    box_summary = build_box_summary(box_counts)

    if route and box_summary:
        return f"{route}{box_summary}"

    if route:
        return route

    if box_summary:
        return box_summary

    return None


# =========================
# Reference / Shipment File Name
# =========================

def generate_reference(name_en, route=None):
    """
    国际:
    thunder-0623-jiayiruan

    代清关:
    thunder-ca-jiayiruan
    """
    if not name_en:
        return None

    name_part = (
        name_en
        .lower()
        .replace(" ", "")
    )

    if route == "代清关":
        return f"thunder-ca-{name_part}"

    ny_time = datetime.now(
        ZoneInfo("America/New_York")
    )

    mmdd = ny_time.strftime("%m%d")

    return f"thunder-{mmdd}-{name_part}"


def generate_shipment_filename(name_en, route, box_summary):
    """
    Jiawen Zou + 国际 + 3大2中1小
    -> jiawenzou-国际3大2中1小
    """
    if not name_en:
        return None

    name_part = (
        name_en
        .lower()
        .replace(" ", "")
    )

    if not route:
        return f"{name_part}-cannot complete - missing shipping route"

    if not box_summary:
        return f"{name_part}-cannot complete - missing box quantity / box size"

    return f"{name_part}-{route}{box_summary}"


# =========================
# Missing / Unclear
# =========================

def validate_customer_info(result):
    """
    总结缺失信息 / 错误信息
    """
    issues = []

    if not result.get("name_cn"):
        issues.append("收件人中文姓名 missing")

    if not result.get("name_en"):
        issues.append("收件人英文姓名 missing")

    if not result.get("phone_cn"):
        issues.append("中国电话 missing")

    if not result.get("address_cn"):
        issues.append("中国地址 missing")

    postal_code = result.get("postal_code_cn")

    if not postal_code:
        issues.append("中国邮编 missing")
    elif not re.fullmatch(r"\d{6}", postal_code):
        issues.append("中国邮编不是6位数，请重新确认")

    if not result.get("email"):
        issues.append("邮箱 missing")

    if not result.get("route"):
        issues.append("线路 missing")

    if not result.get("box_summary"):
        issues.append("箱子数量/尺寸 missing")

    return issues


# =========================
# 主 Parser
# =========================

def parse_customer_info(text):
    """
    输入客户原始信息，输出结构化字段。
    """
    result = {}

    result["name_cn"] = extract_recipient_name_cn(text)

    result["name_en"] = (
        convert_cn_name_to_pinyin(result["name_cn"])
        if result["name_cn"]
        else None
    )

    result["phone_us"] = extract_us_phone(text)

    result["address_us"] = extract_us_address(text)

    result["phone_cn"] = extract_cn_phone(text)

    result["postal_code_cn"] = extract_cn_postal_code(text)

    result["address_cn"] = extract_cn_address(text)

    result["email"] = extract_email(text)

    result["route"] = extract_shipping_route(text)

    result["box_counts"] = extract_box_counts(text)

    result["box_summary"] = build_box_summary(
        result["box_counts"]
    )

    result["route_summary"] = build_route_summary(text)

    result["reference"] = generate_reference(
        result["name_en"],
        result["route"]
    )

    result["shipment_filename"] = generate_shipment_filename(
        result["name_en"],
        result["route"],
        result["box_summary"]
    )

    result["missing_or_unclear"] = validate_customer_info(result)

    return result


# =========================
# 测试
# =========================

if __name__ == "__main__":

    sample = """
收件人姓名 与回国本人/护照格式一致：邹嘉文 Zou/Jiawen

中国地址：
济南市市中区阳光舜城南山苑9-2-501

国内电话：15969687272

国内邮编：250001

邮箱：zoujiawen0428@163.com

国际3大2中1小

美国取件电话 7073056721

美国取件地址/邮编 请具体到房间号
Unit 648, 17600 Cartwright rd, Irvine, Ca, 92614
"""

    result = parse_customer_info(sample)

    for k, v in result.items():
        print(f"{k}: {v}")













# tests = [
#     "国际2大",
#     "国际四大二中一小",
#     "2 large box 国际",
#     "large box * 2 国际",
#     "大箱*2，小箱*1 国际",
#     "2个大箱，1个小箱 国际",
#     "medium box x3 代清关",
# ]

# for t in tests:
#     counts = extract_box_counts(t)
#     print(t, "->", counts, "->", build_box_summary(counts))