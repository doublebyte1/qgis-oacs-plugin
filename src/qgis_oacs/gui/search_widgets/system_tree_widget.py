from qgis.PyQt import (
    QtGui,
    QtWidgets,
)

from ... import models
from ...client import oacs_client, OacsRequestMetadata
from ...constants import IconPath
from ...settings import settings_manager
from .resource_tree_widgets import OacsResourceTreeWidgetBase


class SearchSystemTreeWidget(OacsResourceTreeWidgetBase):
    """Tree-based Systems browser with type filter and relation drill-down."""

    _resource_label = "systems"
    _search_placeholder = "Search systems…"

    # --- type-specific hooks ---

    def _build_extra_search_controls(
            self, bar_layout: QtWidgets.QHBoxLayout) -> None:
        self._type_cb = QtWidgets.QComboBox()
        self._type_cb.addItem("All types", None)
        for stype in models.SystemType:
            self._type_cb.addItem(
                QtGui.QIcon(stype.get_icon_path()), stype.value.upper(), stype)
        bar_layout.addWidget(self._type_cb)

    def _search_controls(self) -> tuple[QtWidgets.QWidget, ...]:
        return (self._free_text_le, self._type_cb, self._search_pb)

    def _connect_type_signals(self) -> None:
        oacs_client.system_list_fetched.connect(self._on_resource_list_fetched)

    def _initiate_search(self) -> None:
        connection = settings_manager.get_current_data_source_connection()
        stype = self._type_cb.currentData()
        meta = oacs_client.initiate_system_list_search(
            connection,
            q_filter=self._free_text_le.text() or None,
            system_type=[stype] if stype else None,
        )
        self._current_search_id = meta.request_id

    def _fetch_item_details(
            self,
            tree_item: QtWidgets.QTreeWidgetItem,
            item_id: str,
    ) -> None:
        if tree_item in self._pending_detail_requests.values():
            return
        connection = settings_manager.get_current_data_source_connection()
        if not connection:
            return
        meta = oacs_client.initiate_system_item_fetch(item_id, connection)
        self._pending_detail_requests[meta.request_id] = tree_item

    def _make_resource_item(
            self, item: models.OacsItem) -> QtWidgets.QTreeWidgetItem:
        item = item  # type: models.System
        type_label = (
            item.feature_type.value.upper() if item.feature_type else "SYSTEM"
        )
        icon_path = (
            item.feature_type.get_icon_path()
            if item.feature_type else IconPath.system_type_system
        )
        return self._make_expandable_resource_item(item, type_label, icon_path)
