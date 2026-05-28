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


# ===== 箱型对应限重(lbs) =====
BIG_BOX_WEIGHT_LIMIT = 55
MEDIUM_BOX_WEIGHT_LIMIT = 45
SMALL_BOX_WEIGHT_LIMIT = 35


# ===== 单边超长阈值(inch) =====
LONGEST_SIDE_LIMIT = 48
SECOND_LONGEST_SIDE_LIMIT = 28


# ===== girth 阈值 最长边+横截面周长 (inch) =====
# girth = a + 2(b+h)
OVERSIZE_GIRTH_LIMIT = 130
GIRTH_SURCHARGE_LIMIT = 95


# ===== 超长费用($) =====
INTERNATIONAL_LONG_FEE = 50
DOMESTIC_LONG_FEE = 30


# ===== Oversize超长费用($) =====
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
def calculate_extra_fee(
    length,
    width,
    height,
    is_international,
    unit,
    actual_weight=None,
    actual_weight_unit="lb",
    base_price=None
):
    
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

    # 实际重量处理
    actual_weight_lbs = None

    if actual_weight is not None:
        if actual_weight_unit == "kg":
            actual_weight_lbs = math.ceil(actual_weight * 2.20462)
        else:
            actual_weight_lbs = math.ceil(actual_weight)

        billable_weight = max(dim_weight, actual_weight_lbs)
    else:
        billable_weight = dim_weight

    # 国际 / 国内参数
    if is_international:
        weight_limit = INTERNATIONAL_WEIGHT_LIMIT
        overweight_rate = INTERNATIONAL_OVERWEIGHT_RATE
        penalty = INTERNATIONAL_OVERWEIGHT_PENALTY
        long_fee = INTERNATIONAL_LONG_FEE
    else:
        weight_limit = DOMESTIC_WEIGHT_LIMIT
        overweight_rate = DOMESTIC_OVERWEIGHT_RATE
        penalty = DOMESTIC_OVERWEIGHT_PENALTY
        long_fee = DOMESTIC_LONG_FEE

    # 超重费
    overweight_fee = 0

    if billable_weight > weight_limit:
        overweight_lbs = billable_weight - weight_limit
        overweight_fee = overweight_lbs * overweight_rate + penalty

    # 超长 / 单边超长 / oversize
    size_fee = 0
    size_fee_name = ""

    girth_value = a + 2 * (b + h)

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

    total_extra_fee = overweight_fee + size_fee

    # ===== 输出到网页 =====

    st.write("## 📦 额外费用计算")

    st.write(
        f"体积重：({length} × {width} × {height}) / 139 = {dim_weight} lbs"
    )

    if actual_weight_lbs is not None:
        st.write(
            f"实际重量：{actual_weight_lbs} lbs；"
            f"体积重：{dim_weight} lbs；"
            f"最终计费重量取较大值 = {billable_weight} lbs"
        )
    else:
        st.write(
            f"最终计费重量：{billable_weight} lbs"
        )

    parts = []

    if overweight_fee > 0:
        parts.append(f"{overweight_fee:g}（超重费）")

        st.write(
            f"超重费：({billable_weight}-{weight_limit}) × "
            f"{overweight_rate} + {penalty} = "
            f"{overweight_fee:g} 美金"
        )
    else:
        st.write("超重费：0 美金")

    # ===== 超长规则检查 =====

    st.write("#### 📏 超长规则检查")

    # a. 最长边
    if a >= LONGEST_SIDE_LIMIT:
        st.write(
            f"❌ 最长边 = {a} inch ≥ {LONGEST_SIDE_LIMIT} inch"
            f" → 触发单边超长费 {long_fee} 美金"
        )
    else:
        st.write(
            f"✅ 最长边 = {a} inch < {LONGEST_SIDE_LIMIT} inch"
        )

    # b. 次长边
    if b >= SECOND_LONGEST_SIDE_LIMIT:
        st.write(
            f"❌ 次长边 = {b} inch ≥ {SECOND_LONGEST_SIDE_LIMIT} inch"
            f" → 触发单边超长费 {long_fee} 美金"
        )
    else:
        st.write(
            f"✅ 次长边 = {b} inch < {SECOND_LONGEST_SIDE_LIMIT} inch"
        )

    # c. 最长边 + 横截面周长
    if girth_value >= OVERSIZE_GIRTH_LIMIT:
        st.write(
            f"❌ Oversize超长："
            f"{a} + 2 × ({b} + {h}) = {girth_value} ≥ {OVERSIZE_GIRTH_LIMIT}"
            f" → 触发 Oversize超长费 {OVERSIZE_FEE} 美金"
        )
    elif girth_value >= GIRTH_SURCHARGE_LIMIT:
        st.write(
            f"❌ 最长边+横截面周长："
            f"{a} + 2 × ({b} + {h}) = {girth_value} ≥ {GIRTH_SURCHARGE_LIMIT}"
            f" → 触发超长费 {long_fee} 美金"
        )
    else:
        st.write(
            f"✅ 最长边+横截面周长："
            f"{a} + 2 × ({b} + {h}) = {girth_value} < {GIRTH_SURCHARGE_LIMIT}"
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


    if base_price is not None:
    final_total = base_price + total_extra_fee
    st.success(
        f"总价 = 单箱运费 {base_price:g} + 额外费用 {total_extra_fee:g} = "
        f"{final_total:g} 美金"
    )

    st.write("")
    st.write("🐸 宮里帮您节省了30秒的计算时间！")
    st.write("🧧 发财！发货！红包拿来！")

    return total_extra_fee



# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# 使用 Streamlit 生成网页简易UI界面，出现输入框

tab1, tab2, tab3 = st.tabs([
    "额外费用计算",
    "尺寸/重量换算",
    "FedEx邮编查询构思"
])










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





with tab1:
    st.title("口水蛙的额外费用计算器")

    unit = st.radio(
        "请选择尺寸单位",
        ["inch", "cm"]
    )

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

    st.divider()

    actual_weight_unit = st.radio(
        "实际重量单位",
        ["lb", "kg"],
        key="actual_weight_unit"
    )


    shipping_type = st.radio(
        "是否国际件？",
        ["国际", "国内"]
    )


    is_international = shipping_type == "国际"

    st.divider()

    actual_weight_input = st.text_input(
        f"请输入实际重量（{actual_weight_unit}，选填）",
        placeholder="不填则只按体积重计算",
        key="actual_weight_input"
    )

    base_price_input = st.text_input(
    "请输入单箱价格（可不填）",
    placeholder="不填则只计算额外费用",
    key="base_price_input"
    )

    


    st.divider()


    if st.button("计算额外费用"):

        try:
            length = float(length)
            width = float(width)
            height = float(height)

            actual_weight = None
            if actual_weight_input.strip() != "":
                actual_weight = float(actual_weight_input)


            base_price = None
            if base_price_input.strip() != "":
                base_price = float(base_price_input)

            calculate_extra_fee(
                length,
                width,
                height,
                is_international,
                unit,
                actual_weight,
                actual_weight_unit,
                base_price
            )
            # st.balloons()    ######################################## 特效！！！！！！！！！

        except ValueError:
            st.error("请输入有效数字")

        except Exception as e:
            st.error(f"程序错误：{e}")

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

with tab2:

    st.title("📏 口水蛙的尺寸换算器")

    convert_direction = st.radio(
        "请选择换算方向",
        ["inch → cm", "cm → inch"],
        key="convert_direction"
    )

    convert_length = st.text_input(
        "请输入长度",
        placeholder="长度",
        key="convert_length"
    )

    convert_width = st.text_input(
        "请输入宽度",
        placeholder="宽度",
        key="convert_width"
    )

    convert_height = st.text_input(
        "请输入高度",
        placeholder="高度",
        key="convert_height"
    )

    if st.button("换算尺寸", key="convert_button"):

        try:

            values = []

            # 收集用户输入
            if convert_length.strip() != "":
                values.append(float(convert_length))

            if convert_width.strip() != "":
                values.append(float(convert_width))

            if convert_height.strip() != "":
                values.append(float(convert_height))

            # 至少输入一个
            if len(values) == 0:
                st.error("请至少输入一个数字")

            else:

                st.balloons() 

                # inch → cm
                if convert_direction == "inch → cm":

                    converted_values = [
                        round(v * 2.54, 2)
                        for v in values
                    ]

                    original_text = " × ".join(
                        str(v) for v in values
                    )

                    converted_text = " × ".join(
                        str(v) for v in converted_values
                    )

                    st.success(
                        f"{original_text} inch\n\n"
                        f"=\n\n"
                        f"{converted_text} cm"
                    )

                # cm → inch
                else:

                    converted_values = [
                        round(v / 2.54, 2)
                        for v in values
                    ]

                    original_text = " × ".join(
                        str(v) for v in values
                    )

                    converted_text = " × ".join(
                        str(v) for v in converted_values
                    )

                    st.success(
                        f"{original_text} cm\n\n"
                        f"=\n\n"
                        f"{converted_text} inch"
                    )

        except ValueError:
            st.error("请输入有效数字")


    st.divider()


    st.title("⚖️ 重量换算器")

    weight_direction = st.radio(
        "请选择重量换算方向",
        ["lb → kg", "kg → lb"],
        key="weight_direction"
    )

    weight_input = st.text_input(
        "请输入重量",
        placeholder="重量",
        key="weight_input"
    )

    if st.button("换算重量", key="weight_convert_button"):

        try:

            weight_value = float(weight_input)

            # lb → kg
            if weight_direction == "lb → kg":

                converted_weight = round(weight_value / 2.20462, 2)

                st.success(
                    f"{weight_value} lbs\n\n"
                    f"=\n\n"
                    f"{converted_weight} kg"
                )

            # kg → lb
            else:

                converted_weight = round(weight_value * 2.20462, 2)

                st.success(
                    f"{weight_value} kg\n\n"
                    f"=\n\n"
                    f"{converted_weight} lbs"
                )

        except ValueError:
            st.error("请输入有效数字")







with tab3:

    st.title("FedEx 中国邮编服务范围查询构思")

    st.info(
        "未来可以接入 FedEx Developer Portal API。"
        "输入中国 6 位邮编后，系统自动判断：正常服务范围 / 偏远地区 / 邮编有误。"
    )

    postal_code = st.text_input(
        "请输入中国 6 位邮编",
        placeholder="例如：200000",
        key="fedex_postal_code"
    )

    if st.button("模拟查询", key="fedex_postal_check_button"):

        if postal_code.strip() == "":
            st.error("请输入邮编")

        elif not postal_code.isdigit() or len(postal_code) != 6:
            st.error("邮编格式有误：请输入 6 位数字")

        else:
            st.success("邮编格式正确。未来这里会调用 FedEx API 查询服务范围。")

            st.write("### 未来返回结果示例")
            st.write("✅ 正常服务范围")
            st.write("⚠️ 偏远地区，需要额外确认费用或时效")
            st.write("❌ 邮编有误 / FedEx 无法识别")

    st.divider()

    st.write("### 为什么要做这个功能")
    st.write(
        "目前从小程序手动查询邮编服务范围比较慢。"
        "如果通过 API 自动查询，员工只需要输入邮编，几秒内就能得到判断结果，"
        "适合客服报价和下单前检查。"
    )

    st.write("### 后续开发思路")
    st.write(
        "1. 申请 / 配置 FedEx Developer Portal API 权限\n\n"
        "2. 用邮编调用 FedEx 服务范围或报价相关接口\n\n"
        "3. 解析返回结果，判断是否正常服务、偏远或无效邮编\n\n"
        "4. 把结果展示在 Streamlit 页面中"
    )




# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# st.divider()

# st.title("大件 / 重货优惠计算器")

# large_unit = st.radio(
#     "请选择尺寸单位",
#     ["inch", "cm"],
#     key="large_unit"
# )

# large_length = st.text_input(
#     f"请输入长度（{large_unit}）",
#     placeholder="长度",
#     key="large_length"
# )

# large_width = st.text_input(
#     f"请输入宽度（{large_unit}）",
#     placeholder="宽度",
#     key="large_width"
# )

# large_height = st.text_input(
#     f"请输入高度（{large_unit}）",
#     placeholder="高度",
#     key="large_height"
# )

# large_shipping_type = st.radio(
#     "是否国际件？",
#     ["国际", "国内"],
#     key="large_shipping_type"
# )

# large_is_international = large_shipping_type == "国际"

# if st.button("计算大件 / 重货优惠价格"):

#     try:
#         large_length = float(large_length)
#         large_width = float(large_width)
#         large_height = float(large_height)

#         calculate_large_package_discount_price(
#             large_length,
#             large_width,
#             large_height,
#             large_is_international,
#             large_unit
#         )

#     except:
#         st.error("请输入有效数字")

