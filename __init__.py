# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CDAUDownloader
                                 A QGIS plugin
 Descarga
                             -------------------
        begin                : 2017-08-26
        copyright            : (C) 2017 by Patricio Soriano :: SIGdeletras.com
        email                : pasoriano@sigdeletras.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
from .resources import *

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load CDAUDownloader class from file CDAUDownloader.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .cdau_downloader import CDAUDownloader
    return CDAUDownloader(iface)
