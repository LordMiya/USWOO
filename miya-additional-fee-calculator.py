#!/usr/bin/env python
# coding: utf-8




import math
import streamlit as st
import pandas as pd



EXCEL_FILE = "ODA_OPA_tiers_codes.xlsx" # 全球偏远地区附加费表格

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
GIRTH_SURCHARGE_LIMIT = 105


# ===== 超长费用($) =====
INTERNATIONAL_LONG_FEE = 50
DOMESTIC_LONG_FEE = 30
INTERNATIONALANDDOMESTIC_LONG_FEE = INTERNATIONAL_LONG_FEE + DOMESTIC_LONG_FEE # 代清关超长费用


# ===== Oversize超长费用($) =====
OVERSIZE_FEE = 200 # 全线路统一价格


# ===== 不同物流线路 大箱限重(lbs)  =====
INTERNATIONAL_WEIGHT_LIMIT = 55
DOMESTIC_WEIGHT_LIMIT = 50
INTERNATIONALANDDOMESTIC_WEIGHT_LIMIT = 50 # 代清关大箱限重


# =====  不同物流线路 超重费率 =====
INTERNATIONAL_OVERWEIGHT_RATE = 3.6
INTERNATIONAL_OVERWEIGHT_PENALTY = 30

DOMESTIC_OVERWEIGHT_RATE = 1.5
DOMESTIC_OVERWEIGHT_PENALTY = 25

INTERNATIONALANDDOMESTIC_OVERWEIGHT_RATE = 5.8 # 代清关超重系数
INTERNATIONALANDDOMESTIC_WEIGHT_LIMIT_OVERWEIGHT_PENALTY = 25 # 代清关超重罚款


# ===== 通用超长 / Oversize 新增规则 =====
VOLUME_SURCHARGE_LIMIT = 10368        # a*b*h >= 10368，收普通超长费
OVERSIZE_SIDE_LIMIT = 95              # 最长边 >= 95，收 Oversize超长费
OVERSIZE_WEIGHT_LIMIT = 110           # 实际重量 >= 110 lbs，收 Oversize超长费
OVERSIZE_VOLUME_LIMIT = 17280         # a*b*h >= 17280，收 Oversize超长费





# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# # input validation
# def get_dimension_input(name):
#     while True:
#         try:
#             value = float(input(f"请输入{name}（inch）："))

#             if value <= 0:
#                 print("❌ 尺寸必须大于 0")
#                 continue

#             if value > 100:
#                 print("❌ 单边尺寸不能超过 100 inch")
#                 continue

#             return value

#         except ValueError:
#             print("❌ 请输入有效数字")


# def get_international_input():
#     while True:
#         value = input("是否国际件？(y/n)：").strip().lower()

#         if value == "y":
#             return True

#         elif value == "n":
#             return False

#         else:
#             print("❌ 只能输入 y 或 n")



# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# ======================================== 定义定价函数 ========================================

