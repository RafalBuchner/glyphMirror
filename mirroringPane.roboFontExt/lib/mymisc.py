from AppKit import NSColor, NSTextField
from vanilla.vanillaBase import VanillaCallbackWrapper
digits_dot_minus = "1234567890.-"
from vanilla import EditText
class RBVanillaEditTextDelegate(VanillaCallbackWrapper):

    _continuous = True

    def control_textView_doCommandBySelector_(self, control, textView, selector):
        if "move" in selector and ( "EndOfDocument" in selector or "EndOfLine" in selector or "BeginningOfDocument" in selector):
            xvalue, yvalue = 1, 1
            if "Left" in selector or "EndOfDocument" in selector:
                xvalue *= -1
                yvalue *= -1
            if "AndModifySelection" in selector and ("BeginningOfDocument" in selector or "EndOfDocument" in selector or "Right" in selector or "Left" in selector):
                yvalue *= 10
                xvalue *= 10
            # if "End" in selector or "Beggining" in selector or "deleteBackward" in selector: return False

            try:

                strValue = textView.string()
                strValue = strValue.replace(",",".")
                strValue = strValue.replace("  ","")
                strValue = strValue.replace(" ","")
                strXvalue, strYvalue = strValue.split(":")
                if "BeginningOfDocument" in selector or "EndOfDocument" in selector:
                    floatYvalue = float(strYvalue)
                    floatYvalue += yvalue
                    floatYvalue = round(floatYvalue, 3)
                    if floatYvalue % 1 != 0:
                        strYvalue = floatYvalue
                    else:
                        strYvalue = int(floatYvalue)
                else:
                    floatXvalue = float(strXvalue)
                    floatXvalue += yvalue
                    floatXvalue = round(floatXvalue, 3)
                    if floatXvalue % 1 != 0:
                        strXvalue = floatXvalue
                    else:
                        strXvalue = int(floatXvalue)

                textView.setString_(f"{strXvalue} : {strYvalue}")
                self.action_(control)
                return True
            except:
                return True
        else:
            return False

    def controlTextDidChange_(self, notification):
        if self._continuous:
            self.action_(notification.object())

    def controlTextDidEndEditing_(self, notification):
        if not self._continuous:
            self.action_(notification.object())

class RBEditText(EditText):
    nsTextFieldClass = NSTextField
    nsTextFieldDelegateClass = RBVanillaEditTextDelegate
    def get(self):
        stringValue = self._nsObject.objectValue()
        if isinstance(stringValue, str):
            if len(stringValue.split(":")) == 2:
                strXvalue, strYvalue = stringValue.split(":")
                strXvalue, strYvalue = strXvalue.replace("  ", ""), strYvalue.replace("  ", "")
                strXvalue, strYvalue = strXvalue.replace(" ", ""), strYvalue.replace(" ", "")

                if not strXvalue.replace('.',"",1).isdigit() or not strYvalue.replace('.',"", 1).isdigit():
                    return None
                else:
                    x = float(strXvalue)
                    y = float(strYvalue)
                    if x % 1 != 0: x = x
                    else: x = int(x)
                    if y % 1 != 0: y = y
                    else: y = int(y)
                    return x, y
        else:
            return None
    def set(self, value):
        """
        Set the contents of the text entry control.
        **value** An object representing the contents of the text entry control.
        If no formatter has been assigned to the control, this should be a string.
        If a formatter has been assigned, this should be an object of the type that
        the formatter expects.
        """
        if value is not None:
            # assert value is tuple, print(value)
            x,y = value
            assert type(x) == int and type(y) == int or type(x) == float and type(y) == float, print(value)

            self._nsObject.setObjectValue_(f'{x} : {y}')
        else:
            self._nsObject.setObjectValue_('0 : 0')


def rgb2NSColor(rgb):
    if rgb is None:
        return
    elif len(rgb) == 1:
        r = g = b = rgb[0]
        a = 1.0
    elif len(rgb) == 2:
        grey, a = rgb
        r = g = b = grey
    elif len(rgb) == 3:
        r, g, b = rgb
        a = 1.0
    elif len(rgb) == 4:
        r, g, b, a = rgb
    else:
        return
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)

def nsColor2RGB(nsColor):
    return nsColor.redComponent(), nsColor.greenComponent(), nsColor.blueComponent(), nsColor.alphaComponent()


############ segmented button issue

from AppKit import NSSegmentedControl, NSSegmentedCell, NSImage, NSSegmentSwitchTrackingSelectOne, NSSegmentSwitchTrackingSelectAny, NSSegmentSwitchTrackingMomentary

from vanilla.py23 import range
from vanilla.vanillaBase import VanillaBaseControl


_trackingModeMap = {
    "one": NSSegmentSwitchTrackingSelectOne,
    "any": NSSegmentSwitchTrackingSelectAny,
    "momentary": NSSegmentSwitchTrackingMomentary,
}


