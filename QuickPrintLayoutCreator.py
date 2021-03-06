# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QuickPrintLayoutCreator
								 A QGIS plugin
 This plugin transforms multiple layers into muliple layouts, based on a template. Then, you can export your creation.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
							  -------------------
		begin				: 2019-12-26
		git sha			  : $Format:%H$
		copyright		\t: (C) 2019 by Martin Bocquet
		email				: martin.bocquet@gmail.com
 ***************************************************************************/

/***************************************************************************
 *																		 *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or	 *
 *   (at your option) any later version.								   *
 *																		 *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .QuickPrintLayoutCreator_dialog import QuickPrintLayoutCreatorDialog
import os.path

from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo, QDir, QUrl, QTimer, Qt, QObject
from qgis.PyQt.QtWidgets import QAction, QListWidgetItem, QFileDialog, QDialogButtonBox, QMenu, QMessageBox, QApplication, QLineEdit
from qgis.PyQt.QtGui import QIcon, QCursor, QDesktopServices, QImageWriter, QBrush
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget
import string
import random
import re
from qgis.gui import QgsMessageBar
from collections import Counter

class QuickPrintLayoutCreator:


	#Functions created by plugin builder
	"""QGIS Plugin Implementation."""
	def __init__(self, iface):
		"""Constructor.

		:param iface: An interface instance that will be passed to this class
			which provides the hook by which you can manipulate the QGIS
			application at run time.
		:type iface: QgsInterface
		"""
		# Save reference to the QGIS interface
		self.iface = iface
		# initialize plugin directory
		self.plugin_dir = os.path.dirname(__file__)
		# initialize locale
		locale = QSettings().value('locale/userLocale')[0:2]
		locale_path = os.path.join(
			self.plugin_dir,
			'i18n',
			'QuickPrintLayoutCreator_{}.qm'.format(locale))

		if os.path.exists(locale_path):
			self.translator = QTranslator()
			self.translator.load(locale_path)
			QCoreApplication.installTranslator(self.translator)

		# Declare instance attributes
		self.actions = []
		self.menu = self.tr(u'&Quick Print Layout Creator and Exporter')

		# Check if plugin was started the first time in current QGIS session
		# Must be set in initGui() to survive plugin reloads
		self.first_start = None
		
		# init the layout manager
		self.layoutManager = QgsProject.instance().layoutManager()
		self.dlg = QuickPrintLayoutCreatorDialog()

	# noinspection PyMethodMayBeStatic
	def tr(self, message):
		"""Get the translation for a string using Qt translation API.

		We implement this ourselves since we do not inherit QObject.

		:param message: String for translation.
		:type message: str, QString

		:returns: Translated version of message.
		:rtype: QString
		"""
		# noinspection PyTypeChecker,PyArgumentList,PyCallByClass
		return QCoreApplication.translate('QuickPrintLayoutCreator', message)


	def add_action(
		self,
		icon_path,
		text,
		callback,
		enabled_flag=True,
		add_to_menu=True,
		add_to_toolbar=True,
		status_tip=None,
		whats_this=None,
		parent=None):
		icon = QIcon(icon_path)
		action = QAction(icon, text, parent)
		action.triggered.connect(callback)
		action.setEnabled(enabled_flag)

		if status_tip is not None:
			action.setStatusTip(status_tip)

		if whats_this is not None:
			action.setWhatsThis(whats_this)

		if add_to_toolbar:
			# Adds plugin icon to Plugins toolbar
			self.iface.addToolBarIcon(action)

		if add_to_menu:
			self.iface.addPluginToMenu(
				self.menu,
				action)

		self.actions.append(action)

		return action
		
	def unload(self):
		"""Removes the plugin menu item and icon from QGIS GUI."""
		for action in self.actions:
			self.iface.removePluginMenu(
				self.tr(u'&Quick Print Layout Creator and Exporter'),
				action)
			self.iface.removeToolBarIcon(action)

	def initGui(self):	
		"""Create the menu entries and toolbar icons inside the QGIS GUI."""
		icon_path = ':/plugins/QuickPrintLayoutCreator/img/icon.png'
		self.add_action(
			icon_path,
			text=self.tr(u'Quick Print Layout Creator and Exporter'),
			callback=self.run,
			parent=self.iface.mainWindow())

		# will be set False in run()
		self.first_start = True

	#Custom functions
	
	#UI fonctions
	def startUI(self):

		if self.first_start == True:
		# Connect to the export button to do the real work
			self.dlg.exportButton = self.dlg.buttonBox.button(QDialogButtonBox.Ok)		
			self.dlg.exportButton.disconnect()			
			self.dlg.exportButton.setText(self.tr(u'Export'))
			self.dlg.exportButton.clicked.connect(self.doIt)
		else:
			# clear the 3 lists
			self.dlg.checkAll.setChecked(False)
			self.dlg.listLayer.clear()
			self.dlg.listLayout.clear()
			self.dlg.supportedFormatsBox.clear()
		
		self.dlg.checkAll.clicked.connect(self.checkAll)
		self.dlg.browse.setStorageMode(QgsFileWidget.StorageMode.GetDirectory)
		
		#init the list of layers
			#old method who doesn't keep the order
			#lay = QgsProject.instance().mapLayers()
			#layers = list(lay.values())
		layers = QgsProject.instance().layerTreeRoot().layerOrder()

		self.listLayersId = [] #a initialiser correctement
		
		for layer in layers:
			#init the list of layersID
			self.listLayersId.append(layer.id())
			
			#create the list of layers in UI, and add a checkbox
			item = QListWidgetItem()
			item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
			item.setCheckState(Qt.Unchecked)
			item.setText(layer.name())
			
			self.dlg.listLayer.addItem(item)
			item2 = QListWidgetItem()
			item2.setFlags(item2.flags() | Qt.ItemIsEditable)
			item2.setFlags(item2.flags() ^ QtCore.Qt.ItemIsUserCheckable)
			#if self.first_start == True:
			item2.setText('Double click to set/change the title')
			item2.setForeground(QBrush(QtCore.Qt.darkGray))
			self.dlg.listLayer.addItem(item2)
			item2.setHidden(True)		
			
		self.dlg.listLayer.clicked.connect(self.layerCheckedEvent)
			
		# init the list of layouts and insert them in UI
		layouts = QgsProject.instance().layoutManager().printLayouts()
		layoutsName = []
		for layout in layouts:
			layoutsName.append(layout.name())
		self.dlg.listLayout.addItems(layoutsName)
		
		#init the list of supported formats
		self.dlg.supportedFormatsBox.addItems(self.getSupportedFormats())
		#set a the default directory on PDF. Put a signal to open browser in last saved PDF, SVG ou image
		self.defaultDirectory = QSettings().value('/UI/lastSaveAsPdfFile')
		self.defaultDirectory = self.dlg.supportedFormatsBox.currentIndexChanged.connect(self.selectDefaultDirectory)
		self.first_start = False
		
	def prepareProgressBar(self, number):
		self.dlg.progressBar.setValue(0)
		self.dlg.progressBar.setMaximum(number)
		
	def checkAll(self):
	#check or uncheck all layers if the "checkAll" button is pressed
		isChecked = self.dlg.checkAll.checkState()
		for rowList in range(0, self.dlg.listLayer.count()):
			item = self.dlg.listLayer.item(rowList)
			if ((item.flags() & Qt.ItemIsUserCheckable) == Qt.ItemIsUserCheckable):
				item.setCheckState(isChecked)		
							
	def selectDefaultDirectory(self):
		#define defaut directory
		if self.dlg.supportedFormatsBox.currentIndex() == 0 :
			#PDF
			directory = QSettings().value('/UI/lastSaveAsPdfFile')
		elif self.dlg.supportedFormatsBox.currentIndex() == 1:
			#SVG		
			directory = QSettings().value('/UI/lastSaveAsSvgFile')
		else:
			#image
			directory = QSettings().value('/UI/lastSaveAsImageDir')
		return directory
	
		
	def getSupportedFormats(self):
		#return supported formats to put into UI
		listFormats = ['PDF (*.pdf)', 'SVG (*.svg)']
		imageformats = QImageWriter.supportedImageFormats()
		for f in imageformats:
			fs = f.data().decode('utf-8')
			listFormats.append('{} (*.{})'.format(fs.upper(), fs))
		return listFormats

		


	
	#Export functions	
	def doIt(self):
		#control the entries and make the exports or generate an error
		
		#get the list of layer selected names
		layerNames, layerIds, layerTitles = self.getCheckedLayers()
		#get the name of the selected layout
		layoutName = self.getSelectedLayout()
		if (layerNames != None and layerIds != None and layoutName != None and layerNames != [] and layoutName != []):
			if	self.dlg.override.checkState():
				for layerName in layerNames:
					self.deleteLayouts(layoutName+'_QuickExport'+'_'+layerName)
			if	self.dlg.exportLayouts.checkState():
				if self.checkDirectory(self.dlg.browse.filePath()):
					self.createNewLayouts(layerNames,layerIds, layoutName, self.getExtensionName(self.dlg.supportedFormatsBox.currentText()), self.dlg.browse.filePath(), layerTitles)
					self.dlg.close()
					QMessageBox.warning(None, self.tr(u'Operation completed'), self.tr(u"Files were exported in "+self.dlg.browse.filePath()),QMessageBox.Ok, QMessageBox.Ok)
				else :
					QMessageBox.warning(None, self.tr(u'Unable to write in folder or inexistant folder'), self.tr(u"The folder doesn't exist or you don't have rights to write in this folder. Please, select another one!"), QMessageBox.Ok, QMessageBox.Ok)
					self.run()
			else:
				self.createNewLayouts(layerNames,layerIds,layoutName, layerTitles = layerTitles)
				QMessageBox.warning(None, self.tr(u'Operation completed'), self.tr(u"New layouts were created"),QMessageBox.Ok, QMessageBox.Ok)
				self.dlg.close()
		elif (layerNames == [] or layerNames == None):
			QMessageBox.warning(None, self.tr(u'Please select a layer'), self.tr(u"No layer selected. Please, select at least one layer!"),QMessageBox.Ok, QMessageBox.Ok)
			self.run()
		elif (layoutName == None or layoutName == []):
			QMessageBox.warning(None, self.tr(u'Please select a layout'), self.tr(u"No layout selected. Please, select at least one layout!"),QMessageBox.Ok, QMessageBox.Ok)
			self.run()
	
	def createNewLayouts(self, layerNames,layerIds, layoutName, exportExtension = None, folder = None, layerTitles = None):
		#do the real job : create layouts and export if necessary
		layoutBase = self.layoutManager.layoutByName(layoutName)		
		self.prepareProgressBar(len(layerNames))
		
		for i, (layerName, layerId, title) in enumerate(zip(layerNames, layerIds, layerTitles)):
			#generate a new name
			newLayoutName = self.getNewLayoutName(layoutName+'_QuickExport'+'_'+layerName)
			self.layoutManager.duplicateLayout(layoutBase,newLayoutName)
			currentLayout = self.layoutManager.layoutByName(newLayoutName)
			
			#set the map
			currentLayer = QgsProject.instance().mapLayer(layerId)
			currentLayout.referenceMap().setLayers([currentLayer])		 #setLayers take a list, and mapLayer(id) return a single layer
			#center the new map as the main canvas
			currentLayout.referenceMap().zoomToExtent(self.iface.mapCanvas().extent())
			
			#set the legend
			for item in currentLayout.items():
				if isinstance(item, QgsLayoutItemLegend):
					legend = item
			legend.setLinkedMap(currentLayout.referenceMap())
			legend.setLegendFilterByMapEnabled(True)
			
			# set the title
			if (title != 'Double click to set/change the title' and title != ''):
				title2 = None
				title1 = None
				for item in currentLayout.items():
					if isinstance(item, QgsLayoutItemLabel):
						title1 = item
						if (item.currentText().lower() == 'title'):
							title2 = item
							
				if (title2 != None):
					title2.setText(title)
				else:
					if (title1 != None):
						title1.setText(title)
			
			if (folder != None and exportExtension != None):
				title = layerName
				exportSettings = self.overrideExportSetings(currentLayout, exportExtension)
			
				if exportExtension == None:
					pass
				elif exportExtension == '.pdf':
					result = QgsLayoutExporter(currentLayout).exportToPdf(os.path.join(folder, title + '.pdf'), exportSettings)
				elif exportExtension == '.svg':
					result = QgsLayoutExporter(currentLayout).exportToSvg(os.path.join(folder, title + '.svg'), exportSettings)
				else:
					result = QgsLayoutExporter(currentLayout).exportToImage(os.path.join(folder, title + exportExtension), exportSettings)

			if not self.dlg.keepLayouts.checkState():
				self.layoutManager.removeLayout(currentLayout)

			self.dlg.progressBar.setValue(i+1)
			
	def getNewLayoutName(self, new_name):
		layouts = self.layoutManager.printLayouts()
		layoutsNames = []
		for layout in layouts:
			layoutsNames.append(layout.name())
		while new_name in layoutsNames:
			#add 1 to version
			new_name += 'a'
		return new_name
		
	def overrideExportSetings(self, layout, extension):
		"""Because GUI settings are not exposed in Python, we need to find and catch user selection
		   See discussion at http://osgeo-org.1560.x6.nabble.com/Programmatically-export-layout-with-georeferenced-file-td5365462.html"""
		#code from maps_printer plugin credits to Harrissou Sant-anna (CAUE 49)
		if extension == '.pdf':
			exportSettings = QgsLayoutExporter.PdfExportSettings()
			if layout.customProperty('dpi') and layout.customProperty('dpi') != -1 : exportSettings.dpi = layout.customProperty('dpi')
			if layout.customProperty('forceVector') == True : exportSettings.forceVectorOutput = True
			if layout.customProperty('rasterize') == True : exportSettings.rasterizeWholeImage = True
		elif extension == '.svg':
			exportSettings = QgsLayoutExporter.SvgExportSettings()
			if layout.customProperty('dpi') and layout.customProperty('dpi') != -1 : exportSettings.dpi = layout.customProperty('dpi')
			if layout.customProperty('forceVector') == True : exportSettings.forceVectorOutput = True
			if layout.customProperty('svgIncludeMetadata') == True : exportSettings.exportMetadata = True
			if layout.customProperty('svgGroupLayers') == True : exportSettings.exportAsLayers = True
		else:
			exportSettings = QgsLayoutExporter.ImageExportSettings()
			if layout.customProperty('exportWorldFile') == True : exportSettings.generateWorldFile = True
			if layout.customProperty('') == True : exportSettings.exportMetadata = True
			if layout.customProperty('dpi') and layout.customProperty('dpi') != -1 : exportSettings.dpi = layout.customProperty('dpi')
			# if layout.customProperty('atlasRasterFormat') == True : exportSettings.xxxx = True
			# if layout.customProperty('imageAntialias') == True : exportSettings.xxxx = True

		return exportSettings		


	def layerCheckedEvent(self):
		#when a layer is checked, open a box to enter the title
		for num in range(0, self.dlg.listLayer.count()):
			item = self.dlg.listLayer.item(num)
			if ((item.flags() & Qt.ItemIsUserCheckable) == Qt.ItemIsUserCheckable):
				item2 = self.dlg.listLayer.item(num+1)
				#open / close the title box
				if item.checkState()== Qt.Checked:
					item2.setHidden(False)
				else:
					item2.setHidden(True)	
				#change color of the box
				if item2.text() == 'Double click to set/change the title':
					item2.setForeground(QBrush(QtCore.Qt.darkGray))
				else:
					item2.setForeground(QBrush(QtCore.Qt.black))
		
	def getExtensionName(self, text):
		#get extension name from the UI name list
		return('.'+re.sub('[^A-Z]', '', text).lower())
		
	def deleteLayouts(self, layoutName):
		layouts = self.layoutManager.printLayouts()
		for layout in layouts:
			if layout.name().startswith(layoutName):
				self.layoutManager.removeLayout(layout)
	
	def checkDirectory(self, path):
		return os.path.isdir(path) and os.access(path, os.W_OK)
		
	def getCheckedLayers(self):
		layerNames = [ self.dlg.listLayer.item(num).text() for num in range(0, self.dlg.listLayer.count()) if self.dlg.listLayer.item(num).checkState() == Qt.Checked]
		layerIds = [ self.listLayersId[int(num/2)] for num in range(0, self.dlg.listLayer.count()) if self.dlg.listLayer.item(num).checkState() == Qt.Checked]
		layerTitles = [ self.dlg.listLayer.item(num+1).text() for num in range(0, self.dlg.listLayer.count()) if self.dlg.listLayer.item(num).checkState() == Qt.Checked]
		layerNames = self.rectifyLayerNames(layerNames)
		return layerNames, layerIds, layerTitles


	def rectifyLayerNames(self, layerNames):
		#check if 2 layers have the same name and return a list without duplicates
		counts = {k:v for k,v in Counter(layerNames).items() if v > 1}
		for i in reversed(range(len(layerNames))):
			item = layerNames[i]
			if item in counts and counts[item]:
				layerNames[i] += str(counts[item])
				counts[item]-=1
		return(layerNames)
		
				
	#main function	
	def run(self):
		"""Run method that performs all the real work"""
		# Create the dialog with elements (after translation) and keep reference
		# Only create GUI ONCE in callback, so that it will only load when the plugin is started
		self.startUI()
		# show the dialog
		self.dlg.show()
		# Run the dialog event loop
		if len(self.layoutManager.printLayouts()) == 0:
			self.iface.messageBar().pushMessage(self.tr(u'There is currently no print layout in the project. '\
			'Please create at least one layout before running this plugin.'),level = Qgis.Warning)
			self.dlg.close()
		if not self.dlg.isVisible():
			self.dlg.show()
		else:
			self.dlg.activateWindow()