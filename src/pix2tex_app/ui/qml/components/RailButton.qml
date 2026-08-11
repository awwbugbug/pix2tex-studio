import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: control

    property string glyph: ""
    property bool selected: false

    implicitWidth: contentRow.implicitWidth + 24
    implicitHeight: 46
    hoverEnabled: true
    scale: down ? 0.97 : hovered ? 1.012 : 1

    Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }

    background: Rectangle {
        color: control.hovered ? Theme.surfaceMid : Theme.surfaceMidClear
        Behavior on color { ColorAnimation { duration: 120 } }

        Rectangle {
            width: parent.width - 18
            height: 2
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            color: Theme.ink
            opacity: control.selected ? 1 : 0
            scale: control.selected ? 1 : 0.45
            Behavior on opacity { NumberAnimation { duration: 150 } }
            Behavior on scale { NumberAnimation { duration: 190; easing.type: Easing.OutCubic } }
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: 3
            color: "transparent"
            border.color: Theme.inkSoft
            border.width: control.visualFocus ? 1 : 0
            radius: Theme.radius
            opacity: control.visualFocus ? 0.7 : 0
            Behavior on opacity { NumberAnimation { duration: 120 } }
        }
    }

    contentItem: Item {
        implicitWidth: contentRow.implicitWidth
        implicitHeight: 20

        Row {
            id: contentRow
            spacing: 6
            anchors.centerIn: parent
            anchors.verticalCenterOffset: 1

            Text {
                height: 20
                text: control.glyph
                color: control.selected ? Theme.ink : Theme.inkSoft
                font.pixelSize: 14
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            Text {
                height: 20
                text: control.text
                color: control.selected ? Theme.ink : Theme.inkSoft
                font.family: Theme.uiFont
                font.pixelSize: 12
                font.weight: control.selected ? Font.DemiBold : Font.Normal
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