class SegmentedButton(VanillaBaseControl):

    """
    A standard segmented button.::
        from vanilla import *
        class SegmentedButtonDemo(object):
             def __init__(self):
                 self.w = Window((100, 40))
                 self.w.button = SegmentedButton((10, 10, -10, 20),
                     [dict(title="A"), dict(title="B"), dict(title="C")],
                    callback=self.buttonCallback)
                 self.w.open()
             def buttonCallback(self, sender):
                 print("button hit!")
        SegmentedButtonDemo()
    **posSize** Tuple of form *(left, top, width, height)* representing the position
    and size of the segmented button. The size of the segmented button sould match
    the appropriate value for the given *sizeStyle*.
    +-------------------------+
    | **Standard Dimensions** |
    +=========+===+===========+
    | Regular | H | 21        |
    +---------+---+-----------+
    | Small   | H | 18        |
    +---------+---+-----------+
    | Mini    | H | 15        |
    +---------+---+-----------+
    **segmentDescriptions** An ordered list of dictionaries describing the segments.
    +----------------------------+--------------------------------------------------------------------------------------------------+
    | width (optional)           | The desired width of the segment.                                                                |
    +----------------------------+--------------------------------------------------------------------------------------------------+
    | title (optional)           | The title of the segment.                                                                        |
    +----------------------------+--------------------------------------------------------------------------------------------------+
    | enabled (optional)         | The enabled state of the segment. The default is `True`.                                         |
    +----------------------------+--------------------------------------------------------------------------------------------------+
    | imagePath (optional)       | A file path to an image to display in the segment.                                               |
    +----------------------------+--------------------------------------------------------------------------------------------------+
    | imageNamed (optional)      | The name of an image already loaded as a *NSImage* by the application to display in the segment. |
    +----------------------------+--------------------------------------------------------------------------------------------------+
    | imageObject (optional)     | A *NSImage* object to display in the segment.                                                    |
    +----------------------------+--------------------------------------------------------------------------------------------------+
    | *imageTemplate* (optional) | A boolean representing if the image should converted to a template image.                        |
    +----------------------------+--------------------------------------------------------------------------------------------------+
    **callback** The method to be called when the user presses the segmented button.
    **selectionStyle** The selection style in the segmented button.
    +-----------+---------------------------------------------+
    | one       | Only one segment may be selected.           |
    +-----------+---------------------------------------------+
    | any       | Any number of segments may be selected.     |
    +-----------+---------------------------------------------+
    | momentary | A segmented is only selected when tracking. |
    +-----------+---------------------------------------------+
    **sizeStyle** A string representing the desired size style of the segmented button. The options are:
    +-----------+
    | "regular" |
    +-----------+
    | "small"   |
    +-----------+
    | "mini"    |
    +-----------+
    """

    nsSegmentedControlClass = NSSegmentedControl
    nsSegmentedCellClass = NSSegmentedCell

    frameAdjustments = {
        "mini": (0, -1, 0, 1), #15
        "small": (-2, -4, 2, 5), #20
        "regular": (0, -4, 0, 5), #24
        }

    def __init__(self, posSize, segmentDescriptions, callback=None, selectionStyle="one", sizeStyle="small"):
        self._setupView(self.nsSegmentedControlClass, posSize)
        if self.nsSegmentedCellClass != NSSegmentedCell:
            self._nsObject.setCell_(self.nsSegmentedCellClass.alloc().init())
        if callback is not None:
            self._setCallback(callback)
        self._setSizeStyle(sizeStyle)
        nsObject = self._nsObject
        nsObject.setSegmentCount_(len(segmentDescriptions))
        nsObject.cell().setTrackingMode_(_trackingModeMap[selectionStyle])
        for segmentIndex, segmentDescription in enumerate(segmentDescriptions):
            width = segmentDescription.get("width", 0)
            title = segmentDescription.get("title", "")
            enabled = segmentDescription.get("enabled", True)
            imagePath = segmentDescription.get("imagePath")
            imageNamed = segmentDescription.get("imageNamed")
            imageTemplate = segmentDescription.get("imageTemplate")
            imageObject = segmentDescription.get("imageObject")
            # create the NSImage if needed
            if imagePath is not None:
                image = NSImage.alloc().initWithContentsOfFile_(imagePath)
            elif imageNamed is not None:
                image = NSImage.imageNamed_(imageNamed)
            elif imageObject is not None:
                image = imageObject
            else:
                image = None
            nsObject.setWidth_forSegment_(width, segmentIndex)
            nsObject.setLabel_forSegment_(title, segmentIndex)
            nsObject.setEnabled_forSegment_(enabled, segmentIndex)
            if image is not None:
                if imageTemplate is not None:
                    # only change the image template setting if its either True or False
                    image.setTemplate_(imageTemplate)
                nsObject.setImage_forSegment_(image, segmentIndex)

    def getNSSegmentedButton(self):
        """
        Return the *NSSegmentedButton* that this object wraps.
        """
        return self._nsObject

    def enable(self, onOff):
        """
        Enable or disable the object. **onOff** should be a boolean.
        """
        for index in range(self._nsObject.segmentCount()):
            self._nsObject.setEnabled_forSegment_(onOff, index)

    def set(self, value):
        """
        Set the selected segement. If this control is set to
        `any` mode, `value` should be a list of integers.
        Otherwise `value` should be a single integer.
        """
        # value should be an int unless we are in "any" mode
        if self._nsObject.cell().trackingMode() != _trackingModeMap["any"]:
            value = [value]
        for index in range(self._nsObject.segmentCount()):
            state = index in value
            self._nsObject.setSelected_forSegment_(state, index)

    def get(self):
        """
        Get the selected segement. If this control is set to
        `any` mode, the returned value will be a list of integers.
        Otherwise the returned value will be a single integer.
        """
        states = []
        for index in range(self._nsObject.segmentCount()):
            state = self._nsObject.isSelectedForSegment_(index)
            if state:
                states.append(index)
        if self._nsObject.cell().trackingMode() != _trackingModeMap["any"]:
            return states[0]
        return states