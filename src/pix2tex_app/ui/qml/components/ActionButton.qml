import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: control

    property bool primary: false
    property bool quiet: false
    property bool iconOnly: false
    property bool danger: false
    property string glyph: ""

    implicitHeight: 30
    implicitWidth: iconOnly ? 30 : Math.max(58, contentRow.implicitWidth + 20)
    hoverEnabled: true
    scale: down && enabled ? 0.965 : hovered && enabled ? 1.015 : 1.0
    opacity: enabled ? 1 : 0.64

    Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
    Behavior on opacity { NumberAnimation { duration: 120 } }

    background: Rectangle {
        radius: Theme.radius
        color: {
            if (!control.enabled) return control.quiet ? Theme.surfaceHighClear : Theme.surfaceLow
            if (control.danger && control.hovered) return "#C42B1C"
            if (control.primary) return control.hovered ? Theme.primaryHover : Theme.primary
            if (control.quiet) return control.hovered ? Theme.surfaceHigh : Theme.surfaceHighClear
            if (control.down) return Theme.surfaceHighest
            return control.hovered ? Theme.surfaceHigh : Theme.panel
        }
        border.width: control.visualFocus ? 1 : control.primary || control.quiet || (control.danger && control.hovered) ? 0 : 1
        border.color: control.visualFocus ? Theme.inkSoft : Theme.line
        Behavior on color { ColorAnimation { duration: 120 } }
        Behavior on border.color { ColorAnimation { duration: 120 } }
    }

    contentItem: Item {
        implicitWidth: contentRow.implicitWidth
        implicitHeight: contentRow.implicitHeight

        Row {
            id: contentRow
            spacing: control.iconOnly || control.glyph.length === 0 ? 0 : 7
            anchors.centerIn: parent

            Text {
                width: visible ? implicitWidth : 0
                height: 18
                visible: control.glyph.length > 0
                text: control.glyph
                color: !control.enabled ? Theme.inkMuted
                     : control.danger && control.hovered ? "white"
                     : control.primary ? Theme.primaryForeground : Theme.ink
                font.family: Theme.uiFont
                font.pixelSize: 14
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            Text {
                width: visible ? implicitWidth : 0
                height: 18
                visible: !control.iconOnly && control.text.length > 0
                text: control.text
                color: !control.enabled ? Theme.inkMuted
                     : control.danger && control.hovered ? "white"
                     : control.primary ? Theme.primaryForeground : Theme.ink
                font.family: Theme.uiFont
                font.pixelSize: 11
                font.weight: control.primary ? Font.DemiBold : Font.Normal
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