def calculate_shipping_fee(
    length,
    width,
    height,
    route_type,
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

    # ===== 根据线路选择参数 =====

    if route_type == "自主清关":
        weight_limit = INTERNATIONAL_WEIGHT_LIMIT
        overweight_rate = INTERNATIONAL_OVERWEIGHT_RATE
        penalty = INTERNATIONAL_OVERWEIGHT_PENALTY
        long_fee = INTERNATIONAL_LONG_FEE

    elif route_type == "代清关":
        weight_limit = INTERNATIONALANDDOMESTIC_WEIGHT_LIMIT
        overweight_rate = INTERNATIONALANDDOMESTIC_OVERWEIGHT_RATE
        penalty = INTERNATIONALANDDOMESTIC_WEIGHT_LIMIT_OVERWEIGHT_PENALTY
        long_fee = INTERNATIONALANDDOMESTIC_LONG_FEE

    elif route_type == "境内行李":
        weight_limit = DOMESTIC_WEIGHT_LIMIT
        overweight_rate = DOMESTIC_OVERWEIGHT_RATE
        penalty = DOMESTIC_OVERWEIGHT_PENALTY
        long_fee = DOMESTIC_LONG_FEE

    else:
        st.error(f"未知线路类型：{route_type}")
        return None

    # ===== 超重费 =====

    overweight_fee = 0

    if billable_weight > weight_limit:
        overweight_lbs = billable_weight - weight_limit
        overweight_fee = overweight_lbs * overweight_rate + penalty

    # ===== 超长 / 单边超长 / Oversize =====

    size_fee = 0
    size_fee_name = ""

    girth_value = a + 2 * (b + h)

    # NEW: 三边体积规则
    volume_value = a * b * h

    # NEW: Oversize 重量规则只看“实际重量”，不看体积重
    actual_weight_oversize = (
        actual_weight_lbs is not None
        and actual_weight_lbs >= OVERSIZE_WEIGHT_LIMIT
    )

    # NEW / MODIFIED:
    # Oversize 优先级最高
    # 条件：
    # 1. 最长边 >= 95
    # 2. 最长边 + 横截面周长 >= 130
    # 3. 实际重量 >= 110 lbs
    # 4. 三边体积 >= 17280
    if (
        a > OVERSIZE_SIDE_LIMIT
        or girth_value >= OVERSIZE_GIRTH_LIMIT
        or actual_weight_oversize
        or volume_value >= OVERSIZE_VOLUME_LIMIT
    ):
        size_fee = OVERSIZE_FEE
        size_fee_name = "Oversize超长费"

    # NEW / MODIFIED:
    # 未触发 Oversize 时，再判断普通超长
    # 条件：
    # 1. 最长边 >= 48
    # 2. 次长边 >= 30
    # 3. 最长边 + 横截面周长 >= 105
    # 4. 三边体积 >= 10368
    elif a >= LONGEST_SIDE_LIMIT:
        size_fee = long_fee
        size_fee_name = "单边超长费"

    elif b >= SECOND_LONGEST_SIDE_LIMIT:
        size_fee = long_fee
        size_fee_name = "单边超长费"

    elif girth_value >= GIRTH_SURCHARGE_LIMIT:
        size_fee = long_fee
        size_fee_name = "超长费"

    elif volume_value >= VOLUME_SURCHARGE_LIMIT:
        size_fee = long_fee
        size_fee_name = "超长费"

    total_extra_fee = overweight_fee + size_fee

    # ===== 输出到网页 =====

    st.write("## 📦 额外费用计算")
    st.write(f"线路类型：{route_type}")

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

    if a >= LONGEST_SIDE_LIMIT:
        st.write(
            f"❌ 最长边 = {a} inch ≥ {LONGEST_SIDE_LIMIT} inch"
            f" → 触发单边超长费 {long_fee} 美金"
        )
    else:
        st.write(
            f"✅ 最长边 = {a} inch < {LONGEST_SIDE_LIMIT} inch"
        )

    if b >= SECOND_LONGEST_SIDE_LIMIT:
        st.write(
            f"❌ 次长边 = {b} inch ≥ {SECOND_LONGEST_SIDE_LIMIT} inch"
            f" → 触发单边超长费 {long_fee} 美金"
        )
    else:
        st.write(
            f"✅ 次长边 = {b} inch < {SECOND_LONGEST_SIDE_LIMIT} inch"
        )

    if girth_value >= GIRTH_SURCHARGE_LIMIT:
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

    # NEW: 普通超长的体积规则展示
    if volume_value >= VOLUME_SURCHARGE_LIMIT:
        st.write(
            f"❌ 三边体积："
            f"{a} × {b} × {h} = {volume_value} ≥ {VOLUME_SURCHARGE_LIMIT}"
            f" → 触发超长费 {long_fee} 美金"
        )
    else:
        st.write(
            f"✅ 三边体积："
            f"{a} × {b} × {h} = {volume_value} < {VOLUME_SURCHARGE_LIMIT}"
        )

    # ===== Oversize规则检查 =====

    st.write("#### 🚨 Oversize规则检查")

    if a >= OVERSIZE_SIDE_LIMIT:
        st.write(
            f"❌ 最长边 = {a} inch ≥ {OVERSIZE_SIDE_LIMIT} inch"
            f" → 触发 Oversize超长费 {OVERSIZE_FEE} 美金"
        )
    else:
        st.write(
            f"✅ 最长边 = {a} inch < {OVERSIZE_SIDE_LIMIT} inch"
        )

    if girth_value >= OVERSIZE_GIRTH_LIMIT:
        st.write(
            f"❌ 最长边+横截面周长："
            f"{a} + 2 × ({b} + {h}) = {girth_value} ≥ {OVERSIZE_GIRTH_LIMIT}"
            f" → 触发 Oversize超长费 {OVERSIZE_FEE} 美金"
        )
    else:
        st.write(
            f"✅ 最长边+横截面周长："
            f"{a} + 2 × ({b} + {h}) = {girth_value} < {OVERSIZE_GIRTH_LIMIT}"
        )

    # NEW: Oversize 实际重量规则展示
    if actual_weight_lbs is not None:
        if actual_weight_lbs >= OVERSIZE_WEIGHT_LIMIT:
            st.write(
                f"❌ 实际重量 = {actual_weight_lbs} lbs ≥ {OVERSIZE_WEIGHT_LIMIT} lbs"
                f" → 触发 Oversize超长费 {OVERSIZE_FEE} 美金"
            )
        else:
            st.write(
                f"✅ 实际重量 = {actual_weight_lbs} lbs < {OVERSIZE_WEIGHT_LIMIT} lbs"
            )
    else:
        st.write(
            f"⚠️ 未填写实际重量，暂不判断实际重量 >= {OVERSIZE_WEIGHT_LIMIT} lbs 的 Oversize规则"
        )

    if volume_value >= OVERSIZE_VOLUME_LIMIT:
        st.write(
            f"❌ 三边体积："
            f"{a} × {b} × {h} = {volume_value} ≥ {OVERSIZE_VOLUME_LIMIT}"
            f" → 触发 Oversize超长费 {OVERSIZE_FEE} 美金"
        )
    else:
        st.write(
            f"✅ 三边体积："
            f"{a} × {b} × {h} = {volume_value} < {OVERSIZE_VOLUME_LIMIT}"
        )

    # ===== 最终收取的超长费用 =====
    # 注意：超长费用只取最高优先级，不重复叠加

    if size_fee > 0:
        parts.append(f"{size_fee:g}({size_fee_name})")

        st.write(
            f"最终收取：{size_fee_name} = {size_fee:g} 美金"
        )
    else:
        st.write("最终收取：超长相关费用 = 0 美金")

    # NEW: 未填写实际重量时，在最终输出附近提醒费用可能偏低
    if actual_weight_lbs is None:
        st.warning(
            f"⚠️ 未填写实际重量，系统未检查『实际重量 >= {OVERSIZE_WEIGHT_LIMIT} lbs 收 Oversize超长费』规则，"
        )

    # ===== 额外费用总额 =====

    if parts:
        st.success(
            f"额外费用 = {' + '.join(parts)} = "
            f"{total_extra_fee:g} 美金"
        )
    else:
        st.success("额外费用 = 0 美金")

    # ===== 如果有单箱运费，计算最终总价 =====

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





# =========================
# 读取并清洗 FedEx ODA 表
# =========================

@st.cache_data
def load_fedex_oda_data():

    raw_df = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Postal Codes and Tiers ",
        header=None
    )

    df = raw_df.iloc[10:].copy()

    df = df.iloc[:, :9]

    df.columns = [
        "country",
        "country_code",
        "city",
        "begin_postal",
        "end_postal",
        "opa_parcel",
        "opa_freight",
        "oda_parcel",
        "oda_freight"
    ]

    df = df[df["country"].notna()]

    df["begin_postal"] = pd.to_numeric(
        df["begin_postal"],
        errors="coerce"
    )

    df["end_postal"] = pd.to_numeric(
        df["end_postal"],
        errors="coerce"
    )

    china_df = df[
        df["country_code"] == "CN"
    ].copy()

    return china_df


