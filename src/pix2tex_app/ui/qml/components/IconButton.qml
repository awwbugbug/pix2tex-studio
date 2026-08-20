import QtQuick
import QtQuick.Shapes
import ".."

// A square icon button for the handwriting board. The board is always a white
// canvas, so this uses a FIXED light palette regardless of the app theme:
// white when idle, black when selected, solid grey when disabled — matching the
// light theme so the selected state stays readable on the white surface.
Item {
    id: root

    property string iconPath: ""
    property bool primary: false
    property bool danger: false
    property bool buttonEnabled: true
    signal clicked()

    implicitWidth: 36
    implicitHeight: 30

    readonly property color _panel: "#FFFFFF"
    readonly property color _hover: "#EDEFF1"
    readonly property color _disabled: "#E7E9EB"
    readonly property color _line: "#C6C6CD"
    readonly property color _ink: "#191C1E"
    readonly property color _inkMuted: "#9A9BA1"
    readonly property color _primary: "#111214"
    readonly property color _primaryHover: "#2D3133"
    readonly property color _onPrimary: "#FFFFFF"
    readonly property color _danger: "#C42B1C"

    Rectangle {
        anchors.fill: parent
        radius: Theme.radius
        color: !root.buttonEnabled ? root._disabled
             : root.primary ? (area.containsMouse ? root._primaryHover : root._primary)
             : (root.danger && area.containsMouse) ? root._danger
             : area.containsMouse ? root._hover : root._panel
        border.width: (root.primary && root.buttonEnabled) ? 0 : 1
        border.color: (root.danger && area.containsMouse) ? root._danger : root._line
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
                strokeColor: !root.buttonEnabled ? root._inkMuted
                    : root.primary ? root._onPrimary
                    : (root.danger && area.containsMouse) ? "white"
                    : root._ink
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
