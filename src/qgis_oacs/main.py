from qgis.gui import (
    QgisInterface,
    QgsGui,
)

from .gui.data_source_select_provider import OacsSourceSelectProvider
from .gui.map_layer_config_widget import OacsMapLayerConfigWidgetFactory


class QgisOacs:
    iface: QgisInterface
    layer_properties_widget_factory: OacsMapLayerConfigWidgetFactory
    source_select_provider: OacsSourceSelectProvider

    def __init__(self, iface: QgisInterface) -> None:
        self.source_select_provider = OacsSourceSelectProvider()
        self.layer_properties_widget_factory = OacsMapLayerConfigWidgetFactory()
        self.iface = iface

    def initGui(self) -> None:
        QgsGui.sourceSelectProviderRegistry().addProvider(self.source_select_provider)
        self.iface.registerMapLayerConfigWidgetFactory(
            self.layer_properties_widget_factory)

    def unload(self):
        QgsGui.sourceSelectProviderRegistry().removeProvider(
            self.source_select_provider
        )
        self.iface.unregisterMapLayerConfigWidgetFactory(
            self.layer_properties_widget_factory)
