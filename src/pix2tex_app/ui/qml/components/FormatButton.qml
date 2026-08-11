import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: control

    property bool selected: false

    implicitHeight: 23
    implicitWidth: Math.max(40, label.implicitWidth + 16)
    hoverEnabled: true
    scale: down ? 0.96 : hovered ? 1.018 : 1

    Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }

    background: Rectangle {
        radius: 3
        color: control.selected ? Theme.panel : control.hovered ? Theme.surfaceHigh : Theme.surfaceHighClear
        border.width: control.selected || control.visualFocus ? 1 : 0
        border.color: control.visualFocus ? Theme.inkSoft : Theme.line
        Behavior on color { ColorAnimation { duration: 110 } }
        Behavior on border.color { ColorAnimation { duration: 110 } }
    }

    contentItem: Text {
        id: label
        text: control.text
        color: control.selected ? Theme.ink : Theme.inkMuted
        font.family: Theme.uiFont
        font.pixelSize: 10
        font.weight: control.selected ? Font.DemiBold : Font.Normal
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
