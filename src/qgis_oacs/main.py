from qgis.PyQt import (
    QtCore,
    QtGui,
    QtWidgets,
)
from qgis.gui import (
    QgisInterface,
    QgsGui,
)

from .constants import IconPath
from .gui.data_source_select_provider import OacsSourceSelectProvider
from .gui.map_layer_config_widget import OacsMapLayerConfigWidgetFactory
from .gui.observations_panel import ObservationsPanel
from .gui.oacs_panel import OacsResourcePanel
from .registry import layer_registry

_PANEL_ACTION_TEXT = "OGC API Connected Systems"


class QgisOacs:
    iface: QgisInterface
    layer_properties_widget_factory: OacsMapLayerConfigWidgetFactory
    source_select_provider: OacsSourceSelectProvider
    _observations_panel: ObservationsPanel
    _resource_panel: OacsResourcePanel
    _toggle_action: QtWidgets.QAction

    def __init__(self, iface: QgisInterface) -> None:
        self.source_select_provider = OacsSourceSelectProvider()
        self.layer_properties_widget_factory = OacsMapLayerConfigWidgetFactory()
        self.iface = iface

    def initGui(self) -> None:
        QgsGui.sourceSelectProviderRegistry().addProvider(self.source_select_provider)
        self.iface.registerMapLayerConfigWidgetFactory(
            self.layer_properties_widget_factory)

        self._resource_panel = OacsResourcePanel(self.iface)
        self.iface.addDockWidget(
            QtCore.Qt.RightDockWidgetArea, self._resource_panel)

        self._observations_panel = ObservationsPanel()
        self.iface.addDockWidget(
            QtCore.Qt.BottomDockWidgetArea, self._observations_panel)
        self._observations_panel.hide()

        self._toggle_action = QtWidgets.QAction(
            QtGui.QIcon(IconPath.main_logo),
            "Toggle OACS plugin panel",
            self.iface.mainWindow(),
        )
        self._toggle_action.setToolTip("Toggle OACS plugin panel")
        self._toggle_action.setCheckable(True)
        self._toggle_action.setChecked(True)
        self._toggle_action.toggled.connect(self._resource_panel.setVisible)
        self._resource_panel.visibilityChanged.connect(self._toggle_action.setChecked)

        self.iface.addToolBarIcon(self._toggle_action)
        self.iface.addPluginToMenu(_PANEL_ACTION_TEXT, self._toggle_action)

        # Set the icon on the plugin's submenu entry in the Plugins menu.
        for menu_action in self.iface.pluginMenu().actions():
            if menu_action.text() == _PANEL_ACTION_TEXT and menu_action.menu():
                menu_action.setIcon(QtGui.QIcon(IconPath.main_logo))
                break

        layer_registry.rebuild_from_project()

    def unload(self):
        QgsGui.sourceSelectProviderRegistry().removeProvider(
            self.source_select_provider
        )
        self.iface.unregisterMapLayerConfigWidgetFactory(
            self.layer_properties_widget_factory)
        self.iface.removeToolBarIcon(self._toggle_action)
        self.iface.removePluginMenu(_PANEL_ACTION_TEXT, self._toggle_action)
        self.iface.removeDockWidget(self._resource_panel)
        self._resource_panel.deleteLater()
        self.iface.removeDockWidget(self._observations_panel)
        self._observations_panel.deleteLater()