# =========================
# 邮编格式检查
# =========================

def is_valid_china_postal_format(postal_code):
    postal_code = str(postal_code).strip()
    return len(postal_code) == 6 and postal_code.isdigit()


# =========================
# 查询函数
# =========================

def check_china_fedex_oda(postal_code, china_df):
    postal_code_str = str(postal_code).strip()

    if not is_valid_china_postal_format(postal_code_str):
        return {
            "status": "invalid",
            "icon": "❌",
            "message": "查不到此邮政编码，请与客户重新确认",
            "postal_code": postal_code_str
        }

    postal_code_num = int(postal_code_str)

    matched = china_df[
        (china_df["begin_postal"] <= postal_code_num) &
        (china_df["end_postal"] >= postal_code_num)
    ]

    if matched.empty:
        return {
            "status": "normal",
            "icon": "✅",
            "message": "此邮政编码属于正常服务范围",
            "postal_code": postal_code_str
        }

    row = matched.iloc[0]
    oda_parcel = row["oda_parcel"]

    if oda_parcel == "Tier B":
        return {
            "status": "oda_tier_b",
            "icon": "⚠️",
            "message": "此邮政编码需要收取超范围派送附加费（Tier B）",
            "postal_code": postal_code_str,
            "begin_postal": int(row["begin_postal"]),
            "end_postal": int(row["end_postal"]),
            "oda_parcel": oda_parcel,
            # "fee_note": "USD 28.20/票 或 USD 0.43/kg，取较高值"
        }

    if oda_parcel == "No":
        return {
            "status": "manual_check",
            "icon": "❗",
            "message": "此邮政编码需要再次确认，可能涉及其他超范围服务规则",
            "postal_code": postal_code_str,
            "begin_postal": int(row["begin_postal"]),
            "end_postal": int(row["end_postal"]),
            "oda_parcel": oda_parcel
        }

    return {
        "status": "unknown",
        "icon": "❗",
        "message": "查询结果异常，请人工确认",
        "postal_code": postal_code_str,
        "begin_postal": int(row["begin_postal"]),
        "end_postal": int(row["end_postal"]),
        "oda_parcel": oda_parcel
    }




















# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# 使用 Streamlit 生成网页简易UI界面，出现输入框




tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "自主清关",
    "代清关",
    "境内行李",
    "尺寸/重量换算",
    "FedEx邮编查询构思",
    "中国邮编查询"
])

# =====================================================================
# TAB 1 自主清关
# =====================================================================

with tab1:

    st.title("自主蛙的费用计算器")

    st.write("")

    st.info("当前计算器适用于：自主清关 / 国际线路")

    route_type = "自主清关"

    unit = st.radio(
        "请选择尺寸单位",
        ["inch", "cm"],
        key="tab1_unit"
    )

    length = st.text_input(
        f"请输入长度（{unit}）",
        placeholder="长度",
        key="tab1_length"
    )

    width = st.text_input(
        f"请输入宽度（{unit}）",
        placeholder="宽度",
        key="tab1_width"
    )

    height = st.text_input(
        f"请输入高度（{unit}）",
        placeholder="高度",
        key="tab1_height"
    )

    st.divider()

    actual_weight_unit = st.radio(
        "实际重量单位",
        ["lb", "kg"],
        key="tab1_actual_weight_unit"
    )

    actual_weight_input = st.text_input(
        f"请输入实际重量（{actual_weight_unit}，选填）",
        placeholder="不填则只按体积重计算",
        key="tab1_actual_weight_input"
    )

    base_price_input = st.text_input(
        "请输入单箱价格（选填）",
        placeholder="不填则只计算额外费用",
        key="tab1_base_price_input"
    )

    st.divider()

    if st.button("计算费用", key="tab1_calculate_button"):

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

            calculate_shipping_fee(
                length,
                width,
                height,
                route_type,
                unit,
                actual_weight,
                actual_weight_unit,
                base_price
            )

        except ValueError:
            st.error("请输入有效数字")

        except Exception as e:
            st.error(f"程序错误：{e}")

# =====================================================================
# TAB 2 代清关
# =====================================================================

