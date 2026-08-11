import QtQuick
import ".."

Rectangle {
    id: root

    property string state: "warming"
    property string label: "准备中"

    readonly property color stateColor: state === "ready" ? Theme.success
                                         : state === "busy" || state === "warming" ? Theme.warning
                                         : state === "preview" ? Theme.inkMuted
                                         : Theme.danger

    implicitWidth: row.implicitWidth + 18
    implicitHeight: 28
    radius: Theme.radius
    color: Theme.panel
    border.color: Theme.line

    Row {
        id: row
        anchors.centerIn: parent
        spacing: 7

        Rectangle {
            width: 6
            height: 6
            radius: 3
            color: root.stateColor
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: root.label
            color: Theme.inkSoft
            font.family: Theme.uiFont
            font.pixelSize: 10
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
