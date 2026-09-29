"""Small UX helpers shared by the sidebar sections (select-all, counters)."""
from typing import Callable, List, Tuple

import streamlit as st


def selection_counter(label: str, items: List[Tuple[str, bool]]) -> None:
    """
    Render a one-line 'N / M selected' counter with a colored caption.

    Args:
        label: Section name to display (e.g. "Essential Applications").
        items: List of (item_id, is_selected) pairs.
    """
    total = len(items)
    selected = sum(1 for _, s in items if s)
    if total == 0:
        return
    if selected == 0:
        color = "gray"
    elif selected == total:
        color = "green"
    else:
        color = "orange"
    # NOTE: Streamlit's colored-text syntax supports named colors only -
    # hex values render literally (raw markup leak).
    st.caption(f":{color}[**{selected}** / {total} {label}]")


def _visible_count(visible: int, total: int, search_query: str) -> int:
    """Resolve how many items a select-all should affect."""
    return visible if search_query else total


def select_all_buttons(
    scope_key: str,
    items: List[Tuple[str, bool]],
    visible_ids: List[str],
    search_query: str,
    set_value: Callable[[str, bool], None],
) -> None:
    """
    Render "✓ All" / "✗ None" buttons for a section.

    The buttons operate on Streamlit widget session keys through the
    ``set_value`` callback (a widget key -> checkbox assignment), so they work
    correctly with Streamlit's rerun model. When a search is active only the
    currently *visible* (matching) items are affected.

    Args:
        scope_key: Unique prefix for the button widget keys.
        items: All (item_id, is_selected) pairs, for the counter.
        visible_ids: Ids currently visible (matched by search).
        search_query: Active search query ("" = none).
        set_value: Callback(item_id, value) that writes the widget session key.
    """
    if not items:
        return
    selection_counter("", items)

    # Two equal columns without a spacer: sidebar is narrow, a third
    # spacer column shrinks the buttons until their labels clip.
    col_all, col_none = st.columns([1, 1])
    target_ids = visible_ids if search_query else [i for i, _ in items]
    action = None
    with col_all:
        # Short labels: sidebar columns are narrow and longer text clips.
        if st.button("✓ All", key=f"{scope_key}_select_all", use_container_width=True):
            action = True
    with col_none:
        if st.button("✗ None", key=f"{scope_key}_clear_all", use_container_width=True):
            action = False
    if action is not None:
        for item_id in target_ids:
            set_value(item_id, action)
        st.rerun()
