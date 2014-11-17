# -*- coding: utf-8 -*-
"""
/***************************************************************************
 reseaux
                                 A QGIS plugin
 Créer
                              -------------------
        begin                : 2014-09-09
        copyright            : (C) 2014 by CEREMA Nord-Picardie
        email                : patrick.palmier@cerema.fr
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from reseauxdialog import reseauxDialog
from reseauxdialog_connect import reseauxDialog_connect
import os.path


class reseaux:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', 'networks_{}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = reseauxDialog()
        self.dlg_connect=reseauxDialog_connect()
        

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/reseaux/icon.png"),
            QCoreApplication.translate(u"Creer graphe",u"Creer graphe"), self.iface.mainWindow())
        # connect the action to the run method
        self.action_reverse = QAction(
            QIcon(":/plugins/reseaux/icon.png"),
            QCoreApplication.translate(u"Inverser",u"Inverser"), self.iface.mainWindow())
            
        self.action_segmenter=QAction(
            QIcon(":/plugins/reseaux/icon.png"),
            QCoreApplication.translate(u"Segmenter",u"Segmenter"), self.iface.mainWindow())

        self.action_connect=QAction(
            QIcon(":/plugins/reseaux/icon.png"),
            QCoreApplication.translate(u"Connecter",u"Connecter") ,self.iface.mainWindow())

        
        self.action.triggered.connect(self.run)
        self.action_reverse.triggered.connect(self.run_inverser)
        self.action_segmenter.triggered.connect(self.run_segmenter)
        self.action_connect.triggered.connect(self.run_connect)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(QCoreApplication.translate(u"&Reseaux",u"&Reseaux"), self.action)
        self.iface.addPluginToMenu(QCoreApplication.translate(u"&Reseaux",u"&Reseaux"), self.action_reverse)
        self.iface.addPluginToMenu(QCoreApplication.translate(u"&Reseaux",u"&Reseaux"), self.action_segmenter)
        self.iface.addPluginToMenu(QCoreApplication.translate(u"&Reseaux",u"&Reseaux"), self.action_connect)
        

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu(QCoreApplication.translate(u"&Reseaux",u"&Reseaux"), self.action)
        self.iface.removePluginMenu(QCoreApplication.translate(u"&Reseaux",u"&Reseaux"),self.action_reverse)
        self.iface.removePluginMenu(QCoreApplication.translate(u"&Reseaux",u"&Reseaux"),self.action_segmenter)
        self.iface.removePluginMenu(QCoreApplication.translate(u"&Reseaux",u"&Reseaux"),self.action_connect)
        
    # run method that performs all the real work
    def run(self):
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            self.creer_graphe(self.dlg.lineEdit.text(),self.dlg.checkBox.isChecked())

    def creer_graphe(self,prefixe,afficher):
        layer=self.iface.activeLayer()
        nom_champs=[]
        for i in layer.dataProvider().fields():
            nom_champs.append(i.name())
        if ("i" not in nom_champs):
            layer.dataProvider().addAttributes([QgsField("i",QVariant.String)])
        if ("j" not in nom_champs):
            layer.dataProvider().addAttributes([QgsField("j",QVariant.String)])
        layer.updateFields()
        layer.commitChanges()
        ida=layer.fieldNameIndex("i")
        idb=layer.fieldNameIndex("j")
        lines=layer.getFeatures()
        noeuds={}
        nom_fichier=QFileDialog.getSaveFileName(caption=QCoreApplication.translate("Enregister fichier noeuds","Enregister fichier noeuds"),directory=os.getcwd(),filter="ESRI Shape File (*.shp)")
        champs=QgsFields()
        champs.append(QgsField("numero",QVariant.String))
        table_noeuds=QgsVectorFileWriter(nom_fichier,"UTF-8",champs,QGis.WKBPoint,layer.crs(),"ESRI Shapefile")
        for ligne in lines:
            gligne=ligne.geometry()
            if gligne.wkbType()==QGis.WKBMultiLineString:
                g=gligne.asMultiPolyline()
                na=g[0][0]
                nb=g[-1][-1]
            elif gligne.wkbType()==QGis.WKBLineString:
                g=gligne.asPolyline()
                na=g[0]
                nb=g[-1]
            if (na not in noeuds):
                noeuds[na]=prefixe+str(len(noeuds)+1)
            if (nb not in noeuds):
                noeuds[nb]=prefixe+str(len(noeuds)+1)
        
        #outs=open("c:/temp/noeuds.txt","w")
        for i,n in enumerate(noeuds):
            node=QgsFeature()
            node.setGeometry(QgsGeometry.fromPoint(QgsPoint(n[0],n[1])))
            #node.setAttributes([noeuds[n]])
            node.setAttributes([str(noeuds[n])])
            table_noeuds.addFeature(node)
        #outs.write(str(n)+";"+str(noeuds[n])+"\n")
        del table_noeuds
        #outs.close()
        lines=layer.getFeatures()
        layer.startEditing()
        layer.beginEditCommand(QCoreApplication.translate("creation du graphe","creation du graphe"))
        for ligne in lines:
            gligne=ligne.geometry()
            if gligne.wkbType()==QGis.WKBMultiLineString:
                g=gligne.asMultiPolyline()
                na=g[0][0]
                nb=g[-1][-1]
            elif gligne.wkbType()==QGis.WKBLineString:
                g=gligne.asPolyline()
                na=g[0]
                nb=g[-1]
            id=ligne.id()
            #valid={ida : noeuds[na], idb: noeuds[nb]}
            layer.changeAttributeValue(id,ida, noeuds[na])
            layer.changeAttributeValue(id,idb, noeuds[nb])
        layer.endEditCommand()
        #layer.commitChanges()
        if afficher:
            nom_couche=os.path.splitext(os.path.basename(nom_fichier))[0]
            vlayer=QgsVectorLayer(nom_fichier,nom_couche,'ogr')
            QgsMapLayerRegistry.instance().addMapLayer(vlayer)
            
    def run_inverser(self):
        layer = self.iface.activeLayer()
        if not layer==None:
            if layer.selectedFeatureCount()>0 and layer.geometryType()==1:
                layer.startEditing()
                layer.beginEditCommand(QCoreApplication.translate("Inversion du sens des lignes","Inversion du sens des lignes"))
                for feature in layer.selectedFeatures():
            
                    geom = feature.geometry()
                    geom.convertToMultiType()
                    nodes = geom.asMultiPolyline()
                    for points in nodes:
                        points.reverse() 
                    newgeom = QgsGeometry.fromMultiPolyline(nodes)
                    layer.changeGeometry(feature.id(),newgeom)
                layer.endEditCommand()
            elif not layer.geometryType()==1:
                QMessageBox().information(None,QCoreApplication.translate("Inverser","Inverser"),QCoreApplication.translate("La couche n est pas composee de lignes","La couche n est pas composee de lignes"))
            else:
                QMessageBox().information(None,QCoreApplication.translate("Inverser","Inverser"),QCoreApplication.translate("selection vide","selection vide"))
        else:
            QMessageBox().information(None,QCoreApplication.translate("Inverser","Inverser"),QCoreApplication.translate("Aucune couche active","Aucune couche active"))
        #layer.commitChanges()
    
    def run_segmenter(self):
        layer = self.iface.activeLayer()
        if not layer==None:
            if layer.selectedFeatureCount()>0 and layer.geometryType()==1:
                layer.startEditing()
                layer.beginEditCommand(QCoreApplication.translate("segmenter les polylignes en lignes simples","segmenter les polylignes en lignes simples"))
                for feature in layer.selectedFeatures():
                    geom = feature.geometry()
                    nodes = geom.convertToType(QGis.Line,True).asMultiPolyline()
                    att=feature.attributes()
                    id=feature.id()
                    for poly in nodes:
                        for pt in range(len(poly)-1):
                            segment=QgsFeature()
                            segment.setGeometry(QgsGeometry.fromPolyline([poly[pt],poly[pt+1]]))
                            segment.setAttributes(att)
                            layer.addFeature(segment)
                    layer.deleteFeature(id)
                layer.endEditCommand()
            elif not layer.geometryType()==1:
                QMessageBox().information(None,QCoreApplication.translate("Segmenter","Segmenter"),QCoreApplication.translate("La couche n est pas composee de lignes","La couche n est pas composee de lignes"))
            else:
                QMessageBox().information(None,QCoreApplication.translate("Segmenter","Segmenter"),QCoreApplication.translate("selection vide","selection vide"))
        else:
            QMessageBox().information(None,QCoreApplication.translate("Segmenter","Segmenter"),QCoreApplication.translate("Aucune couche active","Aucune couche active"))

        
    def run_connect(self):
        # show the dialog
        self.dlg_connect.comboBox.clear()
        for i in self.iface.mapCanvas().layers():
            self.dlg_connect.comboBox.addItem(i.name())
        self.dlg_connect.show()
        # Run the dialog event loop
        result = self.dlg_connect.exec_()
        # See if OK was pressed
        if result == 1:
            self.connect(self.dlg_connect.comboBox.currentText(),self.dlg_connect.lineEdit.text())
        
        
    def connect(self,point_layer,radius):
        delta=float(radius)
        lines=self.iface.activeLayer()
        if not lines==None:
            if lines.geometryType()==1:
                couches=self.iface.mapCanvas().layers()
                index=QgsSpatialIndex()
                for i in lines.getFeatures():
                    if i.geometry().isMultipart():
                        i.setGeometry(QgsGeometry.fromPolyline(i.geometry().asMultiPolyline()[0]))
                    index.insertFeature(i)
                couche_points=QgsMapLayerRegistry.instance().mapLayersByName(point_layer)[0]
                if couche_points.geometryType()==0:
                    points=couche_points.getFeatures()
                    lines.startEditing()
                    lines.beginEditCommand(QCoreApplication.translate("Scinder les polylignes à l'endroit de la connexion","Scinder les polylignes à l'endroit de la connexion"))
                    nb=couche_points.featureCount()
                    for pos,pt in enumerate(points):
                        ptg=pt.geometry()
                        if ptg.isMultipart():
                            ptg=QgsGeometry.fromPoint(ptg.asMultiPoint()[0])
                        coor=ptg.asPoint()
                        nearest=index.intersects(QgsRectangle(coor.x()-delta,coor.y()-delta,coor.x()+delta,coor.y()+delta))
                        dmin=1e38
                        if len(nearest)>0:
                            for n in nearest:
                                f=lines.getFeatures(request=QgsFeatureRequest(n))
                                for g in f:
                                    d=g.geometry().distance(pt.geometry())
                                    if d<=dmin:
                                        dmin=d
                                        gmin=g
                            g=gmin
                            if g.geometry().distance(pt.geometry())<delta:
                                a=g.geometry().closestSegmentWithContext(ptg.asPoint())
                                if not(a[2]==0):
                                    geom=g.geometry()
                                    geom_id=g.id()
                                    att=g.attributes()
                                    connexion=QgsFeature()
                                    connexion.setGeometry(QgsGeometry.fromPolyline([ptg.asPoint(),a[1]]))
                                    connexion.setAttributes(att)
                                    lines.addFeature(connexion)
                                    geom.insertVertex(a[1][0],a[1][1],a[2])
                                    geoma=geom.asPolyline()[:a[2]+1]
                                    geomb=geom.asPolyline()[a[2]:]
                                    fa=QgsFeature()
                                    fa.setGeometry(QgsGeometry.fromPolyline(geoma))
                                    fa.setAttributes(att)
                                    lines.addFeature(fa)
                                    index.insertFeature(fa)
                                    fb=QgsFeature()
                                    fb.setGeometry(QgsGeometry.fromPolyline(geomb))
                                    fb.setAttributes(att)
                                    lines.addFeature(fb)
                                    index.insertFeature(fb)
                                    lines.deleteFeature(g.id())
                                    index.deleteFeature(g)
                    lines.endEditCommand()
                else:
                    QMessageBox().information(None,QCoreApplication.translate("Connecter","Connecter"),QCoreApplication.translate("La couche selectionnee n est pas composee de points","La couche selectionnee n est pas composee de points"))
            else:
                QMessageBox().information(None,QCoreApplication.translate("Connecter","Connecter"),QCoreApplication.translate("La couche active n est pas composee de lignes","La couche active n est pas composee de lignes"))
        else:
            QMessageBox().information(None,QCoreApplication.translate("Connecter","Connecter"),QCoreApplication.translate("Aucune couche active","Aucune couche active"))
        
        