with tab2:

    st.title("代清蛙的费用计算器")

    st.write("")

    st.info("当前计算器适用于：代清关 / 国际线路")

    route_type = "代清关"

    unit = st.radio(
        "请选择尺寸单位",
        ["inch", "cm"],
        key="tab2_unit"
    )

    length = st.text_input(
        f"请输入长度（{unit}）",
        placeholder="长度",
        key="tab2_length"
    )

    width = st.text_input(
        f"请输入宽度（{unit}）",
        placeholder="宽度",
        key="tab2_width"
    )

    height = st.text_input(
        f"请输入高度（{unit}）",
        placeholder="高度",
        key="tab2_height"
    )

    st.divider()

    actual_weight_unit = st.radio(
        "实际重量单位",
        ["lb", "kg"],
        key="tab2_actual_weight_unit"
    )

    actual_weight_input = st.text_input(
        f"请输入实际重量（{actual_weight_unit}，选填）",
        placeholder="不填则只按体积重计算",
        key="tab2_actual_weight_input"
    )

    base_price_input = st.text_input(
        "请输入单箱价格（选填）",
        placeholder="不填则只计算额外费用",
        key="tab2_base_price_input"
    )

    st.divider()

    if st.button("计算费用", key="tab2_calculate_button"):

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

            calculate_shipping_fee(
                length,
                width,
                height,
                route_type,
                unit,
                actual_weight,
                actual_weight_unit,
                base_price
            )

        except ValueError:
            st.error("请输入有效数字")

        except Exception as e:
            st.error(f"程序错误：{e}")




# =====================================================================
# TAB 3 境内行李
# =====================================================================

with tab3:

    st.title("境内蛙的费用计算器")

    st.write("")

    st.info("当前计算器适用于：境内行李 / 国内线路")

    route_type = "境内行李"

    unit = st.radio(
        "请选择尺寸单位",
        ["inch", "cm"],
        key="tab3_unit"
    )

    length = st.text_input(
        f"请输入长度（{unit}）",
        placeholder="长度",
        key="tab3_length"
    )

    width = st.text_input(
        f"请输入宽度（{unit}）",
        placeholder="宽度",
        key="tab3_width"
    )

    height = st.text_input(
        f"请输入高度（{unit}）",
        placeholder="高度",
        key="tab3_height"
    )

    st.divider()

    actual_weight_unit = st.radio(
        "实际重量单位",
        ["lb", "kg"],
        key="tab3_actual_weight_unit"
    )

    actual_weight_input = st.text_input(
        f"请输入实际重量（{actual_weight_unit}，选填）",
        placeholder="不填则只按体积重计算",
        key="tab3_actual_weight_input"
    )

    base_price_input = st.text_input(
        "请输入单箱价格（选填）",
        placeholder="不填则只计算额外费用",
        key="tab3_base_price_input"
    )

    st.divider()

    if st.button("计算费用", key="tab3_calculate_button"):

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

            calculate_shipping_fee(
                length,
                width,
                height,
                route_type,
                unit,
                actual_weight,
                actual_weight_unit,
                base_price
            )

        except ValueError:
            st.error("请输入有效数字")

        except Exception as e:
            st.error(f"程序错误：{e}")




# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
with tab4:



    st.title("⚖️ 口水蛙的重量换算器")

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


    st.divider()


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



















    







with tab5:

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

with tab6:

    st.subheader("口水蛙的中国邮编查询测试1.0")

    st.caption(
        "用于快速判断中国邮编是否涉及 FedEx 超范围派送附加费"
    )


    st.info(
        "系统仅依据 FedEx ODA 邮编表进行匹配，能够识别超范围附加费区域（Tier B）及需人工确认区域（No）。"
        "对于不在 ODA 表中的邮编，系统暂默认视为正常服务范围，暂无法区分“真实存在的正常邮编”与“完全不存在的无效邮编"
    )

    china_df = load_fedex_oda_data()

    postal_code = st.text_input(
        "请输入邮政编码",
        placeholder="6位数"
    )

    if st.button(
        "查询",
        key="oda_query"
    ):

        result = check_china_fedex_oda(
            postal_code,
            china_df
        )

        if result["status"] == "normal":

            st.success(
                f"{result['icon']} {result['message']}"
            )

        elif result["status"] == "oda_tier_b":

            st.warning(
                f"{result['icon']} {result['message']}"
            )

            st.write(
                f"匹配区间：{result['begin_postal']} - {result['end_postal']}"
            )

            # st.write(
            #     f"收费标准：{result['fee_note']}"
            # )

        elif result["status"] == "manual_check":

            st.error(
                f"{result['icon']} {result['message']}"
            )

            st.write(
                f"匹配区间：{result['begin_postal']} - {result['end_postal']}"
            )

        else:

            st.error(
                f"{result['icon']} {result['message']}"
            )
