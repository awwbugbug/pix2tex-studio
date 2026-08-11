import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: control

    property bool plus: false

    implicitWidth: 22
    implicitHeight: 22
    hoverEnabled: true
    padding: 0
    scale: down && enabled ? 0.9 : hovered && enabled ? 1.08 : 1

    Behavior on scale { NumberAnimation { duration: 80; easing.type: Easing.OutCubic } }

    background: Rectangle {
        radius: 4
        color: !control.enabled ? Theme.surfaceHighClear : control.down ? Theme.surfaceHighest : control.hovered ? Theme.surfaceHigh : Theme.surfaceHighClear
        Behavior on color { ColorAnimation { duration: 100 } }
    }

    contentItem: Canvas {
        id: stepIcon
        antialiasing: true

        onPaint: {
            const ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            ctx.strokeStyle = control.enabled ? Theme.inkSoft : Theme.inkMuted
            ctx.globalAlpha = control.enabled ? 1 : 0.45
            ctx.lineWidth = 1.35
            ctx.lineCap = "round"
            const cx = width / 2
            const cy = height / 2
            ctx.beginPath()
            ctx.moveTo(cx - 3.5, cy)
            ctx.lineTo(cx + 3.5, cy)
            if (control.plus) {
                ctx.moveTo(cx, cy - 3.5)
                ctx.lineTo(cx, cy + 3.5)
            }
            ctx.stroke()
            ctx.globalAlpha = 1
        }

        Connections {
            target: control
            function onEnabledChanged() { stepIcon.requestPaint() }
            function onHoveredChanged() { stepIcon.requestPaint() }
            function onPlusChanged() { stepIcon.requestPaint() }
        }
        Connections { target: Theme; function onDarkChanged() { stepIcon.requestPaint() } }
    }
}
