import QtQuick
import QtQuick.Shapes
import ".."

// A square-ish button that renders a stroked SVG-path icon (24x24 viewBox)
// instead of text, matching ActionButton's chrome.
Item {
    id: root

    property string iconPath: ""
    property bool primary: false
    property bool danger: false
    property bool buttonEnabled: true
    signal clicked()

    implicitWidth: 36
    implicitHeight: 30

    Rectangle {
        anchors.fill: parent
        radius: Theme.radius
        opacity: root.buttonEnabled ? 1 : 0.5
        color: !root.buttonEnabled ? Theme.panel
             : root.primary ? (area.containsMouse ? Theme.primaryHover : Theme.primary)
             : (root.danger && area.containsMouse) ? "#C42B1C"
             : area.containsMouse ? Theme.surfaceHigh : Theme.panel
        border.width: root.primary ? 0 : 1
        border.color: (root.danger && area.containsMouse) ? "#C42B1C" : Theme.line
        scale: area.pressed && root.buttonEnabled ? 0.965 : (area.containsMouse && root.buttonEnabled ? 1.015 : 1.0)
        Behavior on color { ColorAnimation { duration: 120 } }
        Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }

        Shape {
            anchors.centerIn: parent
            width: 24
            height: 24
            scale: 16 / 24
            transformOrigin: Item.Center
            antialiasing: true

            ShapePath {
                strokeColor: !root.buttonEnabled ? Theme.inkMuted
                    : root.primary ? Theme.primaryForeground
                    : (root.danger && area.containsMouse) ? "white"
                    : Theme.ink
                strokeWidth: 2
                fillColor: "transparent"
                capStyle: ShapePath.RoundCap
                joinStyle: ShapePath.RoundJoin
                PathSvg { path: root.iconPath }
            }
        }
    }

    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        enabled: root.buttonEnabled
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
