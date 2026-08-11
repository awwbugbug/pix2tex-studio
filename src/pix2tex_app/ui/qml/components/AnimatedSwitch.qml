import QtQuick
import QtQuick.Controls
import ".."

Switch {
    id: control

    implicitWidth: 38
    implicitHeight: 24
    hoverEnabled: true
    padding: 0
    scale: down && enabled ? 0.94 : 1
    opacity: enabled ? 1 : 0.48

    Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on opacity { NumberAnimation { duration: 120 } }

    indicator: Rectangle {
        x: 2
        y: (control.height - height) / 2
        width: 34
        height: 18
        radius: 9
        color: control.checked ? Theme.primary : control.hovered ? Theme.surfaceHighest : Theme.surfaceHigh
        border.color: control.checked ? Theme.primary : Theme.line
        Behavior on color { ColorAnimation { duration: 150 } }
        Behavior on border.color { ColorAnimation { duration: 150 } }

        Rectangle {
            width: 14
            height: 14
            radius: 7
            y: 2
            x: control.checked ? parent.width - width - 2 : 2
            color: control.checked ? Theme.switchKnob : Theme.inkSoft
            Behavior on x { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }
            Behavior on color { ColorAnimation { duration: 140 } }
        }
    }

    contentItem: Item { }
}
