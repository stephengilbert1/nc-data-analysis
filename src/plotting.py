# src/plotting.py
import os
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# --- palette ---
ACCENT  = "#D97757"   # terracotta - the series/category the headline is about
NEUTRAL = "#4A4A4A"   # charcoal - supporting series
CONTEXT = "#B0AEA9"   # warm grey - background context, usually with opacity
GRID    = "#E5E3E0"   # light warm grey - horizontal gridlines
MUTED   = "#7A7772"   # mid grey - source lines, secondary text
GREY_RAMP = ["#6E6B66", "#8A8782", "#A8A5A0", "#C6C3BE"]  # dark→light, for de-emphasised categories
GREY_RAMP_LONG = ["#5C5955", "#767370", "#908D89", "#AAA7A3", "#C4C1BD", "#DEDBD7"]

# --- theme (registered on import) ---
pio.templates["custom_theme"] = go.layout.Template(pio.templates["plotly_white"])
tpl = pio.templates["custom_theme"].layout          # alias to cut the repetition

# Canvas
tpl.width = 1400
tpl.height = 600
tpl.plot_bgcolor = "white"
tpl.paper_bgcolor = "white"
tpl.margin = dict(t=90, b=70, l=70, r=40)

# Type
tpl.font.family = "Helvetica, Arial, sans-serif"
tpl.font.color = "#2B2B2B"
tpl.font.size = 13
tpl.title.font.size = 20

# Editorial title placement (left-aligned, Economist-style)
tpl.title.x = 0
tpl.title.xanchor = "left"
tpl.title.y = 0.95

# Horizontal gridlines only
tpl.yaxis.gridcolor = GRID
tpl.yaxis.zeroline = False
tpl.yaxis.showline = False
tpl.xaxis.showgrid = False
tpl.xaxis.showline = True
tpl.xaxis.linecolor = GRID
tpl.xaxis.tickangle = 0

tpl.colorway = [ACCENT, NEUTRAL, CONTEXT, "#8C6A56", "#5A6B6D",
                "#C9A87C", "#7A8471", "#9B6B6B", "#6B7A99", "#2B2B2B"]

pio.templates.default = "custom_theme"

# Consistent colors for problem flags
pflag_colors = {
    "Unintended Activation": ACCENT,
    "Other": NEUTRAL,
    "Leaking": CONTEXT,
    "Energized Activation": "#8C6A56",
    "Did not Activate": "#5A6B6D",
}

pio.templates.default = "custom_theme"

def plot_rc_over_time(rc_table, root_cause, quarter_order, color=NEUTRAL):
    subset = rc_table[rc_table["Root Cause"] == root_cause]
    fig = px.bar(
        subset, x="Quarter", y="Count",
        category_orders={"Quarter": quarter_order},
        title=f"{root_cause} NCs by Quarter",
    )
    fig.update_traces(marker_color=color)
    fig.update_layout(xaxis_title="", yaxis_title="Number of NCs Opened")
    return fig

def export_charts(charts_dict, folder="../outputs/figures", scale=2):
    os.makedirs(folder, exist_ok=True)
    for name, figure in charts_dict.items():
        figure.write_image(f"{folder}/{name}.png", scale=scale)

def add_source(fig, text, y=-0.12):
    """Add a small grey source note bottom-left, Economist-style."""
    fig.add_annotation(
        text=text, xref="paper", yref="paper", x=0, y=y,
        showarrow=False, xanchor="left",
        font=dict(size=11, color=MUTED),
    )
    return fig

def emphasis_colors(categories, emphasis, accent=ACCENT, ramp=GREY_RAMP):
    """
    Colour list aligned to `categories`: `emphasis` gets `accent`,
    everything else steps through `ramp` in order.
    """
    colors, i = [], 0
    for cat in categories:
        if cat == emphasis:
            colors.append(accent)
        else:
            colors.append(ramp[i % len(ramp)])
            i += 1
    return colors

def build_emphasis_map(categories, emphasis, accent=ACCENT, ramp=GREY_RAMP):
    """
    {category: colour} map — `emphasis` gets `accent`, the rest step through
    `ramp` in order. Keyed by category so colours stay consistent across charts
    regardless of each chart's row order.
    """
    color_map, i = {}, 0
    for cat in categories:
        if cat == emphasis:
            color_map[cat] = accent
        else:
            color_map[cat] = ramp[i % len(ramp)]
            i += 1
    return color_map

def ranked_bar(counts, label_col, emphasis, title, value_col="Count"):
    """
    Horizontal ranked bar, house style: largest at top, emphasised category in
    ACCENT with the rest greyed, direct value labels, no value axis.
    """
    color_map = build_emphasis_map(counts[label_col], emphasis)
    order = counts.sort_values(value_col, ascending=False)[label_col].tolist()

    fig = px.bar(
        counts, x=value_col, y=label_col, orientation="h",
        text=value_col,
        color=label_col, color_discrete_map=color_map,
        category_orders={label_col: order},
        title=title,
    )
    fig.update_traces(textposition="outside")
    fig.update_xaxes(showticklabels=False, showgrid=False, title="")
    fig.update_layout(showlegend=False)
    return fig