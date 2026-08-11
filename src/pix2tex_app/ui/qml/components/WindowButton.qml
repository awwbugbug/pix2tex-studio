import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: control

    property string role: "minimize"
    property bool maximized: false

    implicitWidth: 46
    implicitHeight: 48
    hoverEnabled: true
    scale: down ? 0.96 : hovered ? 1.012 : 1
    padding: 0

    ToolTip.visible: hovered
    ToolTip.delay: 500
    ToolTip.text: role === "close" ? "关闭" : role === "maximize" ? (maximized ? "还原" : "最大化") : "最小化"

    Behavior on scale { NumberAnimation { duration: 80; easing.type: Easing.OutCubic } }

    background: Rectangle {
        color: {
            if (control.role === "close" && control.hovered) return control.down ? "#A7190F" : "#C42B1C"
            if (control.down) return Theme.surfaceHighest
            return control.hovered ? Theme.surfaceHigh : Theme.surfaceHighClear
        }
        Behavior on color { ColorAnimation { duration: 100 } }
    }

    contentItem: Canvas {
        id: iconCanvas

        antialiasing: true
        onPaint: {
            const ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.strokeStyle = control.role === "close" && control.hovered ? "#FFFFFF" : Theme.inkSoft
            ctx.lineWidth = 1.25
            ctx.lineCap = "square"
            ctx.lineJoin = "miter"

            const cx = width / 2
            const cy = height / 2
            ctx.beginPath()

            if (control.role === "minimize") {
                ctx.moveTo(cx - 5, cy)
                ctx.lineTo(cx + 5, cy)
            } else if (control.role === "close") {
                ctx.moveTo(cx - 4, cy - 4)
                ctx.lineTo(cx + 4, cy + 4)
                ctx.moveTo(cx + 4, cy - 4)
                ctx.lineTo(cx - 4, cy + 4)
            } else if (control.maximized) {
                ctx.rect(cx - 3.5, cy - 5, 8, 8)
                ctx.moveTo(cx + 2.5, cy - 3)
                ctx.lineTo(cx - 5, cy - 3)
                ctx.lineTo(cx - 5, cy + 4.5)
                ctx.lineTo(cx + 2.5, cy + 4.5)
            } else {
                ctx.rect(cx - 5, cy - 5, 10, 10)
            }
            ctx.stroke()
        }

        Connections {
            target: control
            function onHoveredChanged() { iconCanvas.requestPaint() }
            function onDownChanged() { iconCanvas.requestPaint() }
            function onMaximizedChanged() { iconCanvas.requestPaint() }
        }
        Connections { target: Theme; function onDarkChanged() { iconCanvas.requestPaint() } }
    }
}
