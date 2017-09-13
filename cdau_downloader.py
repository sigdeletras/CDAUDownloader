# -*- coding: utf-8 -*-

"""
/***************************************************************************
 CDAUDownloader
                                 A QGIS plugin
 Descarga
                              -------------------
        begin                : 2017-08-26
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Patricio Soriano :: SIGdeletras.com
        email                : pasoriano@sigdeletras.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import urllib.request
import zipfile
import urllib
from urllib import request , parse
import sys

# Import the PyQt and QGIS libraries
from qgis.PyQt.QtCore import Qt
# from PyQt5 import QtCore, QtGui, QtWidgets
import os

# from PyQt5.QtWidgets import QDialog

try:
    from qgis.core import Qgis
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5 import uic

    QT_VERSION = 5
    os.environ['QT_API'] = 'pyqt5'
except:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from PyQt4 import uic
    from qgis.core import QgsMapLayerRegistry

    QT_VERSION = 4

import os.path
from qgis.core import *

# import resources
from .resources import *

# from Spanish_Inspire_Catastral_Downloader_dialog import Spanish_Inspire_Catastral_DownloaderDialog
from .cdau_downloader_dialog import CDAUDownloaderDialog
from .listamuni import *
from qgis.core import QgsProject
from qgis.gui import QgsMessageBar

platform = sys.platform

listProvincias = LISTPROV
listMunicipios = LISTMUNI

codprov = ''
codmuni = ''


class CDAUDownloader:
    """QGIS Plugin Implementation."""

    def __init__(self , iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.msgBar = iface.messageBar()
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir ,
            'i18n' ,
            'CDAUDownloader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&CDAU Downloader')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'CDAUDownloader')
        self.toolbar.setObjectName(u'CDAUDownloader')

    # noinspection PyMethodMayBeStatic
    def tr(self , message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CDAUDownloader' , message)

    def add_action(
            self ,
            icon_path ,
            text ,
            callback ,
            enabled_flag=True ,
            add_to_menu=True ,
            add_to_toolbar=True ,
            status_tip=None ,
            whats_this=None ,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = CDAUDownloaderDialog()
        self.dlg.setWindowFlags(Qt.WindowSystemMenuHint | Qt.WindowTitleHint)

        icon = QIcon(icon_path)
        action = QAction(icon , text , parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu ,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/CDAUDownloader/icon.png'
        self.add_action(
            icon_path ,
            text=self.tr(u'CDAU Downloader') ,
            callback=self.run ,
            parent=self.iface.mainWindow())

        self.dlg.pushButton_select_path.clicked.connect(self.select_output_folder)
        self.dlg.pushButton_run.clicked.connect(self.download)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&CDAU Downloader') ,
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def select_output_folder(self):
        """Select output folder"""

        self.dlg.lineEdit_path.clear()
        folder = QFileDialog.getExistingDirectory(self.dlg , "Select folder")
        self.dlg.lineEdit_path.setText(folder)

    def not_data(self):
        """Message for fields without information"""
        self.msgBar.pushMessage('Completar datos de municipio o indicar la ruta de descarga' ,
                                level=QgsMessageBar.INFO , duration=3)

    def filter_municipality(self , index):
        """Message for fields without information"""

        filtroprovincia = self.dlg.comboBox_province.currentText()
        self.dlg.comboBox_municipality.clear()

        self.dlg.comboBox_municipality.addItems([muni for muni in listMunicipios if muni[0:2] == filtroprovincia[0:2]])

        ine_municipio = self.dlg.comboBox_municipality.currentText()

        codprov = ine_municipio[0:2]
        codmuni = ine_municipio[0:5]

    # Progress Download
    def reporthook(self , blocknum , blocksize , totalsize):
        readsofar = blocknum * blocksize
        if totalsize > 0:
            percent = readsofar * 1e2 / totalsize
            self.dlg.progressBar.setValue(int(percent))

    # Encode URL Download
    def EncodeUrl(self , url):
        url = parse.urlsplit(url)
        url = list(url)
        url[2] = parse.quote(url[2])
        encoded_link = parse.urlunsplit(url)
        return encoded_link

    def download(self):
        """Dowload data funtion"""

        if self.dlg.comboBox_municipality.currentText() == '' or self.dlg.lineEdit_path.text() == '':

            self.not_data()

        else:

            try:

                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                ine_municipio = self.dlg.comboBox_municipality.currentText()
                codprov = ine_municipio[0:2]
                codmuni = ine_municipio[0:5]
                zippath = self.dlg.lineEdit_path.text()

                wd = os.path.join(zippath , ine_municipio)

                geojson_file = "cdau_%s_vial.geojson" % (ine_municipio)
                cdau_geojson = os.path.join(wd , geojson_file)

                # pass

                # download Vial
                if self.dlg.checkBox_vial.isChecked():

                    url = u'http://www.callejerodeandalucia.es/servicios/cdau/wfs?srsname=EPSG:4258&typename=cdau:v_vial&version=1.0.0&request=GetFeature&service=WFS&PROPERTYNAME=*&cql_filter=ine_mun=\'%s\'&outputformat=application/json' % (
                        codmuni)
                    # descagar Vial

                    try:
                        os.makedirs(wd)
                    except OSError:
                        pass

                    geojson_file = "%s_cdau_vial.geojson" % (ine_municipio)
                    cdau_geojson = os.path.join(wd , geojson_file)

                    # urllib.request.urlretrieve(url.encode('utf-8') , cdau_geojson)
                    # urllib.request.urlretrieve(url, cdau_geojson)

                    e_url = self.EncodeUrl(url)
                    try:
                        urllib.request.urlretrieve(e_url , cdau_geojson , self.reporthook)
                    except:
                        shutil.rmtree(wd)
                        raise

                # download Tramos
                if self.dlg.checkBox_tramos.isChecked():

                    url = u'http://www.callejerodeandalucia.es/servicios/cdau/wfs?srsname=EPSG:4258&typename=cdau:v_tramo&version=1.0.0&request=GetFeature&service=WFS&PROPERTYNAME=*&cql_filter=ine_mun=\'%s\'&outputformat=application/json' % (
                        codmuni)
                    # descagar Vial

                    try:
                        os.makedirs(wd)
                    except OSError:
                        pass

                    geojson_file = "%s_cdau_tramo.geojson" % (ine_municipio)
                    cdau_geojson = os.path.join(wd , geojson_file)

                    # urllib.request.urlretrieve(url.encode('utf-8') , cdau_geojson)
                    # urllib.request.urlretrieve(url, cdau_geojson)

                    e_url = self.EncodeUrl(url)
                    try:
                        urllib.request.urlretrieve(e_url , cdau_geojson , self.reporthook)
                    except:
                        shutil.rmtree(wd)
                        raise

                # download potalpk
                if self.dlg.checkBox_portalpk.isChecked():

                    url = u'http://www.callejerodeandalucia.es/servicios/cdau/wfs?srsname=EPSG:4258&typename=cdau:v_portalpk&version=1.0.0&request=GetFeature&service=WFS&PROPERTYNAME=*&cql_filter=ine_mun=\'%s\'&outputformat=application/json' % (
                        codmuni)
                    # descagar Vial

                    try:
                        os.makedirs(wd)
                    except OSError:
                        pass

                    geojson_file = "%s_cdau_portalpk.geojson" % (ine_municipio)
                    cdau_geojson = os.path.join(wd , geojson_file)

                    # urllib.request.urlretrieve(url.encode('utf-8') , cdau_geojson)
                    # urllib.request.urlretrieve(url, cdau_geojson)

                    e_url = self.EncodeUrl(url)
                    try:
                        urllib.request.urlretrieve(e_url , cdau_geojson , self.reporthook)
                    except:
                        shutil.rmtree(wd)
                        raise

                # self.msgBar.pushMessage("Ok!" , level=QgsMessageBar.SUCCESS, duration=3)
                self.dlg.progressBar.setValue(100)  # No llega al 100% aunque lo descargue,es random
                QApplication.restoreOverrideCursor()
                # Carga en proyecto si se marca la opcion

                if self.dlg.checkBox_vial.isChecked() or self.dlg.checkBox_tramos.isChecked() or self.dlg.checkBox_portalpk.isChecked():

                    # self.msgBar.pushMessage("Start loading GeoJSON files..." , level=QgsMessageBar.INFO)

                    # loading geojson

                    for geojsonfile in os.listdir(wd):
                        if geojsonfile.endswith('.geojson'):
                            layer = self.iface.addVectorLayer(os.path.join(wd , geojsonfile) , "" ,
                                                              "ogr")
                else:
                    self.msgBar.pushMessage("Seleccione al menos una capa para descargar." , level=QgsMessageBar.INFO ,
                                            duration=3)

                if self.dlg.checkBox_styles.isChecked():
                    if QT_VERSION == 5:
                        if platform == 'win32':
                            layerPortalpk = QgsProject.instance().mapLayersByName('%s_cdau_portalpk' % (ine_municipio))[
                                0]
                            layerVial = QgsProject.instance().mapLayersByName('%s_cdau_vial' % (ine_municipio))[0]
                        else:
                            layerPortalpk = QgsProject.instance().mapLayersByName(
                                '%s_cdau_portalpk OGRGeoJSON Point' % (ine_municipio))[0]
                            layerVial = QgsProject.instance().mapLayersByName(
                                '%s_cdau_vial OGRGeoJSON MultiLineString' % (ine_municipio))[0]

                    else:

                        if platform == 'win32':
                            layerPortalpk = \
                                QgsMapLayerRegistry.instance().mapLayersByName('%s_cdau_portalpk' % (ine_municipio))[0]
                            layerVial = \
                                QgsMapLayerRegistry.instance().mapLayersByName('%s_cdau_vial' % (ine_municipio))[0]

                        else:
                            layerPortalpk = QgsMapLayerRegistry.instance().mapLayersByName(
                                '%s_cdau_portalpk OGRGeoJSON Point' % (ine_municipio))[0]
                            layerVial = QgsMapLayerRegistry.instance().mapLayersByName(
                                '%s_cdau_vial OGRGeoJSON MultiLineString' % (ine_municipio))[0]

                    qmlPortalpk_path = os.path.dirname(__file__) + "/qml/portalpk.qml"
                    layerPortalpk.loadNamedStyle(qmlPortalpk_path)
                    layerPortalpk.triggerRepaint()

                    qmlVial_path = os.path.dirname(__file__) + "/qml/vial.qml"
                    layerVial.loadNamedStyle(qmlVial_path)
                    layerVial.triggerRepaint()

                QApplication.restoreOverrideCursor()

            except Exception as e:
                QApplication.restoreOverrideCursor()
                self.msgBar.pushMessage("Failed! " + str(e) , level=QgsMessageBar.WARNING , duration=3)
                return

    def run(self):
        """Run method that performs all the real work"""

        self.dlg.lineEdit_path.clear()

        self.dlg.comboBox_province.clear()
        self.dlg.comboBox_municipality.clear()
        self.dlg.comboBox_province.addItems(listProvincias)
        self.dlg.comboBox_province.currentIndexChanged.connect(self.filter_municipality)

        self.dlg.checkBox_vial.setChecked(0)
        self.dlg.checkBox_tramos.setChecked(0)
        self.dlg.checkBox_portalpk.setChecked(0)
        self.dlg.checkBox_styles.setChecked(0)

        # show the dialog
        self.dlg.progressBar.setValue(0)
        self.dlg.setWindowIcon(QIcon(':/plugins/CDAUDownloader/icon.png'));

        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:
            pass
