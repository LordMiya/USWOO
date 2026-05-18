#!/usr/bin/env python
# coding: utf-8




import math
import streamlit as st

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# =================== constant ======================

# ===== 箱型价格($) =====
BIG_BOX_PRICE = 158
MEDIUM_BOX_PRICE = 138
SMALL_BOX_PRICE = 98


# ===== 箱型对应重量(lbs) =====
BIG_BOX_WEIGHT_LIMIT = 55
MEDIUM_BOX_WEIGHT_LIMIT = 45
SMALL_BOX_WEIGHT_LIMIT = 35


# ===== 单边超长阈值(inch) =====
LONGEST_SIDE_LIMIT = 48
SECOND_LONGEST_SIDE_LIMIT = 28


# ===== girth 阈值 (inch) =====
# girth = a + 2(b+h)
OVERSIZE_GIRTH_LIMIT = 130
GIRTH_SURCHARGE_LIMIT = 95


# ===== 超长费用($) =====
INTERNATIONAL_LONG_FEE = 50
DOMESTIC_LONG_FEE = 30


# ===== Oversize费用($) =====
OVERSIZE_FEE = 100


# ===== 不同物流线路 大箱限重(lbs)  =====
INTERNATIONAL_WEIGHT_LIMIT = 55
DOMESTIC_WEIGHT_LIMIT = 50


# =====  不同物流线路 超重费率 =====
INTERNATIONAL_OVERWEIGHT_RATE = 3.6
INTERNATIONAL_OVERWEIGHT_PENALTY = 30

DOMESTIC_OVERWEIGHT_RATE = 1.5
DOMESTIC_OVERWEIGHT_PENALTY = 25





# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# input validation
def get_dimension_input(name):
    while True:
        try:
            value = float(input(f"请输入{name}（inch）："))

            if value <= 0:
                print("❌ 尺寸必须大于 0")
                continue

            if value > 100:
                print("❌ 单边尺寸不能超过 100 inch")
                continue

            return value

        except ValueError:
            print("❌ 请输入有效数字")


def get_international_input():
    while True:
        value = input("是否国际件？(y/n)：").strip().lower()

        if value == "y":
            return True

        elif value == "n":
            return False

        else:
            print("❌ 只能输入 y 或 n")



# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# ======================================== 定义额外定价函数 ========================================
def calculate_extra_fee(length, width, height, is_international, unit):
    
    # 如果是 cm，先换算成 inch
    if unit == "cm":
        length = length / 2.54
        width = width / 2.54
        height = height / 2.54
    
    # 箱子三维进一法到个位数，单位为 inch
    length = math.ceil(length)
    width = math.ceil(width)
    height = math.ceil(height)
    
    # 排序：a=最长边, b=次长边, h=最短边
    dims = sorted([length, width, height], reverse=True)
    a, b, h = dims

    # 体积重，向上取整
    dim_weight = math.ceil((length * width * height) / 139)

    # 国际 / 国内参数
    if is_international:
        weight_limit = 55
        overweight_rate = 3.6
        penalty = 30
        long_fee = 50
    else:
        weight_limit = 50
        overweight_rate = 1.5
        penalty = 25
        long_fee = 30

    # 超重费
    overweight_fee = 0

    if dim_weight > weight_limit:
        overweight_lbs = dim_weight - weight_limit
        overweight_fee = overweight_lbs * overweight_rate + penalty

    # 超长 / 单边超长 / oversize
    size_fee = 0
    size_fee_name = ""

    girth_value = a + 2 * (b + h)

    if girth_value >= 130:
        size_fee = 100
        size_fee_name = "Oversize超长费"
    elif a >= 48:
        size_fee = long_fee
        size_fee_name = "单边超长费"
    elif a < 48 and b >= 28:
        size_fee = long_fee
        size_fee_name = "单边超长费"
    elif girth_value >= 105:
        size_fee = long_fee
        size_fee_name = "超长费"

    total_extra_fee = overweight_fee + size_fee

    # ===== 输出到网页 =====

    st.write("## 📦 额外费用计算")
    st.write(
        f"体积重：({length} × {width} × {height}) / 139 = {dim_weight} lbs"
    )

    parts = []

    if overweight_fee > 0:
        parts.append(f"{overweight_fee:g}（超重费）")

        st.write(
            f"超重费：({dim_weight}-{weight_limit}) × "
            f"{overweight_rate} + {penalty} = "
            f"{overweight_fee:g} 美金"
        )
    else:
        st.write("超重费：0 美金")

    # ===== 超长规则检查 =====

    st.write("#### 📏 超长规则检查")

    # a. 最长边
    if a >= 48:
        st.write(
            f"❌ 最长边 = {a} inch ≥ 48 inch"
            f" → 触发单边超长费 {long_fee} 美金"
        )
    else:
        st.write(
            f"✅ 最长边 = {a} inch < 48 inch"
        )

    # b. 次长边
    if b >= 28:
        st.write(
            f"❌ 次长边 = {b} inch ≥ 28 inch"
            f" → 触发单边超长费 {long_fee} 美金"
        )
    else:
        st.write(
            f"✅ 次长边 = {b} inch < 28 inch"
        )

    # c. 最长边 + 横截面周长
    if girth_value >= 130:
        st.write(
            f"❌ Oversize超长："
            f"{a} + 2 × ({b} + {h}) = {girth_value} ≥ 130"
            f" → 触发 Oversize超长费 100 美金"
        )
    elif girth_value >= 105:
        st.write(
            f"❌ 最长边+横截面周长："
            f"{a} + 2 × ({b} + {h}) = {girth_value} ≥ 105"
            f" → 触发超长费 {long_fee} 美金"
        )
    else:
        st.write(
            f"✅ 最长边+横截面周长："
            f"{a} + 2 × ({b} + {h}) = {girth_value} < 105"
        )

    # ===== 最终收取的超长费用 =====
    # 注意：超长费用只取最高优先级，不重复叠加

    if size_fee > 0:
        parts.append(f"{size_fee:g}（{size_fee_name}）")

        st.write(
            f"最终收取：{size_fee_name} = {size_fee:g} 美金"
        )
    else:
        st.write("最终收取：超长相关费用 = 0 美金")

    # ===== 总额 =====

    if parts:
        st.success(
            f"额外费用 = {' + '.join(parts)} = "
            f"{total_extra_fee:g} 美金"
        )
    else:
        st.success("额外费用 = 0 美金")

    st.write("")
    st.write("🐸 宮里帮您节省了30秒的计算时间！")
    st.write("🧧 发财！发货！红包拿来！")

    return total_extra_fee
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def calculate_large_package_discount_price(length, width, height, is_international, unit):

    if unit == "cm":
        length = length / 2.54
        width = width / 2.54
        height = height / 2.54

    length = math.ceil(length)
    width = math.ceil(width)
    height = math.ceil(height)

    dims = sorted([length, width, height], reverse=True)
    a, b, h = dims

    dim_weight = math.ceil((length * width * height) / 139)

    if is_international:
        long_fee = INTERNATIONAL_LONG_FEE
    else:
        long_fee = DOMESTIC_LONG_FEE

    girth_value = a + 2 * (b + h)

    size_fee = 0
    size_fee_name = ""

    if girth_value >= OVERSIZE_GIRTH_LIMIT:
        size_fee = OVERSIZE_FEE
        size_fee_name = "Oversize超长费"
    elif a >= LONGEST_SIDE_LIMIT:
        size_fee = long_fee
        size_fee_name = "单边超长费"
    elif b >= SECOND_LONGEST_SIDE_LIMIT:
        size_fee = long_fee
        size_fee_name = "单边超长费"
    elif girth_value >= GIRTH_SURCHARGE_LIMIT:
        size_fee = long_fee
        size_fee_name = "超长费"

    best_price = float("inf")
    best_big_count = 0
    best_medium_count = 0
    best_small_count = 0
    best_capacity = 0

    for big_count in range(0, 11):
        for medium_count in range(0, 11):
            for small_count in range(0, 11):

                capacity = (
                    big_count * BIG_BOX_WEIGHT_LIMIT
                    + medium_count * MEDIUM_BOX_WEIGHT_LIMIT
                    + small_count * SMALL_BOX_WEIGHT_LIMIT
                )

                price = (
                    big_count * BIG_BOX_PRICE
                    + medium_count * MEDIUM_BOX_PRICE
                    + small_count * SMALL_BOX_PRICE
                )

                if capacity >= dim_weight and capacity > 0:
                    if price < best_price:
                        best_price = price
                        best_big_count = big_count
                        best_medium_count = medium_count
                        best_small_count = small_count
                        best_capacity = capacity

    total_price = best_price + size_fee

    st.write("## 📦 大件 / 重货优惠计算")
    st.write(f"箱子尺寸：{length} × {width} × {height} inch")
    st.write(f"体积重：({length} × {width} × {height}) / 139 = {dim_weight} lbs")
    st.write(f"最长边 + 横截面周长：{a} + 2 × ({b} + {h}) = {girth_value}")

    st.write("#### 📏 超长费用")

    if size_fee > 0:
        st.write(f"{size_fee_name}：{size_fee} 美金")
    else:
        st.write("超长相关费用：0 美金")

    st.write("#### 📦 优惠拆分方式")

    split_parts = []

    if best_big_count > 0:
        st.write(f"大箱：{BIG_BOX_PRICE} × {best_big_count}")
        split_parts.append(f"{BIG_BOX_PRICE} × {best_big_count}")

    if best_medium_count > 0:
        st.write(f"中箱：{MEDIUM_BOX_PRICE} × {best_medium_count}")
        split_parts.append(f"{MEDIUM_BOX_PRICE} × {best_medium_count}")

    if best_small_count > 0:
        st.write(f"小箱：{SMALL_BOX_PRICE} × {best_small_count}")
        split_parts.append(f"{SMALL_BOX_PRICE} × {best_small_count}")

    st.write(f"可覆盖重量：{best_capacity} lbs")

    if size_fee > 0:
        split_parts.append(f"{size_fee}")

    st.success(
        f"优惠算法总价 = {' + '.join(split_parts)} = {total_price:g} 美金"
    )

    return total_price



# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------














# 使用 Streamlit 生成网页简易UI界面，出现输入框

# st.title("口水蛙的额外费用计算器")

# unit = st.radio(
#     "请选择尺寸单位",
#     ["inch", "cm"]
# )

# length = st.number_input(
#     f"请输入长度（{unit}）",
#     min_value=0.0,
#     value=None,
#     placeholder="长度"
# )

# width = st.number_input(
#     f"请输入宽度（{unit}）",
#     min_value=0.0,
#     value=None,
#     placeholder="宽度"
# )

# height = st.number_input(
#     f"请输入高度（{unit}）",
#     min_value=0.0,
#     value=None,
#     placeholder="高度"
# )






# shipping_type = st.radio(
#     "是否国际件？",
#     ["国际", "国内"]
# )

# is_international = shipping_type == "国际"

# if st.button("计算额外费用"):

#     # st.balloons()

#     calculate_extra_fee(
#         length,
#         width,
#         height,
#         is_international,
#         unit
#     )

st.title("口水蛙的额外费用计算器")

unit = st.radio(
    "请选择尺寸单位",
    ["inch", "cm"]
)

# ===== 三维输入 =====

length = st.text_input(
    f"请输入长度（{unit}）",
    placeholder="长度"
)

width = st.text_input(
    f"请输入宽度（{unit}）",
    placeholder="宽度"
)

height = st.text_input(
    f"请输入高度（{unit}）",
    placeholder="高度"
)

# ===== 国际 / 国内 =====

shipping_type = st.radio(
    "是否国际件？",
    ["国际", "国内"]
)

is_international = shipping_type == "国际"

# ===== 按钮 =====

if st.button("计算额外费用"):

    try:

        # 转成 float
        length = float(length)
        width = float(width)
        height = float(height)

        # st.balloons()

        calculate_extra_fee(
            length,
            width,
            height,
            is_international,
            unit
        )

    except:
        st.error("请输入有效数字")




# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



st.divider()

st.title("大件 / 重货优惠计算器")

large_unit = st.radio(
    "请选择尺寸单位",
    ["inch", "cm"],
    key="large_unit"
)

large_length = st.text_input(
    f"请输入长度（{large_unit}）",
    placeholder="长度",
    key="large_length"
)

large_width = st.text_input(
    f"请输入宽度（{large_unit}）",
    placeholder="宽度",
    key="large_width"
)

large_height = st.text_input(
    f"请输入高度（{large_unit}）",
    placeholder="高度",
    key="large_height"
)

large_shipping_type = st.radio(
    "是否国际件？",
    ["国际", "国内"],
    key="large_shipping_type"
)

large_is_international = large_shipping_type == "国际"

if st.button("计算大件 / 重货优惠价格"):

    try:
        large_length = float(large_length)
        large_width = float(large_width)
        large_height = float(large_height)

        calculate_large_package_discount_price(
            large_length,
            large_width,
            large_height,
            large_is_international,
            large_unit
        )

    except:
        st.error("请输入有效数字")

