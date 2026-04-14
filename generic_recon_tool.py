import streamlit as st
import pandas as pd
from io import BytesIO
from fuzzywuzzy import fuzz

# ===============================================================
# PAGE CONFIG
# ===============================================================
st.set_page_config(page_title="Generic Reconciliation Tool", layout="wide")
st.title("🔍 Two‑File Excel Reconciliation Tool")

st.write(
    "1️⃣ Upload files → 2️⃣ Select Common Identifier → "
    "3️⃣ Select Matching Indicator → 4️⃣ Run Reconciliation"
)
st.markdown("---")

# ===============================================================
# SESSION STATE
# ===============================================================
for key in ["headers_loaded", "matching_selected", "df1", "df2"]:
    st.session_state.setdefault(key, False if "loaded" in key else None)

# ===============================================================
# STEP 1 — UPLOAD FILES
# ===============================================================
c1, c2 = st.columns(2)
with c1:
    file1 = st.file_uploader("📘 Upload File 1 (BASE)", type="xlsx")
with c2:
    file2 = st.file_uploader("📗 Upload File 2 (COMPARISON)", type="xlsx")

if not file1 or not file2:
    st.warning("Upload both files to proceed.")
    st.stop()

st.success("✅ Files uploaded")
st.markdown("---")

# ===============================================================
# STEP 2 — LOAD HEADERS
# ===============================================================
if st.button("✅ Choose Common Identifier"):
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    st.session_state.df1 = df1
    st.session_state.df2 = df2
    st.session_state.headers_loaded = True

if not st.session_state.headers_loaded:
    st.stop()

df1 = st.session_state.df1
df2 = st.session_state.df2

common_1 = st.selectbox("Common Identifier – File 1 (BASE)", df1.columns)
common_2 = st.selectbox("Common Identifier – File 2 (COMPARISON)", df2.columns)

st.markdown("---")

# ===============================================================
# STEP 3 — MATCHING INDICATOR
# ===============================================================
if st.button("✅ Choose Matching Indicator"):
    st.session_state.matching_selected = True

if not st.session_state.matching_selected:
    st.stop()

match_1 = st.selectbox("Matching Column – File 1 (BASE)", df1.columns)
match_2 = st.selectbox("Matching Column – File 2 (COMPARISON)", df2.columns)

st.markdown("---")

# -----------------------------------------------------------
# DATATYPE VALIDATION FOR MATCHING INDICATORS
# -----------------------------------------------------------
def classify_datatype(series: pd.Series) -> str:
    """
    Classifies a pandas Series into a logical datatype category:
    NUMERIC / STRING / DATETIME
    """

    # Drop nulls for accurate detection
    s = series.dropna()

    if s.empty:
        return "UNKNOWN"

    # Check datetime
    if pd.api.types.is_datetime64_any_dtype(s):
        return "DATETIME"

    # Check numeric (int/float)
    if pd.api.types.is_numeric_dtype(s):
        return "NUMERIC"

    # Try coercing object → numeric
    try:
        pd.to_numeric(s.astype(str), errors="raise")
        return "NUMERIC"
    except Exception:
        pass

    return "STRING"


dtype_file1 = classify_datatype(df1[match_1])
dtype_file2 = classify_datatype(df2[match_2])



if dtype_file1 != dtype_file2:
    st.error(
        f"""
        ❌ Datatype mismatch detected for matching indicators
        
        • File 1 column **{match_1}** → {dtype_file1}  
        • File 2 column **{match_2}** → {dtype_file2}
        
        Matching indicators must be of the same datatype to reconcile.
        """
    )
    st.stop()



# -----------------------------------------------------------
# FUZZY MATCHING CONFIG (ONLY FOR STRING INDICATORS)
# -----------------------------------------------------------
use_fuzzy = False
fuzzy_threshold = 100  # strict by default

if dtype_file1 == "STRING":
    st.markdown("### 🔧 Set Fuzzy Matching Threshold")
    st.write("Since the matching indicators are STRING, you can set a Fuzzy Matching Threshold (50-100) to allow for minor typos/spelling differences. A score of 100 means exact match only.")
    use_fuzzy = True
    col1, col2 = st.columns(2)
    with col1:
        fuzzy_threshold = st.slider(
            "",
            min_value=50,
            max_value=100,
            value=90,
            step=5
        )


# ===============================================================
# Fuzzy Score Function (Only for STRING indicators)
# ===============================================================

def fuzzy_score(v1: str, v2: str) -> int:
    """
    Returns fuzzy similarity score between 0 and 100
    """
    return fuzz.token_sort_ratio(v1, v2)



