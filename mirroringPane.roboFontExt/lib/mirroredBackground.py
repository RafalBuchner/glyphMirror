from mymisc import *
from vanilla import *
from mojo.events import addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView
from mojo.drawingTools import *
from AppKit import NSSegmentStyleRoundRect, NSRoundRectBezelStyle
from mojo.extensions import getExtensionDefault, setExtensionDefault
from copy import deepcopy

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def dPoint(scale, p, s=4):
    s = s * scale
    r = s / 2
    x, y = p
    rect(x - r, y - r, s, s)

def offsetPoint(offset, point):
    ox,oy = offset
    x, y = point
    return (ox+x, oy+y)


class MirrorPane(object):
    globalKey = "com.rafalbuchner.mirroringDrawingGlobal"
    localkey = "com.rafalbuchner.mirroringDrawingLocal"
    mirroringOptions = ["none", "hor", "ver", "both"]
    mirroringOptionsDict = [dict(title=option) for option in mirroringOptions]
    showOptions = ["fill", "nodes", "stroke"]
    showOptionsDict = [dict(title=option) for option in showOptions]
    defaultGlobal = dict(drawGlyph=1, showOptions=[0], colorFill=(0, 0, 1, .45), colorStroke=(0, 0, 1, .45))
    defaultLocal = dict(mirroringOptions=3, offset=(0, 0))

    def __init__(self):
        self.glyph = CurrentGlyph()
        self.working_options = self.defaultLocal
        self.initUI()
        self.addObservers()
        addObserver(self, "inspectorWindowWillShowDescriptions", "inspectorWindowWillShowDescriptions")

    def initUI(self):
        btnH = 20
        txtH = 15
        x, y, p = 10, 10, 10

        self.loadSettings()
        self.view = Group((0, 0, -0, -0))
        self.view.drawChBox = CheckBox((x, y, -p, btnH), "draw mirrored glyph", callback=self.drawChBoxCallback,
                                       sizeStyle="mini")
        y += btnH + p / 2
        self.view.mirroringOptionsTxt = TextBox((x, y, -p, txtH), "mirroring options", sizeStyle="small")
        y += txtH + p / 2
        self.view.mirroringOptions = SegmentedButton((x, y, -p, btnH), self.mirroringOptionsDict, sizeStyle="mini",
                                                     callback=self.mirroringOptionsCallback)
        nsObj = self.view.mirroringOptions.getNSSegmentedButton()
        nsObj.setSegmentStyle_(NSSegmentStyleRoundRect)
        self.view.mirroringOptions.set([0])
        y += p + btnH
        self.view.showOptionsTxt = TextBox((x, y, -p, txtH), "show", sizeStyle="small")
        y += txtH + p / 2
        self.view.showOptions = SegmentedButton((x, y, -p, btnH), self.showOptionsDict, sizeStyle="mini",
                                                callback=self.showOptionsCallback, selectionStyle="any")
        nsObj = self.view.showOptions.getNSSegmentedButton()
        nsObj.setSegmentStyle_(NSSegmentStyleRoundRect)
        y += p + btnH
        self.view.offsetTxt = TextBox((x, y, -p, txtH), "offset", sizeStyle="small")
        y += txtH + p / 2
        self.view.offsetX = RBEditText((x, y, 50, txtH), 0, sizeStyle="mini", placeholder="x value",
                                       callback=self.txtXCallback)
        self.view.offsetY = RBEditText((x + 50, y, 50, txtH), 0, sizeStyle="mini", placeholder="y value",
                                       callback=self.txtYCallback)
        y += btnH + p / 2
        self.view.fillTxt = TextBox((x, y, -p, txtH), "fill", sizeStyle="small")
        self.view.colorFillCW = ColorWell((x + 50, y, 50, txtH),
                                          callback=self.colorFillEdit, color=rgb2NSColor(self.colorFill))
        self.view.generateBasedOnFillChBox = CheckBox((x+p*11,y,-p,txtH), 'Generate stroke from fill', sizeStyle="mini", callback=self.generateStrokeColorBasedOnFillCallBack)
        y += txtH + p / 2
        self.view.strokeTxt = TextBox((x, y, -p, txtH), "stroke", sizeStyle="small")
        self.view.colorStroke = ColorWell((x + 50, y, 50, txtH),
                                          callback=self.colorStrokeEdit, color=rgb2NSColor(self.colorStroke))
        y += txtH + p
        self.view.exportToLayer = Button((x, y, -p, btnH), "export to layer", sizeStyle="mini",
                                         callback=self.exportToLayerCallback)
        nsObj = self.view.exportToLayer.getNSButton()
        nsObj.setBezelStyle_(NSRoundRectBezelStyle)
        y += btnH + p
        self.view.saveSettingsForCurrentGlyph = Button((x, y, -p, btnH), "Save settings for Glyph", sizeStyle="mini",
                                         callback=self.saveSettingsForCurrentGlyphCallback)
        nsObj = self.view.saveSettingsForCurrentGlyph.getNSButton()
        nsObj.setBezelStyle_(NSRoundRectBezelStyle)
        y += btnH + p
        self.height = y

        self.initLocalsUI()
        self.initGlobalsUI()
        self.loadGlyph()
        self.intiCallbackRadios()

    def determineMirroringOption(self):
        self.mirroringType = self.mirroringOptions[self.working_options['mirroringOptions']]
        if self.mirroringType == "none":
            self.reflectionMatrix = [1, 0, 0, 1, 0, 0]
        if self.mirroringType == "both":
            self.reflectionMatrix = [-1, 0, 0, -1, 0, 0]
        if self.mirroringType == "ver":
            self.reflectionMatrix = [1, 0, 0, -1, 0, 0]
        if self.mirroringType == "hor":
            self.reflectionMatrix = [-1, 0, 0, 1, 0, 0]
        # else:
        #     self.reflectionMatrix = [1,0,0,1,0,0]

    def addObservers(self):
        addObserver(self, "saveSettingsCallback", "fontWillClose")
        addObserver(self, "currentGlyphChangedCallback", "currentGlyphChanged")
        addObserver(self, "currentGlyphChangedCallback", "glyphWindowDidOpen")
        addObserver(self, "drawBackgroundCallback", "drawBackground")

    def removeObservers(self):
        removeObserver(self, "inspectorWindowWillShowDescriptions")
        removeObserver(self, "fontWillClose")
        removeObserver(self, "currentGlyphChanged")
        removeObserver(self, "glyphWindowDidOpen")
        removeObserver(self, "drawBackground")

    def initLocalsUI(self):
        self.txtXCallback(self.view.offsetX)
        self.txtYCallback(self.view.offsetY)


    def intiCallbackRadios(self):
        self.mirroringType = "none"

    def drawAction(self, scale):
        def _drawGlyph():
            if self.generateStrokeColorBasedOnFill == 1:
                r,g,b,a = nsColor2RGB(self.view.colorFillCW.get())
                colorStroke = (r,g,b,a*.3)
            else:
                colorStroke = self.colorStroke
            stroke(*colorStroke)
            if self.drawNodes:
                fill(*colorStroke)
                # stroke(None)
                for c in self.glyph:
                    for p in c.bPoints:
                        _p, p, p_ = (p.bcpIn, p.anchor, p.bcpOut)
                        dPoint(scale, p)
                        if _p != (0,0):
                            _p = offsetPoint(p,_p)
                            dPoint(scale, _p)
                            line(_p, p)
                        if p_ != (0,0):
                            p_ = offsetPoint(p,p_)
                            dPoint(scale, p_)
                            line(p_, p)

            if not self.drawStroke:
                stroke(None)
            if self.drawFill:
                fill(*self.colorFill)
            else:
                fill(None)
            drawGlyph(self.glyph)

        x, y = self.drawingMeasurements
        self.offsetX, self.offsetY = self.working_options['offset']
        translate(x + self.offsetX, y + self.offsetY)
        self.determineMirroringOption()

        transform(self.reflectionMatrix)
        translate(-x, -y)

        _drawGlyph()

    def loadGlyph(self):
        self.glyph = CurrentGlyph()

        if self.glyph is not None:
            self.working_options = self.glyph.lib.get(self.localkey)
            if self.glyph.lib.get(self.localkey) is None:
                globalSettings = self.glyph.font.lib.get(self.globalKey)
                if globalSettings is not None:
                    globalGlyphSettings = globalSettings.get('glyphSettings', self.defaultLocal)
                else:
                    globalGlyphSettings = self.defaultLocal
                self.working_options = globalGlyphSettings

            offsetX, offsetY = self.working_options['offset']
            mirroringOptions = self.working_options['mirroringOptions']
            self.view.offsetX.set(offsetX)
            self.view.offsetY.set(offsetY)
            self.view.mirroringOptions.set(mirroringOptions)

    def saveCurrentGlyphSettingsAsGlobal(self):
        glyphSettings = self.working_options
        settings = getExtensionDefault(self.globalKey)
        settings['glyphSettings'] = glyphSettings
        setExtensionDefault(self.globalKey, settings)

    def saveSettings(self):
        glyphSettings = self.working_options
        settings = dict(
            drawGlyph=self.view.drawChBox.get(),
            showOptions=self.view.showOptions.get(),
            colorFill=nsColor2RGB(self.view.colorFillCW.get()),
            colorStroke=nsColor2RGB(self.view.colorStroke.get()),
            glyphSettings=glyphSettings,
            generateStrokeColorBasedOnFill=self.generateStrokeColorBasedOnFill
        )
        setExtensionDefault(self.globalKey, settings)

    def loadSettings(self):
        if getExtensionDefault(self.globalKey) is None:
            self.settings = self.defaultGlobal
        else:
            self.settings = getExtensionDefault(self.globalKey)
        drawGlyph = self.settings.get("drawGlyph")
        showOptions = self.settings.get("showOptions")
        colorFill = self.settings.get("colorFill")
        colorStroke = self.settings.get("colorStroke")
        self.generateStrokeColorBasedOnFill = self.settings.get("generateStrokeColorBasedOnFill", 0)
        if drawGlyph is not None:
            self.drawGlyph = drawGlyph
        else:
            self.drawGlyph = self.defaultGlobal['drawGlyph']
        if showOptions is not None:
            self.showOptions = showOptions
        else:
            self.showOptions = self.defaultGlobal['showOptions']
        if colorFill is not None:
            self.colorFill = colorFill
        else:
            self.colorFill = self.defaultGlobal['colorFill']
        if colorStroke is not None:
            self.colorStroke = colorStroke
        else:
            self.colorStroke = self.defaultGlobal['colorStroke']

    def initGlobalsUI(self):
        self.view.drawChBox.set(self.drawGlyph)
        self.view.showOptions.set(self.showOptions)
        self.view.colorFillCW.set(rgb2NSColor(self.colorFill))
        self.view.colorStroke.set(rgb2NSColor(self.colorStroke))
        self.colorFillEdit(self.view.colorFillCW)
        self.colorStrokeEdit(self.view.colorStroke)
        self.drawChBoxCallback(self.view.drawChBox)
        self.showOptionsCallback(self.view.showOptions)
        self.showOptionsCallback(self.view.showOptions)
        self.generateStrokeColorBasedOnFillCallBack(self.view.generateBasedOnFillChBox)

    # UI callbacks
    def generateStrokeColorBasedOnFillCallBack(self, sender):
        if sender.get() == 1:
            self.view.colorStroke.enable(False)
            self.view.strokeTxt.enable(False)
            self.generateStrokeColorBasedOnFill = 1

        else:
            self.view.colorStroke.enable(True)
            self.view.strokeTxt.enable(True)
            self.generateStrokeColorBasedOnFill = 0


    def exportToLayerCallback(self, sender):
        def _layerBtnCallback(sender):
            layersource = self.glyph.layer.name
            layertarget = sender.getTitle()
            if layersource != layertarget:
                targetGlyph = self.glyph.getLayer(layertarget, True)
                self.glyph.copyLayerToLayer(layersource, layertarget)
                x, y = self.drawingMeasurements
                ox, oy = self.offset
                origin = (x, y)
                self.determineMirroringOption()
                a,b,c,d,e,f = self.reflectionMatrix
                e += ox
                f += oy
                targetGlyph.transformBy((a,b,c,d,e,f), origin=origin)

        x,y,p = 5,5,5
        btnH = 20
        height = y
        self.pop = Popover((0, 0))
        self.pop.cb = self._layerBtnCallback
        for i, layer in enumerate(self.glyph.font.layerOrder):
            setattr(self.pop, layer + "_cb", _layerBtnCallback)

            obj = Button((x, y + (btnH+p)*i, -p, btnH), layer, sizeStyle="small", callback=_layerBtnCallback)
            setattr(self.pop, layer + "_btn", obj)
            height +=y + btnH
        self.pop.resize(140, height)
        self.pop.open(parentView=sender, preferredEdge='left')#, relativeRect=relativeRect)

    def saveSettingsForCurrentGlyphCallback(self, sender):
        self.glyph.lib[self.localkey] = deepcopy(self.working_options)

    def colorFillEdit(self, sender):
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
        self.offsetX = 0
        if sender.get() is not None:
            if isfloat(sender.get()):
                self.offsetX = float(sender.get())
        # self.saveCurrentGlyphSettingsAsGlobal()
        UpdateCurrentGlyphView()

    def txtYCallback(self, sender):
        self.offsetY = 0
        if sender.get() is not None:
            if isfloat(sender.get()):
                self.offsetY = float(sender.get())
        # self.saveCurrentGlyphSettingsAsGlobal()
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
        self.drawGlyph = 0
        if sender.get() == 1:
            self.drawGlyph = 1
        UpdateCurrentGlyphView()

    # observer events
    def saveSettingsCallback(self, info):
        self.saveSettings()

    def currentGlyphChangedCallback(self, info):
        self.loadGlyph()

    def drawBackgroundCallback(self, info):
        if self.glyph is not None and self.drawGlyph == 1:
            scale = info['scale']
            save()
            self.drawAction(scale)
            restore()

    @property
    def mirroringType(self):
        return self.__mirroringType

    @mirroringType.setter
    def mirroringType(self, value):
        self.__mirroringType = value
        mirroringOptions = self.mirroringOptions.index(value)
        self.working_options['mirroringOptions'] = mirroringOptions

    @property
    def offsetX(self):
        return self.__offsetX

    @offsetX.setter
    def offsetX(self, value):
        self.__offsetX = value
        x,y = self.working_options.get('offset', (0,0))
        offset = (value, y)
        self.working_options['offset'] = offset
    
    @property
    def offsetY(self):
        return self.__offsetY

    @offsetY.setter
    def offsetY(self, value):
        self.__offsetY = value
        x,y = self.working_options.get('offset', (0,0))
        offset = (x, value)
        self.working_options['offset'] = offset

    @property
    def drawingMeasurements(self):
        _x, _y, x_, y_ = self.glyph.bounds
        self.__drawingMeasurements = ((x_ - _x) / 2 + _x, (y_ - _y) / 2 + _y)
        return self.__drawingMeasurements

    ########## stuff
    def inspectorWindowWillShowDescriptions(self, notification):
        # create an inspector item
        item = dict(label="Mirror Glyph", view=self.view, size=self.height)
        # insert or append the item to the list of inspector panes

        notification["descriptions"].insert(4, item)


mirrorPane = MirrorPane()
test = True
if test:
    class Win:
        def __init__(self, MirrorPane):
            self.pane = MirrorPane
            self.w = FloatingWindow((100, 100, 100, 100))
            self.w.bind("close", self.close)
            self.w.open()

        def close(self, sender):
            self.pane.removeObservers()


    Win(mirrorPane)
