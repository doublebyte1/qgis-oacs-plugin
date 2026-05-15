"""Generic tree-based browser widgets for OACS resources.

Each concrete class pairs with one resource type. The shared infrastructure
lives in OacsResourceTreeWidgetBase; subclasses only implement the three
type-specific hooks: _connect_type_signals, _initiate_search, _make_resource_item.
"""

import abc
import uuid

from qgis.PyQt import (
    QtCore,
    QtGui,
    QtWidgets,
)

from ... import models, utils
from ...client import oacs_client, OacsRequestMetadata
from ...constants import IconPath, LinkRelation, OgcLinkRelation
from ...settings import settings_manager
from ..abc import AbstractQWidgetMeta

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_RESOURCE_ITEM_TYPE = 1001
_GROUP_ITEM_TYPE = 1002
_RELATED_ITEM_TYPE = 1003
_PLACEHOLDER_TYPE = 1004

_ITEM_DATA_ROLE = QtCore.Qt.UserRole
_DETAILS_FETCHED_ROLE = QtCore.Qt.UserRole + 1
_LINK_ROLE = QtCore.Qt.UserRole + 2

_LINK_REL_TO_ICON: dict[str, str] = {
    # singular resource links
    LinkRelation.system: IconPath.system_type_system,
    OgcLinkRelation.system: IconPath.system_type_system,
    LinkRelation.procedure: IconPath.procedure_type_procedure,
    OgcLinkRelation.procedure: IconPath.procedure_type_procedure,
    LinkRelation.deployment: IconPath.deployment,
    OgcLinkRelation.deployment: IconPath.deployment,
    LinkRelation.sampling_feature: IconPath.sampling_feature,
    OgcLinkRelation.sampling_feature: IconPath.sampling_feature,
    # collection / association links
    LinkRelation.implementing_systems: IconPath.system_type_system,
    OgcLinkRelation.implementing_systems: IconPath.system_type_system,
    LinkRelation.data_streams: IconPath.datastream,
    OgcLinkRelation.data_streams: IconPath.datastream,
    LinkRelation.control_streams: IconPath.datastream,
    OgcLinkRelation.control_streams: IconPath.datastream,
    LinkRelation.observations: IconPath.datastream_type_observation,
    OgcLinkRelation.observations: IconPath.datastream_type_observation,
    LinkRelation.sampling_features: IconPath.sampling_feature,
    OgcLinkRelation.sampling_features: IconPath.sampling_feature,
    LinkRelation.deployments: IconPath.deployment,
    OgcLinkRelation.deployments: IconPath.deployment,
    LinkRelation.sub_deployments: IconPath.deployment,
    OgcLinkRelation.sub_deployments: IconPath.deployment,
    LinkRelation.parent_deployment: IconPath.deployment,
    OgcLinkRelation.parent_deployment: IconPath.deployment,
    LinkRelation.deployed_systems: IconPath.system_type_system,
    OgcLinkRelation.deployed_systems: IconPath.system_type_system,
    LinkRelation.procedures: IconPath.procedure_type_procedure,
    OgcLinkRelation.procedures: IconPath.procedure_type_procedure,
    LinkRelation.sub_systems: IconPath.system_type_system,
    OgcLinkRelation.sub_systems: IconPath.system_type_system,
    LinkRelation.parent_system: IconPath.system_type_system,
    OgcLinkRelation.parent_system: IconPath.system_type_system,
    LinkRelation.sampled_feature: IconPath.sampling_feature,
    OgcLinkRelation.sampled_feature: IconPath.sampling_feature,
    LinkRelation.sample_of: IconPath.sampling_feature,
    OgcLinkRelation.sample_of: IconPath.sampling_feature,
    LinkRelation.platform: IconPath.system_type_platform,
    OgcLinkRelation.platform: IconPath.system_type_platform,
}


# ---------------------------------------------------------------------------
# Shared detail panel
# ---------------------------------------------------------------------------

