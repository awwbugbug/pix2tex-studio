import QtQuick
import QtQuick.Controls
import ".."

Button {
    id: control

    property bool dark: false

    implicitWidth: 30
    implicitHeight: 30
    hoverEnabled: true
    padding: 0
    scale: down ? 0.94 : hovered ? 1.04 : 1

    ToolTip.visible: hovered
    ToolTip.delay: 500
    ToolTip.text: dark ? "切换到亮色" : "切换到暗色"

    Behavior on scale { NumberAnimation { duration: 100; easing.type: Easing.OutCubic } }

    background: Rectangle {
        radius: Theme.radius
        color: control.down ? Theme.surfaceHighest : control.hovered ? Theme.surfaceHigh : Theme.panel
        border.color: Theme.line
        Behavior on color { ColorAnimation { duration: 150 } }
        Behavior on border.color { ColorAnimation { duration: 150 } }
    }

    contentItem: Item {
        rotation: control.dark ? 0 : -16
        Behavior on rotation { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

        Canvas {
            id: themeIcon
            anchors.fill: parent
            antialiasing: true

            onPaint: {
                const ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                const cx = width / 2
                const cy = height / 2
                ctx.strokeStyle = Theme.ink
                ctx.fillStyle = Theme.ink
                ctx.lineWidth = 1.35
                ctx.lineCap = "round"

                if (control.dark) {
                    ctx.beginPath()
                    ctx.arc(cx, cy, 3.2, 0, Math.PI * 2)
                    ctx.stroke()
                    for (let i = 0; i < 8; i++) {
                        const a = i * Math.PI / 4
                        ctx.beginPath()
                        ctx.moveTo(cx + Math.cos(a) * 5.3, cy + Math.sin(a) * 5.3)
                        ctx.lineTo(cx + Math.cos(a) * 7.1, cy + Math.sin(a) * 7.1)
                        ctx.stroke()
                    }
                } else {
                    ctx.beginPath()
                    ctx.arc(cx - 0.8, cy, 6.1, 0, Math.PI * 2)
                    ctx.fill()
                    ctx.globalCompositeOperation = "destination-out"
                    ctx.beginPath()
                    ctx.arc(cx + 2.3, cy - 2.1, 5.7, 0, Math.PI * 2)
                    ctx.fill()
                    ctx.globalCompositeOperation = "source-over"
                }
            }

            Connections { target: control; function onDarkChanged() { themeIcon.requestPaint() } }
            Connections { target: Theme; function onDarkChanged() { themeIcon.requestPaint() } }
        }
    }
}
