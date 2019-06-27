from vanilla import *
from mymisc import *
from mojo.events import addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView
from mojo.drawingTools import *
from AppKit import NSSegmentStyleRoundRect, NSRoundRectBezelStyle
from mojo.extensions import getExtensionDefault, setExtensionDefault


def dPoint(scale, p, s=4):
    s = s * scale
    r = s / 2
    x, y = p
    rect(x - r, y - r, s, s)


def offsetPoint(offset, point):
    ox, oy = offset
    x, y = point
    return (ox+x, oy+y)


class MirrorPane(object):
    globalKey = "com.rafalbuchner.mirroringDrawingGlobal"
    localkey = "com.rafalbuchner.mirroringDrawingLocal"
    mirroringOptions = ["None", "Horizontal", "Vertical", "Both"]
    mirroringOptionsDict = [dict(title=option) for option in mirroringOptions]
    showOptions = ["Fill", "Nodes", "Stroke"]
    showOptionsDict = [dict(title=option) for option in showOptions]
    defaultGlobal = dict(drawGlyph=1, showOptions=[0], color=(0, 0, 1, .45))
    defaultLocal = dict(mirroringOptions=3, offset=(0, 0))

    def __init__(self):
        self.glyph = CurrentGlyph()
        self.mirroringType = "None"
        self.initUI()
        self.addObservers()
        addObserver(self, "inspectorWindowWillShowDescriptions",
                    "inspectorWindowWillShowDescriptions")

    def initUI(self):
        btnH = 20
        txtH = 17
        x, y, p = 10, 10, 10

        self.loadSettings()
        self.view = Group((0, 0, -0, -0))
        self.view.drawChBox = CheckBox((x, y, -p, btnH), "Show mirrored glyph", callback=self.drawChBoxCallback,
                                       sizeStyle="small")
        y += btnH + p / 2
        self.view.mirroringOptionsTxt = TextBox(
            (x, y, -p, txtH), "Reflection", sizeStyle="small")
        y += txtH + p / 2
        self.view.mirroringOptions = SegmentedButton((x, y, -p, btnH), self.mirroringOptionsDict, sizeStyle="small",
                                                     callback=self.mirroringOptionsCallback)

        nsObj = self.view.mirroringOptions.getNSSegmentedButton()
        nsObj.setSegmentStyle_(NSSegmentStyleRoundRect)
        # self.view.mirroringOptions.set([0])
        y += p + btnH
        self.view.showOptionsTxt = TextBox(
            (x, y, -p, txtH), "Display", sizeStyle="small")
        y += txtH + p / 2

        print(self.showOptionsDict)

        # CheckBox(posSize, title, callback=None, value=False, sizeStyle='regular')
        # self.view.showOptions = SegmentedButton((x, y, -p, btnH), self.showOptionsDict, sizeStyle="small",
        #                                         callback=self.showOptionsCallback, selectionStyle="any")
        self.view.showOptions = CheckBox((x, y, -p, btnH), self.showOptions[0], sizeStyle="regular",
                                         callback=self.showOptionsCallback, value="False")
        # self.view.showOptions = CheckBox((x, y, -p, btnH), self.showOptions[1], sizeStyle="regular",
        #                                  callback=self.showOptionsCallback, value="False")
        # self.view.showOptions = CheckBox((x, y, -p, btnH), self.showOptions[2], sizeStyle="regular",
        #                                  callback=self.showOptionsCallback, value="False")
        # nsObj = self.view.showOptions.getNSSegmentedButton()
        # nsObj.setSegmentStyle_(NSSegmentStyleRoundRect)
        y += p + btnH
        self.view.offsetTxt = TextBox(
            (x, y, -p, txtH), "offset", sizeStyle="small")
        y += txtH + p / 2
        self.view.offsetLabel = TextBox(
            (x, y+2, -p, txtH), "x : y", sizeStyle="small")

        self.view.offset = RBEditText((x + 40, y, 75, btnH), 0, sizeStyle="small", placeholder="x : y",
                                      callback=self.txtCallback)
        y += btnH + p / 2
        self.view.colorTxt = TextBox(
            (x, y+2, -p, txtH), "color", sizeStyle="small")
        self.view.colorCW = ColorWell((x + 40, y, 75, btnH),
                                      callback=self.colorEdit, color=rgb2NSColor(self.color))
        y += btnH + p
        self.view.exportToLayer = Button((x, y, -p, btnH), "Export to layer…", sizeStyle="small",
                                         callback=self.exportToLayerCallback)
        nsObj = self.view.exportToLayer.getNSButton()
        nsObj.setBezelStyle_(NSRoundRectBezelStyle)
        y += btnH + p
        self.height = y

        self.initLocalsUI()
        self.initGlobalsUI()
        self.loadGlyph(initialLoad=True)

    def determineMirroringOption(self):
        if self.mirroringType == "None":
            self.reflectionMatrix = [1, 0, 0, 1, 0, 0]
        if self.mirroringType == "Both":
            self.reflectionMatrix = [-1, 0, 0, -1, 0, 0]
        if self.mirroringType == "Vertical":
            self.reflectionMatrix = [1, 0, 0, -1, 0, 0]
        if self.mirroringType == "Horizontal":
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

    def drawAction(self, scale):
        def _drawGlyph():
            stroke(*self.color)
            if self.drawNodes:
                fill(*self.color)
                # stroke(None)
                for c in self.glyph:
                    for p in c.bPoints:
                        _p, p, p_ = (p.bcpIn, p.anchor, p.bcpOut)
                        dPoint(scale, p)
                        if _p != (0, 0):
                            _p = offsetPoint(p, _p)
                            dPoint(scale, _p)
                            line(_p, p)
                        if p_ != (0, 0):
                            p_ = offsetPoint(p, p_)
                            dPoint(scale, p_)
                            line(p_, p)

            if not self.drawStroke:
                stroke(None)
            if self.drawFill:
                fill(*self.color)
            else:
                fill(None)
            drawGlyph(self.glyph)

        if self.offset is not None:
            x, y = self.drawingMeasurements
            ox, oy = self.offset
            translate(x + ox, y + oy)
            self.determineMirroringOption()

            transform(self.reflectionMatrix)
            translate(-x, -y)

            _drawGlyph()

    def loadGlyph(self, initialLoad=False):
        if self.glyph is not None and not initialLoad:
            if self.offset is not None:
                offset = self.offset
            else:
                offset = (0, 0)
            localSettings = self.glyph.lib.get(self.localkey)
            if localSettings is None:
                self.glyph.lib[self.localkey] = self.defaultLocal
            else:
                # I will need to find another solution without exceptions:
                self.glyph.lib[self.localkey] = dict(offset=offset,
                                                     mirroringOptions=self.view.mirroringOptions.get())
                # try:
                #     self.glyph.lib[self.localkey] = dict(offset=offset,
                #                                          mirroringOptions=self.view.mirroringOptions.get())
                # except:
                #     self.glyph.lib[self.localkey] = dict(offset=offset, mirroringOptions=[3])

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
                self.mirroringOptionsCallback(self.view.mirroringOptions)
            if offset is not None:
                self.view.offset.set(offset)
                self.txtCallback(self.view.offset)

    def saveSettings(self):
        settings = dict(
            drawGlyph=self.view.drawChBox.get(),
            showOptions=self.view.showOptions.get(),
            color=nsColor2RGB(self.view.colorCW.get()),
        )
        setExtensionDefault(self.globalKey, settings)

    def loadSettings(self):
        if getExtensionDefault(self.globalKey) is None:
            self.settings = self.defaultGlobal
        else:
            self.settings = getExtensionDefault(self.globalKey)
        drawGlyph = self.settings.get("drawGlyph")
        showOptions = self.settings.get("showOptions")
        color = self.settings.get("color")
        if drawGlyph is not None:
            self.drawGlyph = drawGlyph
        else:
            self.drawGlyph = self.defaultGlobal['drawGlyph']
        if showOptions is not None:
            self.showOptions = showOptions
        else:
            self.showOptions = self.defaultGlobal['showOptions']
        if color is not None:
            self.color = color
        else:
            self.color = self.defaultGlobal['color']

    def initGlobalsUI(self):
        self.view.drawChBox.set(self.drawGlyph)
        self.view.colorCW.set(rgb2NSColor(self.color))
        self.drawChBoxCallback(self.view.drawChBox)
        self.colorEdit(self.view.colorCW)

    def initLocalsUI(self):
        self.view.showOptions.set(self.showOptions)
        self.showOptionsCallback(self.view.showOptions)
        self.txtCallback(self.view.offset)

    # UI callbacks
    def _layerBtnCallback(self, sender):
        print("A")
        print(sender.getTitle())

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
                a, b, c, d, e, f = self.reflectionMatrix
                e += ox
                f += oy
                targetGlyph.transformBy((a, b, c, d, e, f), origin=origin)

        x, y, p = 5, 5, 5
        btnH = 20
        height = y
        self.pop = Popover((0, 0))
        self.pop.cb = self._layerBtnCallback
        for i, layer in enumerate(self.glyph.font.layerOrder):
            setattr(self.pop, layer + "_cb", _layerBtnCallback)
            # cb = getattr(self.pop, layer + "_cb" )
            # print(cb)
            obj = Button((x, y + (btnH+p)*i, -p, btnH), layer,
                         sizeStyle="small", callback=_layerBtnCallback)
            setattr(self.pop, layer + "_btn", obj)
            height += y + btnH
        self.pop.resize(140, height)
        # , relativeRect=relativeRect)
        self.pop.open(parentView=sender, preferredEdge='left')

    def colorEdit(self, sender):
        color = sender.get()
        if isinstance(color, tuple):
            self.color = sender.get()
        else:
            self.color = nsColor2RGB(sender.get())
        UpdateCurrentGlyphView()

    def txtCallback(self, sender):
        self.offset = sender.get()
        UpdateCurrentGlyphView()

    def showOptionsCallback(self, sender):

        print(sender)
        # if len(sender.get()) == 0:
        #     sender.set([0])
        # if 0 in sender.get():
        #     self.drawFill = True
        # else:
        #     self.drawFill = False
        # if 1 in sender.get():
        #     self.drawNodes = True
        # else:
        #     self.drawNodes = False

        # if 2 in sender.get():
        #     self.drawStroke = True
        # else:
        #     self.drawStroke = False
        # UpdateCurrentGlyphView()

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
    def drawingMeasurements(self):
        _x, _y, x_, y_ = self.glyph.bounds
        self.__drawingMeasurements = ((x_ - _x) / 2 + _x, (y_ - _y) / 2 + _y)
        return self.__drawingMeasurements

    # stuff
    def inspectorWindowWillShowDescriptions(self, notification):
        # create an inspector item
        item = dict(label="Glyph Mirror", view=self.view, size=self.height)
        # insert or append the item to the list of inspector panes

        notification["descriptions"].insert(4, item)


mirrorPane = MirrorPane()
test = False
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