class _ResourceDetailPanel(QtWidgets.QWidget):
    """Shows metadata and actions for the currently selected tree node."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_item: models.OacsItem | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._header_la = QtWidgets.QLabel("No item selected")
        self._header_la.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self._header_la.setWordWrap(True)
        layout.addWidget(self._header_la)

        self._sub_la = QtWidgets.QLabel("")
        self._sub_la.setWordWrap(True)
        self._sub_la.setStyleSheet("color: palette(dark);")
        layout.addWidget(self._sub_la)

        self._props_tw = QtWidgets.QTableWidget()
        self._props_tw.setColumnCount(2)
        self._props_tw.setHorizontalHeaderLabels(["Property", "Value"])
        self._props_tw.horizontalHeader().setStretchLastSection(True)
        self._props_tw.verticalHeader().setVisible(False)
        self._props_tw.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._props_tw.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._props_tw.setAlternatingRowColors(True)
        layout.addWidget(self._props_tw, stretch=1)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        self._load_pb = QtWidgets.QPushButton()
        self._load_pb.setEnabled(False)
        self._load_pb.clicked.connect(self._on_load_clicked)
        btn_row.addWidget(self._load_pb)
        layout.addLayout(btn_row)

    def clear(self) -> None:
        self._current_item = None
        self._header_la.setText("No item selected")
        self._sub_la.setText("")
        self._props_tw.clearContents()
        self._props_tw.setRowCount(0)
        self._load_pb.setEnabled(False)

    def show_item(self, item: models.OacsItem) -> None:
        self._current_item = item
        self._header_la.setText(item.name)
        if isinstance(item, models.OacsFeature):
            self._sub_la.setText(item.uid)
            self._fill_properties(self._properties_with_url(item))
            self._update_load_button(item.geometry)
        else:
            self._sub_la.setText(item.description or "")
            self._fill_properties(self._properties_with_url(item))
            self._load_pb.setEnabled(False)

    @staticmethod
    def _properties_with_url(item: models.OacsItem) -> dict[str, str]:
        props = item.get_renderable_properties()
        connection = settings_manager.get_current_data_source_connection()
        if connection and hasattr(type(item), "collection_path"):
            props["URL"] = item.get_detail_url(connection.base_url)
        return props

    def _update_load_button(self, geometry) -> None:
        has_geometry = bool(geometry)
        self._load_pb.setEnabled(True)
        self._load_pb.setText("Add to Map" if has_geometry else "Add as Layer")
        icon_path = (
            IconPath.feature_has_geospatial_location
            if has_geometry
            else IconPath.feature_does_not_have_geospatial_location
        )
        self._load_pb.setIcon(QtGui.QIcon(icon_path))

    def _fill_properties(self, properties: dict[str, str]) -> None:
        self._props_tw.clearContents()
        self._props_tw.setRowCount(len(properties))
        for row, (k, v) in enumerate(properties.items()):
            self._props_tw.setItem(row, 0, QtWidgets.QTableWidgetItem(str(k)))
            if k == "URL":
                link = QtWidgets.QLabel(f'<a href="{v}">{v}</a>')
                link.setOpenExternalLinks(True)
                link.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
                link.setContentsMargins(4, 2, 4, 2)
                self._props_tw.setCellWidget(row, 1, link)
            else:
                self._props_tw.setItem(row, 1, QtWidgets.QTableWidgetItem(str(v)))
        self._props_tw.resizeColumnToContents(0)
        self._props_tw.resizeRowsToContents()

    def _on_load_clicked(self) -> None:
        if self._current_item and isinstance(self._current_item, models.OacsFeature):
            utils.load_oacs_feature_as_layer(self._current_item)


# ---------------------------------------------------------------------------
# Abstract base widget
# ---------------------------------------------------------------------------

class OacsResourceTreeWidgetBase(
    QtWidgets.QWidget,
    metaclass=AbstractQWidgetMeta,
):
    """Abstract master-detail tree browser for a single OACS resource type.

    Subclasses implement three hooks:
      _connect_type_signals  — wire up the resource-specific client signals
      _initiate_search       — call the right client list-search method
      _make_resource_item    — turn an OacsItem into a top-level QTreeWidgetItem

    Optional overrides:
      _fetch_item_details    — fetch a single item's full record (default no-op)
      _build_extra_search_controls — insert extra widgets into the search bar
      _search_controls       — return the full tuple of interactive search widgets
    """

    # Subclasses set to False when the resource type never has related resources
    # (e.g. DataStream, Procedure).  Controls whether expand indicators appear.
    _items_have_relations: bool = True

    # Set to False for non-feature types (DataStream) that cannot be loaded as layers.
    _supports_load_all: bool = True

    # Used in the "No X found" placeholder and the search-bar hint.
    _resource_label: str = "items"
    _search_placeholder: str = "Search…"

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        # Dummy layout so OacsDataSourceWidget.handle_current_connection_changed
        # can call utils.clear_search_results without error.
        self.search_results_layout = QtWidgets.QVBoxLayout()

        self._current_search_id: uuid.UUID | None = None
        self._last_feature_list: models.OacsFeatureList | None = None
        self._pending_detail_requests: dict[uuid.UUID, QtWidgets.QTreeWidgetItem] = {}
        self._pending_link_requests: dict[uuid.UUID, QtWidgets.QTreeWidgetItem] = {}

        self._build_ui()
        self._connect_base_signals()
        self._connect_type_signals()

    # ------------------------------------------------------------------ hooks

    @abc.abstractmethod
    def _connect_type_signals(self) -> None:
        """Connect resource-specific client signals (list_fetched, item_fetched)."""

    @abc.abstractmethod
    def _initiate_search(self) -> None:
        """Call the appropriate client search method and store the request id."""

    @abc.abstractmethod
    def _make_resource_item(self, item: models.OacsItem) -> QtWidgets.QTreeWidgetItem:
        """Create a top-level tree item for a search result."""

    def _fetch_item_details(
            self,
            tree_item: QtWidgets.QTreeWidgetItem,
            item_id: str,
    ) -> None:
        """Fetch the full record for one item.  Override for types that support it."""

    def _fetch_related_item_details(
            self,
            tree_item: QtWidgets.QTreeWidgetItem,
            item: models.OacsItem,
    ) -> None:
        if tree_item in self._pending_detail_requests.values():
            return
        connection = settings_manager.get_current_data_source_connection()
        if not connection:
            return
        if isinstance(item, models.System):
            meta = oacs_client.initiate_system_item_fetch(item.id_, connection)
        elif isinstance(item, models.Deployment):
            meta = oacs_client.initiate_deployment_item_fetch(item.id_, connection)
        elif isinstance(item, models.SamplingFeature):
            meta = oacs_client.initiate_sampling_feature_item_fetch(item.id_, connection)
        elif isinstance(item, models.Procedure):
            meta = oacs_client.initiate_procedure_item_fetch(item.id_, connection)
        elif isinstance(item, models.DataStream):
            meta = oacs_client.initiate_datastream_item_fetch(item.id_, connection)
        else:
            return
        self._pending_detail_requests[meta.request_id] = tree_item

    def _build_extra_search_controls(
            self, bar_layout: QtWidgets.QHBoxLayout) -> None:
        """Insert extra widgets into the search bar.  Override if needed."""

    def _search_controls(self) -> tuple[QtWidgets.QWidget, ...]:
        return (self._free_text_le, self._search_pb)

    # -------------------------------------------------------------------- UI

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        search_bar = QtWidgets.QWidget()
        bar = QtWidgets.QHBoxLayout(search_bar)
        bar.setContentsMargins(8, 8, 8, 4)

        self._free_text_le = QtWidgets.QLineEdit()
        self._free_text_le.setPlaceholderText(self._search_placeholder)
        self._free_text_le.returnPressed.connect(self._run_search)
        bar.addWidget(self._free_text_le, stretch=1)

        self._build_extra_search_controls(bar)

        self._search_pb = QtWidgets.QPushButton("Search")
        self._search_pb.setIcon(utils.create_icon_from_svg(IconPath.search))
        self._search_pb.clicked.connect(self._run_search)
        bar.addWidget(self._search_pb)

        root.addWidget(search_bar)

        if self._supports_load_all:
            load_all_bar = QtWidgets.QWidget()
            load_all_layout = QtWidgets.QHBoxLayout(load_all_bar)
            load_all_layout.setContentsMargins(8, 0, 8, 4)
            load_all_layout.addStretch()
            self._load_all_pb = QtWidgets.QPushButton()
            self._load_all_pb.setVisible(False)
            self._load_all_pb.clicked.connect(self._on_load_all_clicked)
            load_all_layout.addWidget(self._load_all_pb)
            root.addWidget(load_all_bar)

        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        self._tree = QtWidgets.QTreeWidget()
        self._tree.setHeaderLabels(["Name / Resource", "Type"])
        self._tree.header().setStretchLastSection(False)
        self._tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self._tree.header().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeToContents)
        self._tree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self._tree.setUniformRowHeights(True)
        self._splitter.addWidget(self._tree)

        self._detail = _ResourceDetailPanel()
        self._splitter.addWidget(self._detail)
        self._splitter.setSizes([300, 200])

        root.addWidget(self._splitter, stretch=1)

    def _connect_base_signals(self) -> None:
        oacs_client.system_list_fetched.connect(self._on_system_list_fetched)
        oacs_client.system_item_fetched.connect(self._on_resource_item_fetched)
        oacs_client.deployment_list_fetched.connect(self._on_dep_list_fetched)
        oacs_client.deployment_item_fetched.connect(self._on_resource_item_fetched)
        oacs_client.sampling_feature_list_fetched.connect(self._on_sf_list_fetched)
        oacs_client.sampling_feature_item_fetched.connect(self._on_resource_item_fetched)
        oacs_client.procedure_list_fetched.connect(self._on_procedure_list_fetched)
        oacs_client.procedure_item_fetched.connect(self._on_resource_item_fetched)
        oacs_client.datastream_list_fetched.connect(self._on_ds_list_fetched)
        oacs_client.datastream_item_fetched.connect(self._on_resource_item_fetched)
        oacs_client.request_started.connect(self._on_request_started)
        oacs_client.request_ended.connect(self._on_request_ended)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        self._tree.itemExpanded.connect(self._on_item_expanded)
        settings_manager.current_data_source_connection_changed.connect(self._reset)

    # -------------------------------------------------- search lifecycle ---

    def _on_request_started(self, _: OacsRequestMetadata) -> None:
        utils.toggle_widgets_enabled(self._search_controls(), force_state=False)

    def _on_request_ended(self, _: OacsRequestMetadata) -> None:
        utils.toggle_widgets_enabled(self._search_controls(), force_state=True)

    def _run_search(self) -> None:
        self._reset()
        connection = settings_manager.get_current_data_source_connection()
        if connection:
            self._initiate_search()

    def _reset(self) -> None:
        self._tree.clear()
        self._detail.clear()
        self._current_search_id = None
        self._last_feature_list = None
        self._pending_detail_requests.clear()
        self._pending_link_requests.clear()
        if self._supports_load_all:
            self._load_all_pb.setVisible(False)

    # -------------------------------------------------- response handlers --

    def _on_resource_list_fetched(
            self,
            item_list,
            meta: OacsRequestMetadata,
    ) -> None:
        if meta.request_id != self._current_search_id:
            return
        items = item_list.items
        if not items:
            self._tree.addTopLevelItem(
                QtWidgets.QTreeWidgetItem(
                    [f"No {self._resource_label} found", ""]))
            return
        if self._supports_load_all:
            self._last_feature_list = item_list
            self._load_all_pb.setText(
                f"Load all {len(items)} results as layers")
            self._load_all_pb.setVisible(True)
        for item in items:
            self._tree.addTopLevelItem(self._make_resource_item(item))

    def _on_resource_item_fetched(
            self,
            item: models.OacsItem,
            meta: OacsRequestMetadata,
    ) -> None:
        tree_item = self._pending_detail_requests.pop(meta.request_id, None)
        if tree_item is None:
            return
        tree_item.setData(0, _ITEM_DATA_ROLE, item)
        tree_item.setData(0, _DETAILS_FETCHED_ROLE, True)
        while tree_item.childCount():
            tree_item.removeChild(tree_item.child(0))
        links = item.get_relevant_links()
        if links:
            for link in links:
                tree_item.addChild(self._make_group_item(link))
        else:
            tree_item.setChildIndicatorPolicy(
                QtWidgets.QTreeWidgetItem.DontShowIndicator)
        selected = self._tree.selectedItems()
        if selected and selected[0] is tree_item:
            self._detail.show_item(item)

    def _on_system_list_fetched(
            self,
            system_list: models.SystemList,
            meta: OacsRequestMetadata,
    ) -> None:
        self._populate_group(meta.request_id, system_list.items)

    def _on_dep_list_fetched(
            self,
            dep_list: models.DeploymentList,
            meta: OacsRequestMetadata,
    ) -> None:
        self._populate_group(meta.request_id, dep_list.items)

    def _on_sf_list_fetched(
            self,
            sf_list: models.SamplingFeatureList,
            meta: OacsRequestMetadata,
    ) -> None:
        self._populate_group(meta.request_id, sf_list.items)

    def _on_procedure_list_fetched(
            self,
            procedure_list: models.ProcedureList,
            meta: OacsRequestMetadata,
    ) -> None:
        self._populate_group(meta.request_id, procedure_list.items)

    def _on_ds_list_fetched(
            self,
            ds_list: models.DataStreamList,
            meta: OacsRequestMetadata,
    ) -> None:
        self._populate_group(meta.request_id, ds_list.items)

    def _populate_group(
            self,
            request_id: uuid.UUID,
            items: list[models.OacsItem],
    ) -> None:
        group_item = self._pending_link_requests.pop(request_id, None)
        if group_item is None:
            return
        group_item.setData(0, _DETAILS_FETCHED_ROLE, True)
        while group_item.childCount():
            group_item.removeChild(group_item.child(0))
        if not items:
            group_item.addChild(
                QtWidgets.QTreeWidgetItem(["(none)", ""], _PLACEHOLDER_TYPE))
            return
        for oacs_item in items:
            group_item.addChild(self._make_related_item(oacs_item))

    # ------------------------------------------------ tree item factories --

    def _make_expandable_resource_item(
            self,
            item: models.OacsItem,
            type_label: str,
            icon_path: str,
    ) -> QtWidgets.QTreeWidgetItem:
        tw_item = QtWidgets.QTreeWidgetItem(
            [item.name, type_label], _RESOURCE_ITEM_TYPE)
        tw_item.setData(0, _ITEM_DATA_ROLE, item)
        tw_item.setData(0, _DETAILS_FETCHED_ROLE, False)
        tw_item.setIcon(0, utils.create_icon_from_svg(icon_path, 16))
        if isinstance(item, models.OacsFeature):
            tw_item.setToolTip(0, item.uid)
        if self._items_have_relations:
            tw_item.setChildIndicatorPolicy(
                QtWidgets.QTreeWidgetItem.ShowIndicator)
        return tw_item

    def _make_group_item(self, link: models.Link) -> QtWidgets.QTreeWidgetItem:
        title = link.title or link.rel or "Related"
        item = QtWidgets.QTreeWidgetItem([title, ""], _GROUP_ITEM_TYPE)
        item.setData(0, _LINK_ROLE, link)
        item.setData(0, _DETAILS_FETCHED_ROLE, False)
        icon_path = _LINK_REL_TO_ICON.get(link.rel, IconPath.search)
        item.setIcon(0, utils.create_icon_from_svg(icon_path, 14))
        item.addChild(QtWidgets.QTreeWidgetItem(["…", ""], _PLACEHOLDER_TYPE))
        return item

    def _make_related_item(
            self, oacs_item: models.OacsItem) -> QtWidgets.QTreeWidgetItem:
        if isinstance(oacs_item, models.SamplingFeature):
            type_label = (
                oacs_item.feature_type.upper()
                if isinstance(oacs_item.feature_type, str)
                else (oacs_item.feature_type.value.upper()
                      if oacs_item.feature_type else "SAMPLING_FEATURE")
            )
            icon_path = IconPath.sampling_feature
        elif isinstance(oacs_item, models.DataStream):
            type_label = (
                oacs_item.datastream_type.value.upper()
                if oacs_item.datastream_type else "DATASTREAM"
            )
            icon_path = (
                oacs_item.datastream_type.get_icon_path()
                if oacs_item.datastream_type else IconPath.datastream
            )
        elif isinstance(oacs_item, models.Deployment):
            type_label = (oacs_item.feature_type or "DEPLOYMENT").upper()
            icon_path = IconPath.deployment
        elif isinstance(oacs_item, models.Procedure):
            type_label = (
                oacs_item.feature_type.value.upper()
                if oacs_item.feature_type else "PROCEDURE"
            )
            icon_path = IconPath.procedure_type_procedure
        elif isinstance(oacs_item, models.System):
            type_label = (
                oacs_item.feature_type.value.upper()
                if oacs_item.feature_type else "SYSTEM"
            )
            icon_path = (
                oacs_item.feature_type.get_icon_path()
                if oacs_item.feature_type else IconPath.system_type_system
            )
        else:
            type_label = ""
            icon_path = IconPath.system_type_system

        item = QtWidgets.QTreeWidgetItem(
            [oacs_item.name, type_label], _RELATED_ITEM_TYPE)
        item.setData(0, _ITEM_DATA_ROLE, oacs_item)
        item.setData(0, _DETAILS_FETCHED_ROLE, False)
        item.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ShowIndicator)
        item.setIcon(0, utils.create_icon_from_svg(icon_path, 14))
        if isinstance(oacs_item, models.OacsFeature):
            item.setToolTip(0, oacs_item.uid)
        return item

    # ----------------------------------------------------- tree signals ---

    def _on_item_expanded(self, item: QtWidgets.QTreeWidgetItem) -> None:
        itype = item.type()
        if itype == _RESOURCE_ITEM_TYPE:
            if not item.data(0, _DETAILS_FETCHED_ROLE):
                if item.childCount() == 0:
                    item.addChild(QtWidgets.QTreeWidgetItem(
                        ["Loading details…", ""], _PLACEHOLDER_TYPE))
                resource: models.OacsItem = item.data(0, _ITEM_DATA_ROLE)
                self._fetch_item_details(item, resource.id_)
        elif itype == _RELATED_ITEM_TYPE:
            if not item.data(0, _DETAILS_FETCHED_ROLE):
                item.addChild(QtWidgets.QTreeWidgetItem(
                    ["Loading details…", ""], _PLACEHOLDER_TYPE))
                resource: models.OacsItem = item.data(0, _ITEM_DATA_ROLE)
                self._fetch_related_item_details(item, resource)
        elif itype == _GROUP_ITEM_TYPE:
            if not item.data(0, _DETAILS_FETCHED_ROLE):
                link: models.Link = item.data(0, _LINK_ROLE)
                self._fetch_group_contents(item, link)

    def _fetch_group_contents(
            self,
            group_item: QtWidgets.QTreeWidgetItem,
            link: models.Link,
    ) -> None:
        if group_item in self._pending_link_requests.values():
            return
        connection = settings_manager.get_current_data_source_connection()
        if not connection:
            return
        meta = oacs_client.initiate_request_from_link(link, connection)
        if meta:
            self._pending_link_requests[meta.request_id] = group_item
        else:
            while group_item.childCount():
                group_item.removeChild(group_item.child(0))
            group_item.addChild(QtWidgets.QTreeWidgetItem(
                ["Not supported yet", ""], _PLACEHOLDER_TYPE))
            group_item.setData(0, _DETAILS_FETCHED_ROLE, True)

    def _on_load_all_clicked(self) -> None:
        if self._last_feature_list:
            connection = settings_manager.get_current_data_source_connection()
            prefix = (
                f"{connection.name}-{self._resource_label}"
                if connection else self._resource_label
            )
            utils.load_oacs_feature_list_as_layers(
                self._last_feature_list, name_prefix=prefix)

    def _on_selection_changed(self) -> None:
        selected = self._tree.selectedItems()
        if not selected:
            self._detail.clear()
            return
        item = selected[0]
        if item.type() in (_RESOURCE_ITEM_TYPE, _RELATED_ITEM_TYPE):
            self._detail.show_item(item.data(0, _ITEM_DATA_ROLE))
        else:
            self._detail.clear()

    # ------------------------------------------- size hint (like others) --

    def sizeHint(self) -> QtCore.QSize:
        if self.isVisible():
            return super().sizeHint()
        return QtCore.QSize(0, 0)

    def minimumSizeHint(self) -> QtCore.QSize:
        if self.isVisible():
            return super().minimumSizeHint()
        return QtCore.QSize(0, 0)


# ---------------------------------------------------------------------------
# Concrete implementations
# ---------------------------------------------------------------------------

class SearchDeploymentTreeWidget(OacsResourceTreeWidgetBase):

    _resource_label = "deployments"
    _search_placeholder = "Search deployments…"

    def _connect_type_signals(self) -> None:
        oacs_client.deployment_list_fetched.connect(self._on_resource_list_fetched)

    def _initiate_search(self) -> None:
        connection = settings_manager.get_current_data_source_connection()
        meta = oacs_client.initiate_deployment_list_search(
            connection,
            q_filter=self._free_text_le.text() or None,
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
        meta = oacs_client.initiate_deployment_item_fetch(item_id, connection)
        self._pending_detail_requests[meta.request_id] = tree_item

    def _make_resource_item(
            self, item: models.OacsItem) -> QtWidgets.QTreeWidgetItem:
        item = item  # type: models.Deployment
        type_label = (item.feature_type or "DEPLOYMENT").upper()
        return self._make_expandable_resource_item(
            item, type_label, IconPath.deployment)


class SearchSamplingFeatureTreeWidget(OacsResourceTreeWidgetBase):

    _resource_label = "sampling features"
    _search_placeholder = "Search sampling features…"

    def _connect_type_signals(self) -> None:
        oacs_client.sampling_feature_list_fetched.connect(
            self._on_resource_list_fetched)

    def _initiate_search(self) -> None:
        connection = settings_manager.get_current_data_source_connection()
        meta = oacs_client.initiate_sampling_feature_list_search(
            connection,
            q_filter=self._free_text_le.text() or None,
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
        meta = oacs_client.initiate_sampling_feature_item_fetch(item_id, connection)
        self._pending_detail_requests[meta.request_id] = tree_item

    def _make_resource_item(
            self, item: models.OacsItem) -> QtWidgets.QTreeWidgetItem:
        item = item  # type: models.SamplingFeature
        type_label = (
            item.feature_type.upper()
            if isinstance(item.feature_type, str)
            else (item.feature_type.value.upper()
                  if item.feature_type else "SAMPLING_FEATURE")
        )
        return self._make_expandable_resource_item(
            item, type_label, IconPath.sampling_feature)


class SearchProcedureTreeWidget(OacsResourceTreeWidgetBase):

    _resource_label = "procedures"
    _search_placeholder = "Search procedures…"

    def _connect_type_signals(self) -> None:
        oacs_client.procedure_list_fetched.connect(self._on_resource_list_fetched)

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
        meta = oacs_client.initiate_procedure_item_fetch(item_id, connection)
        self._pending_detail_requests[meta.request_id] = tree_item

    def _initiate_search(self) -> None:
        connection = settings_manager.get_current_data_source_connection()
        meta = oacs_client.initiate_procedure_list_search(
            connection,
            q_filter=self._free_text_le.text() or None,
        )
        self._current_search_id = meta.request_id

    def _make_resource_item(
            self, item: models.OacsItem) -> QtWidgets.QTreeWidgetItem:
        item = item  # type: models.Procedure
        type_label = (
            item.feature_type.value.upper()
            if item.feature_type else "PROCEDURE"
        )
        return self._make_expandable_resource_item(
            item, type_label, IconPath.procedure_type_procedure)


class SearchDataStreamTreeWidget(OacsResourceTreeWidgetBase):

    _supports_load_all = False
    _resource_label = "datastreams"
    _search_placeholder = "Search datastreams…"

    def _connect_type_signals(self) -> None:
        oacs_client.datastream_list_fetched.connect(self._on_resource_list_fetched)

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
        meta = oacs_client.initiate_datastream_item_fetch(item_id, connection)
        self._pending_detail_requests[meta.request_id] = tree_item

    def _initiate_search(self) -> None:
        connection = settings_manager.get_current_data_source_connection()
        meta = oacs_client.initiate_datastream_list_search(
            connection,
            q_filter=self._free_text_le.text() or None,
        )
        self._current_search_id = meta.request_id

    def _make_resource_item(
            self, item: models.OacsItem) -> QtWidgets.QTreeWidgetItem:
        item = item  # type: models.DataStream
        type_label = (
            item.datastream_type.value.upper()
            if item.datastream_type else "DATASTREAM"
        )
        icon_path = (
            item.datastream_type.get_icon_path()
            if item.datastream_type else IconPath.datastream
        )
        return self._make_expandable_resource_item(item, type_label, icon_path)
