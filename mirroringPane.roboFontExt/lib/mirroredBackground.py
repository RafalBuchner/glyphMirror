from mymisc import *
from vanilla import *
from mojo.events import addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView
from mojo.drawingTools import *
from AppKit import  NSSegmentStyleRoundRect, NSRoundRectBezelStyle
from mojo.extensions import getExtensionDefault, setExtensionDefault


def dPoint(scale,p,s=6):
    s = s*scale
    r = s/2
    x, y = p
    rect(x-r,y-r,s,s)

class CustomInspectorExample(object):
    globalKey = "com.rafalbuchner.mirroringDrawingGlobal"
    localkey = "com.rafalbuchner.mirroringDrawingLocal"
    mirroringOptions = ["none","hor", "ver", "both"]
    mirroringOptionsDict = [dict(title=option) for option in mirroringOptions]
    showOptions = ["fill", "nodes", "stroke"]
    showOptionsDict = [dict(title=option) for option in showOptions]
    defaultGlobal = dict(drawGlyph=1,showOptions=[0],fillColor=(0,0,1,.5),strokeColor=(0,0,1,.5))
    defaultLocal = dict(mirroringOptions=3,offset=(0,0))
    def __init__(self):
        # subscribe to the moment when an inspector will be shown

        addObserver(self, "inspectorWindowWillShowDescriptions", "inspectorWindowWillShowDescriptions")
        addObserver(self, "saveSettingsCallback", "applicationWillTerminate")

        self.drawFill = False
        self.drawNodes = False
        self.drawStroke = False
        self.colorFill = (0,0,1)
        self.colorStroke = (0,0,1)
        self.glyph = CurrentGlyph()

        self.initUI()
    def initUI(self):
        btnH = 20
        txtH = 15
        x,y,p = 10,10,10
        self.view = Group((0,0,-0,-0))
        self.view.drawChBox = CheckBox((x,y,-p,btnH), "draw mirrored glyph", callback=self.drawChBoxCallback,sizeStyle="mini")
        y += btnH + p/2
        self.view.mirroringOptionsTxt = TextBox((x,y,-p,txtH), "mirroring options",sizeStyle="small")
        y += txtH + p/2
        self.view.mirroringOptions = SegmentedButton((x,y,-p,btnH), self.mirroringOptionsDict, sizeStyle="mini", callback=self.mirroringOptionsCallback)
        nsObj = self.view.mirroringOptions.getNSSegmentedButton()
        nsObj.setSegmentStyle_(NSSegmentStyleRoundRect)
        self.view.mirroringOptions.set([0])
        y += p + btnH
        self.view.showOptionsTxt = TextBox((x,y,-p,txtH), "show",sizeStyle="small")
        y += txtH + p/2
        self.view.showOptions = SegmentedButton((x,y,-p,btnH), self.showOptionsDict, sizeStyle="mini",callback=self.showOptionsCallback,selectionStyle="any")
        nsObj = self.view.showOptions.getNSSegmentedButton()
        nsObj.setSegmentStyle_(NSSegmentStyleRoundRect)
        y += p + btnH
        self.view.offsetTxt = TextBox((x,y,-p,txtH), "offset",sizeStyle="small")
        y += txtH + p/2
        self.view.offsetX = RBEditText((x,y,50,txtH), 0, sizeStyle="mini",placeholder="x value",callback=self.txtXCallback)
        self.view.offsetY = RBEditText((x+50,y,50,txtH), 0, sizeStyle="mini",placeholder="y value",callback=self.txtYCallback)
        y += btnH + p/2
        self.view.fillTxt = TextBox((x,y,-p,txtH), "fill",sizeStyle="small")
        self.view.fillColor = ColorWell((x+50, y, 50, txtH),
                                    callback=self.colorFillEdit, color=rgb2NSColor(self.colorFill))
        y += txtH + p/2
        self.view.strokeTxt = TextBox((x,y,-p,txtH), "stroke",sizeStyle="small")
        self.view.strokeColor = ColorWell((x+50, y, 50, txtH),
                                    callback=self.colorStrokeEdit, color=rgb2NSColor(self.colorStroke))
        y += txtH + p
        self.view.exportToLayer = Button((x,y,-p,btnH), "export to layer", sizeStyle="mini",callback=self.exportToLayerCallback)
        nsObj = self.view.exportToLayer.getNSButton()
        nsObj.setBezelStyle_(NSRoundRectBezelStyle)
        y += btnH + p
        self.height = y
        self.loadSettings()
        self.initCallbacksUI()
        self.loadGlyph()
        self.intiCallbackRadios()
        self.addObservers()

    def determineMirroringOption(self):
        if self.mirroringType == "none":
            self.reflectionMatrix = [1,0,0,1,0,0]
        if self.mirroringType == "both":
            self.reflectionMatrix = [-1,0,0,-1,0,0]
        if self.mirroringType == "ver":
            self.reflectionMatrix = [1,0,0,-1,0,0]
        if self.mirroringType == "hor":
            self.reflectionMatrix = [-1,0,0,1,0,0]
        # else:
        #     self.reflectionMatrix = [1,0,0,1,0,0]


    def addObservers(self):
        addObserver(self, "currentGlyphChangedCallback", "currentGlyphChanged")
        addObserver(self, "drawBackgroundCallback", "drawBackground")

    def removeObservers(self):
        removeObserver(self, "currentGlyphChanged")
        removeObserver(self, "drawBackground")

    def initCallbacksUI(self):
        self.txtXCallback(self.view.offsetX)
        self.txtYCallback(self.view.offsetY)
        self.colorFillEdit(self.view.fillColor)
        self.colorStrokeEdit(self.view.strokeColor)
        self.drawChBoxCallback(self.view.drawChBox)

    def intiCallbackRadios(self):
        self.mirroringType = "none"

    def drawAction(self, scale):
        def _drawGlyph():
            if self.drawNodes:
                fill( *self.colorStroke )
                stroke(None)
                for c in self.glyph:
                    for p in c.points:
                        dPoint(scale,p.position)

            strokeWidth(1 * scale)
            if self.drawStroke: stroke( *self.colorStroke )
            else:               stroke( None )
            if self.drawFill:   fill  ( *self.colorFill )
            else:               fill  ( None )
            drawGlyph(self.glyph)


        x, y = self.drawingMeasurements

        translate(x+self.offsetX,y+self.offsetY)
        self.determineMirroringOption()

        transform(self.reflectionMatrix)
        translate(-x,-y)


        _drawGlyph()


    def loadGlyph(self):
        if self.glyph is not None:
            offset = (self.offsetX, self.offsetY)
            localSettings = self.glyph.lib.get(self.localkey)
            if localSettings is None:
                self.glyph.lib[self.localkey] = self.defaultLocal
            else:
                # I will need to find another solution without exceptions:
                try:
                    self.glyph.lib[self.localkey] = dict(offset=offset, mirroringOptions=self.view.mirroringOptions.get())
                except:
                    self.glyph.lib[self.localkey] = dict(offset=offset, mirroringOptions=[3])


        self.glyph = CurrentGlyph()

        if self.glyph is not None:
            if self.localkey in self.glyph.lib:
                localSettings = self.glyph.lib[self.localkey]
            else:
                localSettings = self.defaultLocal

            offset = localSettings.get("offset")
            mirroringOptions = localSettings.get("mirroringOptions")
            if mirroringOptions is not None:
                self.view.mirroringOptions.set(mirroringOptions)
            if offset is not None:
                ox, oy = offset
                self.view.offsetX.set(ox)
                self.view.offsetY.set(oy)
                self.txtXCallback(self.view.offsetX)
                self.txtYCallback(self.view.offsetY)



    def saveSettings(self):
        settings = dict(
            drawGlyph=self.view.drawChBox.get(),
            showOptions=self.view.showOptions.get(),
            fillColor=nsColor2RGB(self.view.fillColor.get()),
            strokeColor=nsColor2RGB(self.view.strokeColor.get()),
        )
        setExtensionDefault(self.globalKey, settings)

    def loadSettings(self):
        if getExtensionDefault(self.globalKey) is None:
            self.settings = self.defaultGlobal
        else:
            self.settings = getExtensionDefault(globalKey)
        drawGlyph = self.settings.get("drawGlyph")
        showOptions = self.settings.get("showOptions")
        fillColor = self.settings.get("fillColor")
        strokeColor = self.settings.get("strokeColor")

        if drawGlyph is not None:
            self.view.drawChBox.set(drawGlyph)
        else:
            self.view.drawChBox.set( self.defaultGlobal['drawGlyph'] )

        if showOptions is not None:
            self.view.showOptions.set(showOptions)
        else:
            self.view.showOptions.set( self.defaultGlobal['showOptions'] )

        if fillColor is not None:
            self.view.fillColor.set( rgb2NSColor(fillColor) )
        else:
            self.view.fillColor.set( rgb2NSColor(self.defaultGlobal['fillColor']) )

        if strokeColor is not None:
            self.view.strokeColor.set( rgb2NSColor(strokeColor) )
        else:
            self.view.strokeColor.set( rgb2NSColor(self.defaultGlobal['strokeColor']) )
        self.colorFillEdit(self.view.fillColor)
        self.colorStrokeEdit(self.view.strokeColor)
        self.drawChBoxCallback(self.view.drawChBox)
        self.showOptionsCallback(self.view.showOptions)





    # UI callbacks
    def exportToLayerCallback(self,sender):
        pass

    def colorFillEdit(self,sender):
        color = sender.get()
        if isinstance(color, tuple):
            self.colorFill = sender.get()
        else:
            self.colorFill = nsColor2RGB(sender.get())
        UpdateCurrentGlyphView()

    def colorStrokeEdit(self, sender):
        color = sender.get()
        if isinstance(color, tuple):
            self.colorStroke = sender.get()
        else:
            self.colorStroke = nsColor2RGB(sender.get())
        UpdateCurrentGlyphView()

    def txtXCallback(self, sender):
        self.offsetX = float(sender.get())
        UpdateCurrentGlyphView()

    def txtYCallback(self, sender):
        self.offsetY = float(sender.get())
        UpdateCurrentGlyphView()

    def showOptionsCallback(self, sender):
        if len(sender.get()) == 0:
            sender.set([0])
        if 0 in sender.get():
            self.drawFill = True
        else:
            self.drawFill = False
        if 1 in sender.get():
            self.drawNodes = True
        else:
            self.drawNodes = False

        if 2 in sender.get():
            self.drawStroke = True
        else:
            self.drawStroke = False
        UpdateCurrentGlyphView()

    def mirroringOptionsCallback(self, sender):
        self.mirroringType = self.mirroringOptions[sender.get()]

        UpdateCurrentGlyphView()

    def drawChBoxCallback(self, sender):
        self.drawGlyph = False
        if sender.get() == 1:
            self.drawGlyph = True
            self.addObservers()
        else:
            self.removeObservers()
        UpdateCurrentGlyphView()

    # observer events
    def saveSettingsCallback(self, info):
        self.saveSettings()

    def currentGlyphChangedCallback(self, info):
        self.loadGlyph()

    def drawBackgroundCallback(self, info):
        if self.glyph is not None and self.drawGlyph:
            scale = info['scale']
            save()
            self.drawAction(scale)
            restore()

    @property
    def drawingMeasurements(self):
        _x,_y,x_,y_ = self.glyph.bounds
        self.__drawingMeasurements = ((x_-_x)/2+_x,(y_-_y)/2+_y)
        return self.__drawingMeasurements

    ########## stuff
    def inspectorWindowWillShowDescriptions(self, notification):
        # create an inspector item
        item = dict(label="Mirror Glyph", view=self.view, size=self.height)
        # insert or append the item to the list of inspector panes

        notification["descriptions"].insert(4, item)




CustomInspectorExample()
