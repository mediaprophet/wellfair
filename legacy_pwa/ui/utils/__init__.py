from .styling import (
    CLINICAL_HIGHLIGHT_PATTERNS,
    HEALTH_COLORS,
    highlight_turtle_clinical,
    inject_css,
)
from .data_access import cached_load, cached_transform, load_dataset_mappings, get_all_structured_assessments
from .analytics import extract_timeline_events, get_dashboard_metrics
from .plotting import plot_dataset_chart
from .selectors import find_df_by_datatype, find_df_by_keyword
from .mock_data import init_mock_data
from .navigation import render_sidebar_nav, get_nav_items, get_current_section, set_current_section
from .components import (
    render_premium_card,
    render_kpi_row,
    render_section_header,
    render_info_banner,
    render_simple_metric_card,
    render_alert_card,
)

from src.persistence import (
    save_vault_data,
    load_vault_data,
    save_questionnaires,
    load_questionnaires,
    save_pathology_reports,
    load_pathology_reports,
    auto_save_structured_data,
    auto_load_structured_data,
)

from src.version import __version__, VERSION_INFO

__all__ = [
    "HEALTH_COLORS",
    "CLINICAL_HIGHLIGHT_PATTERNS",
    "inject_css",
    "highlight_turtle_clinical",
    "cached_load",
    "cached_transform",
    "load_dataset_mappings",
    "get_all_structured_assessments",
    "get_dashboard_metrics",
    "extract_timeline_events",
    "plot_dataset_chart",
    "find_df_by_keyword",
    "find_df_by_datatype",
    "init_mock_data",
    "render_sidebar_nav",
    "get_nav_items",
    "get_current_section",
    "set_current_section",
    "render_premium_card",
    "render_kpi_row",
    "render_section_header",
    "render_info_banner",
    "render_simple_metric_card",
    "render_alert_card",
    "save_vault_data",
    "load_vault_data",
    "save_questionnaires",
    "load_questionnaires",
    "save_pathology_reports",
    "load_pathology_reports",
    "auto_save_structured_data",
    "auto_load_structured_data",
    "__version__",
    "VERSION_INFO",
]