# ===============================================================
# NORMALIZATION FUNCTION
# ===============================================================
def normalize_value(v):
    if pd.isna(v):
        return ""
    v = str(v).strip()
    try:
        n = float(v)
        if n.is_integer():
            return str(int(n))
        return str(n)
    except ValueError:
        return v

# ===============================================================
# STEP 4 — RUN RECONCILIATION
# ===============================================================


if "is_running" not in st.session_state:
    st.session_state.is_running = False


if st.button("🚀 Run Reconciliation", disabled=st.session_state.is_running):

    
    st.session_state.is_running = True

    with st.spinner("Reconciling…"):
        # do_actual_reconciliation_work()


    # -----------------------------------------------------------
    # TABLE 1 — Common Identifier Missing in BASE File (File 1)
    # -----------------------------------------------------------
   
    # -----------------------------------------------------------
    # TABLE 1 — Common Identifier Present in File 2 but NOT in BASE
    # -----------------------------------------------------------

    # miss_common_base = df1[
    #     df1[common_1].isna()
    #     | (df1[common_1].astype(str).str.strip() == "")
    # ]

    # df1_valid = df1.drop(miss_common_base.index)

    # base_keys = (
    #     df1_valid[common_1]
    #     .astype(str)
    #     .str.strip()
    #     .unique()
    #     .tolist()
    # )

    # present_in_comp_not_base = df2[
    #     ~df2[common_2]
    #     .astype(str)
    #     .str.strip()
    #     .isin(base_keys)
    # ]

    # -----------------------------------------------------------
    # TABLE 2 — MISMATCHES (Missing indicator OR Value mismatch)
    # -----------------------------------------------------------
        mismatches = []
        not_found_in_base = []
        not_found_in_comparison = []

        # for _, row1 in df1_valid.iterrows():

        #     key = str(row1[common_1]).strip()

        #     candidates = df2[
        #         df2[common_2].astype(str).str.strip() == key
        #     ]

        #     if candidates.empty:
        #         continue

        #     print(f"Processing Key: {key} | Candidates in File 2: {candidates}")

        #     row2 = candidates.iloc[0]

        #     raw_v1 = row1[match_1]
        #     raw_v2 = row2[match_2]

        #     v1_missing = pd.isna(raw_v1) or str(raw_v1).strip() == ""
        #     v2_missing = pd.isna(raw_v2) or str(raw_v2).strip() == ""

        #     v1 = normalize_value(raw_v1) if not v1_missing else ""
        #     v2 = normalize_value(raw_v2) if not v2_missing else ""

        #     # if v1_missing or v2_missing or v1 != v2:
        #     #     mismatches.append({
        #     #         "Common_Key": key,
        #     #         "File1_Indicator": match_1,
        #     #         "File1_Value": raw_v1,
        #     #         "File2_Indicator": match_2,
        #     #         "File2_Value": raw_v2,
        #     #         "Mismatch_Reason": (
        #     #             "Missing in File 1 (Base)" if v1_missing else
        #     #             "Missing in File 2 (Comparison)" if v2_missing else
        #     #             "Value Mismatch"
        #     #         )
        #     #     })

            
        #     # Determine mismatch
        #     is_mismatch = False
        #     reason = ""
        #     score = None

        #     if v1_missing:
        #         is_mismatch = True
        #         reason = "Missing in File 1"

        #     elif v2_missing:
        #         is_mismatch = True
        #         reason = "Missing in File 2"

        #     else:
        #         if use_fuzzy:
        #             score = fuzzy_score(v1, v2)
        #             if score < fuzzy_threshold:
        #                 is_mismatch = True
        #                 reason = f"Fuzzy Mismatch"
        #         else:
        #             if v1 != v2:
        #                 is_mismatch = True
        #                 reason = "Value Mismatch"

        #     if is_mismatch:
        #         mismatches.append({
        #             "Common_Key": key,
        #             "File1_Indicator": match_1,
        #             "File1_Value": raw_v1,
        #             "File2_Indicator": match_2,
        #             "File2_Value": raw_v2,
        #             "Mismatch_Reason": reason,
        #             "Matching_Score": score
        #         })


        for _, comp_row in df2.iterrows():

            comp_key = str(comp_row[common_2]).strip()

            # 🔍 Look for matching base record
            base_candidates = df1[
                df1[common_1].astype(str).str.strip() == comp_key
            ]

            # --------------------------------------------------
            # CASE 1 — NOT FOUND IN BASE FILE
            # --------------------------------------------------

            if pd.isna(comp_row[common_2]) or str(comp_row[common_2]).strip() == "":
                # print(f"Row '{comp_row}' not found in Comparison File for Comparison Key: '{comp_key}'")
                not_found_in_comparison.append(comp_row.to_dict())

            if base_candidates.empty:
                #  Skip if common identifier is missing in comparison file as well and addding entire row to separate list for review instead of mismatch table
                if pd.isna(comp_row[common_2]) or str(comp_row[common_2]).strip() == "":
                    continue
                    
                else:
                    not_found_in_base.append({"Common Identifier in Comparison File": comp_key})
                continue

            # --------------------------------------------------
            # CASE 2 — FOUND → CHECK MATCHING INDICATOR
            # --------------------------------------------------
            base_row = base_candidates.iloc[0]

            raw_base = base_row[match_1]
            raw_comp = comp_row[match_2]

            base_missing = pd.isna(raw_base) or str(raw_base).strip() == ""
            comp_missing = pd.isna(raw_comp) or str(raw_comp).strip() == ""

            base_val = normalize_value(raw_base) if not base_missing else ""
            comp_val = normalize_value(raw_comp) if not comp_missing else ""

            is_mismatch = False
            reason = ""
            score = None

            if base_missing:
                is_mismatch = True
                reason = "Missing in Base File"

            elif comp_missing:
                is_mismatch = True
                reason = "Missing in Comparison File"

            else:
                if use_fuzzy:
                    score = fuzzy_score(base_val, comp_val)
                    if score < fuzzy_threshold:
                        is_mismatch = True
                        reason = "Fuzzy Mismatch"
                else:
                    if base_val != comp_val:
                        is_mismatch = True
                        reason = "Value Mismatch"

            if is_mismatch:
                mismatches.append({
                    "Common Identifier": comp_key,
                    "Base File Indicator": match_1,
                    "Base File Value": raw_base,
                    "Comparison File Indicator": match_2,
                    "Comparison File Value": raw_comp,
                    "Mismatch Reason": reason,
                    "Matching Score": score
                })


        df_mismatches = pd.DataFrame(mismatches)

    st.success("✅ Reconciliation Completed")
    st.session_state.is_running = False
    st.markdown("---")

    # -----------------------------------------------------------
    # DOWNLOAD UTILITY
    # -----------------------------------------------------------
    def to_excel(df):
        buf = BytesIO()
        df.to_excel(buf, index=False)
        return buf.getvalue()

    # -----------------------------------------------------------
    # OUTPUT TABLES (ONLY 2)
    # -----------------------------------------------------------
    # st.subheader("🔸 Common Identifier Missing in BASE File (File 1)")
    # st.dataframe(miss_common_base, use_container_width=True)
    # st.download_button(
    #     "Download",
    #     to_excel(miss_common_base),
    #     "common_id_missing_in_base.xlsx"
    # )


    # Removing duplicates from not_found_in_comparison
    unique_not_found_in_comparison = []
    for item in not_found_in_comparison:
        if item not in unique_not_found_in_comparison:
            unique_not_found_in_comparison.append(item)

    st.subheader("Common Identifier Not Found in Comparison File (File 2)")
    st.markdown(
            f"<h3 style='color:#b00020;'>❌ Total Cases: {len(unique_not_found_in_comparison)}</h3>",
            unsafe_allow_html=True
        )
    st.dataframe(pd.DataFrame(unique_not_found_in_comparison), use_container_width=True)
    st.download_button(
        "Download",
        to_excel(pd.DataFrame(unique_not_found_in_comparison)),
        "common_id_missing_in_comparison.xlsx"
    )

    # Removing duplicates from not_found_in_base
    unique_not_found_in_base = []
    for item in not_found_in_base:
        if item not in unique_not_found_in_base:
            unique_not_found_in_base.append(item)

    st.subheader("🔸Common Identifier Present in Comparison File but Missing in Base File")
    st.markdown(
            f"<h3 style='color:#b00020;'>❌ Total Cases: {len(unique_not_found_in_base)}</h3>",
            unsafe_allow_html=True
        )
    st.dataframe(pd.DataFrame(unique_not_found_in_base), use_container_width=True)
    st.download_button(
        "Download",
        to_excel(pd.DataFrame(unique_not_found_in_base)),
        "common_id_present_in_comparison_not_in_base.xlsx"
    )

    st.subheader("🔸 Matching Indicator Mismatches (Incl. Missing)")
    st.markdown(
            f"<h3 style='color:#b00020;'>❌ Total Mismatches / Breaks: {len(df_mismatches)}</h3>",
            unsafe_allow_html=True
        )
    st.dataframe(df_mismatches, use_container_width=True)
    st.download_button(
        "Download",
        to_excel(df_mismatches),
        "matching_indicator_mismatches.xlsx"
    )