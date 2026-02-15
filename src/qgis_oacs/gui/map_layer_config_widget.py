from pathlib import Path

import qgis.core
import qgis.gui
from qgis.PyQt import (
    QtGui,
    QtWidgets,
)
from qgis.PyQt.uic import loadUiType

from ..constants import IconPath

MapLayerConfigWidgetUi, _ = loadUiType(
    Path(__file__).parents[1] / "ui/map_layer_config_widget.ui")


class OacsMapLayerConfigWidget(
    qgis.gui.QgsMapLayerConfigWidget,
    MapLayerConfigWidgetUi
):

    def __init__(
            self,
            layer: qgis.core.QgsMapLayer | None,
            canvas: qgis.gui.QgsMapCanvas | None,
            parent: QtWidgets.QWidget | None = None
    ):
        super().__init__(layer, canvas, parent)
        self.setupUi(self)


class OacsMapLayerConfigWidgetFactory(qgis.gui.QgsMapLayerConfigWidgetFactory):

    def __init__(self) -> None:
        super().__init__(
            "OGC API - Connected Systems",
            QtGui.QIcon(IconPath.main_logo)
        )

    def supportsLayer(self, layer):
        return True

    def supportLayerPropertiesDialog(self):
        return True

    def createWidget(
            self,
            layer: qgis.core.QgsMapLayer | None,
            canvas: qgis.gui.QgsMapCanvas | None,
            dock_widget: bool = True,
            parent: QtWidgets.QWidget | None = None,
    ) -> qgis.gui.QgsMapLayerConfigWidget | None:
        return OacsMapLayerConfigWidget(layer, canvas, parent)