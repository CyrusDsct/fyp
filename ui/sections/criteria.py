import streamlit as st

def _as_str(x, default="unknown"):
    if x is None:
        return default
    if isinstance(x, (dict, list)):
        try:
            return st.json.dumps(x, ensure_ascii=False)
        except Exception:
            return str(x)
    s = str(x).strip()
    return s if s else default

def _get_obj(d: dict, key: str):
    if not isinstance(d, dict):
        return None
    v = d.get(key)
    return v if isinstance(v, dict) else None

def build_criteria_items(analysis_json: dict):
    #Returns: (items, item_by_id)
    extract = _get_obj(analysis_json, "extract") or {}

    # backward-compat: if no extract, try to treat top-level keys as items
    if not extract:
        skip = {"explanation", "map_quality", "recommendations", "status", "analysis"}
        extract = {}
        for k, v in (analysis_json or {}).items():
            if k in skip:
                continue
            extract[k] = v

    # Human label map (by leaf key name)
    LEAF_LABELS = {
        # map
        "map_title": "Map title",
        "citations": "Citations",
        "bgcolour": "Background colour",
        "url": "URL",
        # legend
        "has_legend": "Legend present",
        "orientation": "Legend orientation",
        "continguity": "Contiguity",
        "contiguity": "Contiguity",
        "range": "Range",
        "num_bins": "Number of bins",
        "frequency": "Frequency shown",
        "no_data": "No data category",
        "explicit_other": "Explicit 'Other' category",
        "incomplete_info": "Incomplete info",
        "data_type": "Data type",
        "semantic_type": "Semantic type",
        "color_scheme": "Colour scheme",
        "colour_scheme": "Colour scheme",
        "colours": "Colours",
        "colors": "Colours",
        "colour_semantics": "Colour semantics",
        "legend_placement": "Legend placement",
        "placement": "Legend placement",
        "border": "Legend border",
        # data
        "data_distribution": "Data distribution",
        "classification": "Classification method",
        # high level
        "colourblind_friendly": "Colourblind friendliness",
        "print_friendly": "Print friendliness",
    }

    PATH_LABELS = {
        "legend.border": "Legend border",
        "legend.color_scheme": "Colour scheme",
        "legend.colour_scheme": "Colour scheme",
        "map.bgcolour": "Background colour",
        "map.map_title": "Map title",
        "map.citations": "Citations",
        "data.classification": "Classification method",
    }

    GROUP_LABELS = {
        "map": "Map",
        "legend": "Legend",
        "data": "Data",
        "high_level": "High-level",
    }

    def is_item_dict(d):
        return isinstance(d, dict) and any(k in d for k in ("value", "quality", "explanation", "fixes"))

    def to_title_from_key(k: str) -> str:

        k = (k or "").replace("_", " ").strip()
        return k[:1].upper() + k[1:] if k else "Unknown"

    def label_for(path: str) -> str:
        # path like "legend.num_bins"
        if not path:
            return "Unknown"

        base = path.split("[", 1)[0]

        if base in PATH_LABELS:
            return PATH_LABELS[base]

        leaf = base.split(".")[-1]
        if leaf in LEAF_LABELS:
            return LEAF_LABELS[leaf]

        return to_title_from_key(leaf)

    def group_for(path: str) -> str:
        if not path:
            return "Other"
        head = path.split(".", 1)[0].split("[", 1)[0]
        return GROUP_LABELS.get(head, "Other")

    items = []
    item_by_id = {}

    def walk(obj, path=""):
        if is_item_dict(obj):
            item_id = path or "unknown"
            item = {
                "id": item_id,
                "group": group_for(item_id),
                "label": label_for(item_id),  # human-readable label
                "value": _as_str(obj.get("value")),
                "quality": _as_str(obj.get("quality"), "neutral").lower().strip(),
                "explanation": _as_str(obj.get("explanation")),
                "fixes": _as_str(obj.get("fixes"), "none"),
                "raw": obj,
            }
            items.append(item)
            item_by_id[item_id] = item
            return

        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else str(k)
                walk(v, new_path)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                new_path = f"{path}[{i}]"
                walk(v, new_path)
        else:
            return

    walk(extract, "")
    # TODO: to be discussed
    group_order = {"Map": 0, "Legend": 1, "Data": 2, "High-level": 3, "Other": 9}
    items.sort(key=lambda x: (group_order.get(x["group"], 9), x["label"].lower(), x["id"].lower()))
    return items, item_by_id


def render_criteria(analysis_json: dict, items: list):
    st.subheader("Criteria")

    if not items:
        st.info("No criteria items found in JSON under `extract`.")
        st.json(analysis_json)
        return

    good = bad = neutral = 0
    for it in items:
        q = (it.get("quality") or "neutral").lower().strip()
        if q == "good":
            good += 1
        elif q == "bad":
            bad += 1
        else:
            neutral += 1

    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Good", good)
    c2.metric("❌ Bad", bad)
    c3.metric("⚪ Neutral", neutral)

    # st.caption(f"Total criteria: {len(items)}")

    # Filters
    qualities = ["all", "good", "neutral", "bad"]
    sel_q = st.radio("Filter (quality)", qualities, horizontal=True, index=0, key="criteria_filter")

    groups = ["all"] + sorted({it.get("group", "Other") for it in items})
    sel_g = st.selectbox("Filter (group)", groups, index=0, key="criteria_group_filter")

    shown = 0
    for it in items:
        q = (it.get("quality") or "neutral").lower().strip()
        g = it.get("group", "Other")

        if sel_q != "all" and q != sel_q:
            continue
        if sel_g != "all" and g != sel_g:
            continue

        shown += 1

        icon = "✅" if q == "good" else ("❌" if q == "bad" else "⚪")
        title = f"{icon} [{g}] {it.get('label','Unknown')} — {q.upper()}"

        with st.expander(title, expanded=False):
            st.markdown(f"**Value:** {it.get('value','')}")
            st.markdown(f"**Explanation:** {it.get('explanation','')}")
            fixes = it.get("fixes", "none")
            if fixes and str(fixes).strip().lower() != "none":
                st.markdown(f"**Fixes:** {fixes}")

            # debug only
            # st.caption(f"Path: `{it.get('id','')}`")
    # debug
    # st.caption(f"Showing {shown} item(s) for filters: quality=`{sel_q}`, group=`{sel_g}`")
    