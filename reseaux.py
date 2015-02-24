# -*- coding: utf-8 -*-
"""
/***************************************************************************
 reseaux
                                 A QGIS plugin
 CrÃ©er
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
from qgis.utils import *
import numpy
import math
import time

# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from reseauxdialog import reseauxDialog
from reseauxdialog_connect import reseauxDialog_connect
from linear_interpolation_dialog_connect import reseauxDialog_interpol
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
        self.dlg_interpol=reseauxDialog_interpol()
        self.largeur=0.0
        self.hauteur=0.0
        self.nx=0
        self.ny=0
        self.deltax=0.0
        self.deltay=0.0
        self.pixel_size_x=0.0
        self.pixel_size_y=0.0
        self.rep=self.plugin_dir
        

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/reseaux/icon.png"),
            QCoreApplication.translate(u"Build graph",u"Build graph"), self.iface.mainWindow())
        # connect the action to the run method
        self.action_reverse = QAction(
            QIcon(":/plugins/reseaux/icon.png"),
            QCoreApplication.translate(u"Reverse",u"Reverse"), self.iface.mainWindow())
            
        self.action_segmenter=QAction(
            QIcon(":/plugins/reseaux/icon.png"),
            QCoreApplication.translate(u"Split",u"Split"), self.iface.mainWindow())

        self.action_connect=QAction(
            QIcon(":/plugins/reseaux/icon.png"),
            QCoreApplication.translate(u"Connect",u"Connect") ,self.iface.mainWindow())

        self.action_interpol=QAction(
            QIcon(":/plugins/reseaux/icon.png"),
            QCoreApplication.translate(u"Linear interpolation",u"Linear interpolation") ,self.iface.mainWindow())
        
        self.action_help=QAction(
            QIcon(":/plugins/reseaux/icon.png"),
            QCoreApplication.translate(u"Help",u"Help") ,self.iface.mainWindow())
        
        self.action.triggered.connect(self.run)
        self.action_reverse.triggered.connect(self.run_inverser)
        self.action_segmenter.triggered.connect(self.run_segmenter)
        self.action_connect.triggered.connect(self.run_connect)
        self.action_interpol.triggered.connect(self.run_interpol)
        self.action_help.triggered.connect(self.run_help)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"), self.action)
        self.iface.addPluginToVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"), self.action_reverse)
        self.iface.addPluginToVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"), self.action_segmenter)
        self.iface.addPluginToVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"), self.action_connect)
        self.iface.addPluginToVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"), self.action_interpol)
        self.iface.addPluginToVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"), self.action_help)
        
        
        QObject.connect(self.dlg_interpol.lineEdit, SIGNAL("textEdited(QString)"), self.maj_taille_x)
        QObject.connect(self.dlg_interpol.lineEdit_2, SIGNAL("textEdited(QString)"), self.maj_taille_y)
        QObject.connect(self.dlg_interpol.lineEdit_3, SIGNAL("textEdited(QString)"), self.maj_nb_x)
        QObject.connect(self.dlg_interpol.lineEdit_4, SIGNAL("textEdited(QString)"), self.maj_nb_y)
        
        QObject.connect(self.dlg_interpol.pushButton,SIGNAL("clicked()"),self.parcourir)
        
    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"), self.action)
        self.iface.removePluginVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"),self.action_reverse)
        self.iface.removePluginVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"),self.action_segmenter)
        self.iface.removePluginVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"),self.action_connect)
        self.iface.removePluginVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"),self.action_interpol)
        self.iface.removePluginVectorMenu(QCoreApplication.translate(u"&Networks",u"&Networks"),self.action_help)
        
    # run method that performs all the real work
    def run(self):
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            self.creer_graphe(self.dlg.lineEdit.text(),self.dlg.checkBox.isChecked())
            
    def parcourir(self):
        self.dlg_interpol.lineEdit_8.setText(QFileDialog.getSaveFileName(caption=QCoreApplication.translate("Save raster layer as","Save raster layer as"),directory=self.rep,filter="ArcInfo ASCII grid (*.asc)"))
        
    def run_help(self):
        #showPluginHelp(self.plugin_dir+"index.html")
        showPluginHelp()
    
    def maj_taille_x(self,ncells_x):
        if not (ncells_x==""):
            if float(ncells_x)>0:
                self.dlg_interpol.lineEdit_3.setText(str(round(self.largeur/float(ncells_x),2)))
                self.pixel_size_x=float(self.dlg_interpol.lineEdit_3.text())
        
    def maj_taille_y(self,ncells_y):
        if not (ncells_y==""):
            if float(ncells_y)>0:
                self.dlg_interpol.lineEdit_4.setText(str(round(self.hauteur/float(ncells_y),2)))
                self.pixel_size_y=float(self.dlg_interpol.lineEdit_4.text())
    
    def maj_nb_x(self,deltax):
        if not (self.nx==""):
            if float(deltax)>0:
                self.dlg_interpol.lineEdit.setText(str(round(self.largeur/float(deltax),0)))
                self.nx=float(self.dlg_interpol.lineEdit.text())
        
    def maj_nb_y(self,deltay):
        if not (self.ny==""):
            if float(deltay)>0:
                self.dlg_interpol.lineEdit_2.setText(str(round(self.hauteur/float(deltay),0)))
                self.ny=float(self.dlg_interpol.lineEdit_2.text())
        
    
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
        nom_fichier=QFileDialog.getSaveFileName(caption=QCoreApplication.translate("Save node layer as","Save nodes layer as"),directory=os.getcwd(),filter="ESRI Shape File (*.shp)")
        champs=QgsFields()
        champs.append(QgsField("Id",QVariant.String))
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
        layer.beginEditCommand(QCoreApplication.translate("Building graph","Building graph"))
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
                layer.beginEditCommand(QCoreApplication.translate("Reverse polyline directions","Reverse polyline directions"))
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
                QMessageBox().information(None,QCoreApplication.translate("Reverse","Reverse"),QCoreApplication.translate("The active layer isn't composed of linear objects","The active layer isn't composed of linear objects"))
            else:
                QMessageBox().information(None,QCoreApplication.translate("Reverse","Reverse"),QCoreApplication.translate("Empty selection","Empty selection"))
        else:
            QMessageBox().information(None,QCoreApplication.translate("Reverse","Reverse"),QCoreApplication.translate("No active layer","No active layer"))
        #layer.commitChanges()
    
    def run_segmenter(self):
        layer = self.iface.activeLayer()
        if not layer==None:
            if layer.selectedFeatureCount()>0 and layer.geometryType()==1:
                layer.startEditing()
                layer.beginEditCommand(QCoreApplication.translate("Split polylines into lines","Split polylines into lines"))
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
                QMessageBox().information(None,QCoreApplication.translate("Split","Split"),QCoreApplication.translate("The layer isn't composed of linear objects","The layer isn't composed of linear objects"))
            else:
                QMessageBox().information(None,QCoreApplication.translate("Split","Split"),QCoreApplication.translate("Empty selection","Empty selection"))
        else:
            QMessageBox().information(None,QCoreApplication.translate("Split","Split"),QCoreApplication.translate("No active layer","No active layer"))

        
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
        
    def run_interpol(self):
        layer = self.iface.activeLayer()
        if layer!=None:

            if layer.type()==QgsMapLayer.VectorLayer:

                self.fenetre=self.iface.mapCanvas().extent()

                a=self.fenetre.toString().split(":")
                p1=a[0].split(',')
                p2=a[1].split(',')


                self.ll=(float(p1[0]),float(p1[1]))
                self.hauteur=float(p2[1])-float(p1[1])
                self.largeur=float(p2[0])-float(p1[0])
                self.nx=int(self.dlg_interpol.lineEdit.text())
                self.ny=int(self.dlg_interpol.lineEdit_2.text())
                self.dlg_interpol.lineEdit_3.setText(str(round(self.largeur/self.nx,2)))
                self.dlg_interpol.lineEdit_4.setText(str(round(self.hauteur/self.ny,2)))
                self.pixel_size_x=float(self.dlg_interpol.lineEdit_3.text())
                self.pixel_size_y=float(self.dlg_interpol.lineEdit_4.text()) 
                
                for i in layer.dataProvider().fields():
                    self.dlg_interpol.comboBox.addItem(i.name())
                    self.dlg_interpol.comboBox_2.addItem(i.name())
                    self.dlg_interpol.comboBox_3.addItem(i.name())
                    self.dlg_interpol.comboBox_4.addItem(i.name())
                    self.dlg_interpol.comboBox_5.addItem(i.name())
                    self.dlg_interpol.comboBox_6.addItem(i.name())
                    self.dlg_interpol.comboBox_7.addItem(i.name())
                    self.dlg_interpol.comboBox_8.addItem(i.name())
                self.dlg_interpol.show()

                result = self.dlg_interpol.exec_()
                # See if OK was pressed
                if result == 1:
                    self.rasterfile=self.dlg_interpol.lineEdit_8.text()
                    self.AB_i=self.dlg_interpol.comboBox.currentText()
                    self.AB_j=self.dlg_interpol.comboBox_2.currentText()
                    self.BA_i=self.dlg_interpol.comboBox_7.currentText()
                    self.BA_j=self.dlg_interpol.comboBox_8.currentText()
                    self.flow_direction=self.dlg_interpol.comboBox_3.currentText()
                    self.diffusion_direction=self.dlg_interpol.comboBox_4.currentText()
                    self.impassibility=self.dlg_interpol.comboBox_5.currentText()
                    self.diffusion_speed=self.dlg_interpol.comboBox_6.currentText()
                    self.decimals=int(self.dlg_interpol.lineEdit_7.text())
                    self.radius=float(self.dlg_interpol.lineEdit_5.text())
                    self.default_speed=float(self.dlg_interpol.lineEdit_6.text())
                    self.flag_variable_speed=self.dlg_interpol.checkBox_3.isChecked()
                    self.flag_impassibility=self.dlg_interpol.checkBox.isChecked()
                    self.flag_add_layer=self.dlg_interpol.checkBox_2.isChecked()
                    if self.rasterfile!="":
                        self.calcul_interpol()
            else:
                QMessageBox().information(None,QCoreApplication.translate("Linear interpolation","Linear interpolation"),QCoreApplication.translate("The active layer isn't composed of linear objects","The active layer isn't composed of linear objects"))
        else:
            QMessageBox().information(None,QCoreApplication.translate("Linear interpolation","Linear interpolation"),QCoreApplication.translate("No active layer","No active layer"))
            
            
            
    def calcul_interpol(self):

        grille=numpy.array([[-9999.0]*self.ny]*self.nx)
        grille_distance=numpy.array([[1e38]*self.ny]*self.nx)
        self.rep=os.path.dirname(self.rasterfile)
        layer=self.iface.activeLayer()
        if layer.type()==QgsMapLayer.VectorLayer:
            if not layer==None:
                if layer.geometryType()==1:
                    simple=QgsSimplifyMethod()
                    simple.setMethodType(QgsSimplifyMethod.PreserveTopology)
                    simple.setTolerance(min(self.pixel_size_x,self.pixel_size_y)/2)
                    texte='"'+self.diffusion_direction+'" in (\'1\',\'2\',\'3\') and (("'+self.AB_j+'" IS NOT NULL and "'+self.flow_direction+'" in (\'1\',\'2\')) or ("'+self.BA_j+'" IS NOT NULL and "'+self.flow_direction+'" in (\'2\',\'3\')))'
                    request=(QgsFeatureRequest().setFilterRect(self.fenetre)).setFilterExpression(texte).setSimplifyMethod(simple).setFlags(QgsFeatureRequest.ExactIntersect)
                    req_intra=(QgsFeatureRequest().setFilterRect(self.fenetre)).setFilterExpression('"'+self.impassibility+'" in (\'1\',\'2\',\'3\')').setSimplifyMethod(simple).setFlags(QgsFeatureRequest.ExactIntersect)
                    features=[f for f in layer.getFeatures(request)]
                    features_intra=[f for f in layer.getFeatures(req_intra)]

                    progressMessageBar = self.iface.messageBar().createMessage(QCoreApplication.translate("Interpolating...","Interpolating..."))
                    progress = QProgressBar()
                    progress.setMaximum(len(features))
                    progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

                    progressMessageBar.layout().addWidget(progress)
                    self.iface.messageBar().pushWidget(progressMessageBar, self.iface.messageBar().INFO)

                    for k,i in enumerate(features):
                        if k%100==0:
                            progress.setValue(k )
                        sens=i.attribute(self.flow_direction)
                        diffusion=i.attribute(self.diffusion_direction)
                        if self.flag_variable_speed:
                            speed=60/(1000*i.attribute(self.diffusion_speed))
                        else:
                            speed=60/(1000*self.default_speed)
                        if sens in ['1','2','3'] :
                            geom=i.geometry()
                            zone=geom.buffer(self.radius,12).boundingBox()
                            self.deltax=int((zone.xMinimum()-self.ll[0])/self.pixel_size_x)
                            self.deltay=int((zone.yMinimum()-self.ll[1])/self.pixel_size_y)
                            self.dx=int(zone.width()/self.pixel_size_x)
                            self.dy=int(zone.height()/self.pixel_size_y)
                            l1=geom.length()
                            geom_l=geom.asPolyline()
                            for p in range(self.dx):
                                d2x=self.deltax+p
                                for q in range(self.dy):
                                    d2y=self.deltay+q
                                    if 0<=d2x<self.nx and 0<=d2y<self.ny :
                                        pt1=QgsGeometry.fromPoint(QgsPoint(self.ll[0]+(d2x+0.5)*self.pixel_size_x,self.ll[1]+(d2y+0.5)*self.pixel_size_y))
                                        res=geom.closestSegmentWithContext(pt1.asPoint())
                                        d=round(res[0],self.decimals)

                                        if d<=grille_distance[d2x,self.ny-1-d2y] and d<self.radius*self.radius:
                                            if d>0 and l1>0:
                                                pt2=res[1]
                                                geoma=geom_l[:res[2]]+[pt2]
                                                l2=QgsGeometry.fromPolyline(geoma).length()
                                                if res[2]==0:
                                                    pt3=geom_l[res[2]]
                                                    pt4=geom_l[res[2]+1]
                                                else:
                                                    pt3=geom_l[res[2]-1]
                                                    pt4=geom_l[res[2]]
                                                p1=pt1.asPoint()
                                                test_sens=(pt4.x()-pt3.x())*(p1.y()-pt2.y())-(p1.x()-pt2.x())*(pt4.y()-pt3.y())
                                                if sens in ['1','3'] and not i.attribute(self.AB_j)==None:
                                                    if (diffusion in ['1','3'] and test_sens<=0) or (diffusion in ['2','3'] and test_sens>=0):
                                                        tj=i.attribute(self.AB_j)
                                                        if not tj==None:
                                                            ti=i.attribute(self.AB_i)
                                                            if not ti==None:
                                                                t=tj*(l2/l1)+ti*(1-(l2/l1))+math.sqrt(d)*speed
                                                                l3=QgsGeometry.fromPolyline([pt1.asPoint(),QgsPoint(pt2)])
                                                        result_test=False
                                                        if l3!=None:
                                                            if len(features_intra)>0:
                                                                for intra in features_intra:
                                                                    if intra.geometry().intersects(l3):
                                                                        result_test=True
                                                                        break
                                                        if result_test==False:
                                                            if t<grille[d2x,self.ny-1-d2y] or grille[d2x,self.ny-1-d2y]==-9999:
                                                                grille_distance[d2x,self.ny-1-d2y] =d
                                                                grille[d2x,self.ny-1-d2y] =t
                                                if sens in ['2','3'] and not i.attribute(self.BA_j)==None:
                                                    if (diffusion in ['1','3'] and test_sens>=0) or (diffusion in ['2','3'] and test_sens<=0):
                                                        tj=i.attribute(self.BA_j)
                                                        if not tj==None:
                                                            ti=i.attribute(self.BA_i)
                                                            if not ti==None:
                                                                t=ti*(l2/l1)+tj*(1-(l2/l1))+math.sqrt(d)*speed
                                                                l3=QgsGeometry.fromPolyline([pt1.asPoint(),QgsPoint(pt2)])
                                                        result_test=False
                                                        if l3!=None:
                                                            if len(features_intra)>0:
                                                                for intra in features_intra:
                                                                    if intra.geometry().intersects(l3):
                                                                        result_test=True
                                                                        break
                                                        if result_test==False:
                                                            if t<grille[d2x,self.ny-1-d2y] or grille[d2x,self.ny-1-d2y]==-9999:
                                                                grille_distance[d2x,self.ny-1-d2y] =d
                                                                grille[d2x,self.ny-1-d2y] =t
                    sortie=os.path.splitext(self.rasterfile)
                    fichier_grille=open(sortie[0]+".asc",'w')
                    fichier_grille.write("NCOLS {0:d}\nNROWS {1:d}\nXLLCORNER {2}\nYLLCORNER {3}\nDX {4}\nDY {5}\nNODATA_VALUE -9999\n".format(self.nx,self.ny,self.ll[0],self.ll[1],self.pixel_size_x,self.pixel_size_y))
                    fichier_grille2=open(sortie[0]+"_dist.asc",'w')
                    fichier_grille2.write("NCOLS {0:d}\nNROWS {1:d}\nXLLCORNER {2}\nYLLCORNER {3}\nDX {4}\nDY {5}\nNODATA_VALUE -9999\n".format(self.nx,self.ny,self.ll[0],self.ll[1],self.pixel_size_x,self.pixel_size_y))
                    g1=numpy.rot90(grille,1)
                    g1=numpy.flipud(g1)
                    g2=numpy.rot90(grille_distance,1)
                    g2=numpy.flipud(g2)
                    for i in g1:
                        fichier_grille.write(" ".join([str(ii) for ii in i])+"\n")
                    fichier_grille.close()
                    for i in g2:
                        fichier_grille2.write(" ".join([str(math.sqrt(ii)) for ii in i])+"\n")
                    fichier_grille2.close()

                    fichier_prj=open(sortie[0]+".prj",'w')
                    fichier2_prj=open(sortie[0]+"_dist.prj",'w')
                    fichier_prj.write(layer.crs().toWkt())
                    fichier2_prj.write(layer.crs().toWkt())
                    fichier_prj.close()
                    fichier2_prj.close()
                    nom_sortie=os.path.basename(sortie[0])
                    rlayer=QgsRasterLayer(sortie[0]+".asc",nom_sortie)
                    self.iface.messageBar().clearWidgets()
                    QgsMapLayerRegistry.instance().addMapLayer(rlayer)
            else:
                QMessageBox().information(None,QCoreApplication.translate("Linear interpolation","Linear interpolation"),QCoreApplication.translate("The active layer isn't composed of linear objects","The active layer isn't composed of linear objects"))
        else:
            QMessageBox().information(None,QCoreApplication.translate("Linear interpolation","Linear interpolation"),QCoreApplication.translate("The active layer isn't a vector layer","The active layer isn't a vector layer"))

        
        
    
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
                    lines.beginEditCommand(QCoreApplication.translate("Split polylines at connection","Split polylines at connection"))
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
                    QMessageBox().information(None,QCoreApplication.translate("Connect","Connect"),QCoreApplication.translate("The selected layer isn't composed of points","The selected layer isn't composed of points"))
            else:
                QMessageBox().information(None,QCoreApplication.translate("Connect","Connect"),QCoreApplication.translate("The active layer isn't composed of linear objects","The active layer isn't composed of linear objects"))
        else:
            QMessageBox().information(None,QCoreApplication.translate("Connect","Connect"),QCoreApplication.translate("No active layer","No active layer"))
        
        
