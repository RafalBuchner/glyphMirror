from AppKit import NSColor, NSTextField, NSKeyDownMask, NSEvent, NSUpArrowFunctionKey, NSDownArrowFunctionKey, NSCommandKeyMask, NSShiftKeyMask
from vanilla.vanillaBase import VanillaCallbackWrapper
digits_dot_minus = "1234567890.-"
from vanilla import EditText

class RBNSTextField(NSTextField):
    def keyUp_(self, event):
        if event.characters() == NSUpArrowFunctionKey or event.characters() == NSDownArrowFunctionKey:
            shiftDown = NSEvent.modifierFlags() & NSShiftKeyMask
            commandDown = NSEvent.modifierFlags() & NSCommandKeyMask
            value = 1
            if event.characters() == NSDownArrowFunctionKey: value *= -1
            if shiftDown: value *= 10
            if commandDown and shiftDown: value *= 10
            # if "End" in selector or "Right" in selector or "Left" in selector or "Beggining" in selector or "deleteBackward" in selector: return False

            strValue = self.stringValue()
            strValue = strValue.replace(",",".")
            # print(strValue)
            for chr in strValue:
                if chr not in digits_dot_minus:
                    return True
            floatValue = float(strValue)
            floatValue += value
            floatValue = round(floatValue, 3)
            if floatValue % 1 != 0:
                strValue = floatValue
            else:
                strValue = int(floatValue)

            self.setStringValue_(str(strValue))
            # print(self.delegate())
            self.delegate().action_(self)

class RBEditText(EditText):
    nsTextFieldClass = RBNSTextField

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
