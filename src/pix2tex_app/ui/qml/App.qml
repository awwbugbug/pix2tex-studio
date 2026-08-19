pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "components"

ApplicationWindow {
    id: window

    width: 980
    height: 640
    minimumWidth: 820
    minimumHeight: 540
    visible: true
    title: "pix2tex"
    color: Theme.surface
    flags: Qt.Window | Qt.FramelessWindowHint

    property int pageIndex: 0
    property int editorIndex: 0
    property real imageScale: 1.0
    property bool drawMode: false
    property string pendingWindowAction: ""
    property bool restoringFromMinimized: false
    readonly property bool maximized: visibility === Window.Maximized

    onClosing: function(close) {
        if (desktopIntegration.shouldHideOnClose()) {
            close.accepted = false
            desktopIntegration.hideToTray()
        }
    }

    onVisibilityChanged: function() {
        if (window.visibility === Window.Minimized) {
            restoringFromMinimized = true
        } else if (restoringFromMinimized) {
            restoringFromMinimized = false
            windowSurface.opacity = 0.72
            windowSurface.scale = 0.982
            restoreTransition.restart()
        }
    }

    function changePage(index) {
        pageIndex = index
    }

    function activeEditor() {
        return editorIndex === 0 ? rawEditor : formattedEditor
    }

    function runWindowAction(action) {
        if (windowTransition.running)
            return
        pendingWindowAction = action
        windowTransition.start()
    }

    SequentialAnimation {
        id: windowTransition

        ParallelAnimation {
            NumberAnimation { target: windowSurface; property: "opacity"; to: 0.78; duration: 85; easing.type: Easing.InCubic }
            NumberAnimation { target: windowSurface; property: "scale"; to: 0.985; duration: 85; easing.type: Easing.InCubic }
        }
        ScriptAction {
            script: {
                if (window.pendingWindowAction === "minimize") {
                    windowSurface.opacity = 1
                    windowSurface.scale = 1
                    window.showMinimized()
                } else if (window.pendingWindowAction === "maximize") {
                    window.maximized ? window.showNormal() : window.showMaximized()
                } else if (window.pendingWindowAction === "close") {
                    window.close()
                }
            }
        }
        ParallelAnimation {
            NumberAnimation { target: windowSurface; property: "opacity"; to: 1; duration: 150; easing.type: Easing.OutCubic }
            NumberAnimation { target: windowSurface; property: "scale"; to: 1; duration: 170; easing.type: Easing.OutCubic }
        }
    }

    ParallelAnimation {
        id: restoreTransition
        NumberAnimation { target: windowSurface; property: "opacity"; to: 1; duration: 170; easing.type: Easing.OutCubic }
        NumberAnimation { target: windowSurface; property: "scale"; to: 1; duration: 190; easing.type: Easing.OutCubic }
    }

    Component.onCompleted: Theme.dark = appController.darkMode

    Connections {
        target: appController
        function onThemeModeChanged() { Theme.dark = appController.darkMode }
        function onImageUrlChanged() {
            window.imageScale = 1
            sourceFlick.contentX = 0
            sourceFlick.contentY = 0
        }
    }

    Shortcut {
        sequence: "Ctrl+A"
        context: Qt.ApplicationShortcut
        enabled: appController.globalHotkey !== "Ctrl+A"
                 && !rawEditor.activeFocus
                 && !formattedEditor.activeFocus
        onActivated: appController.captureFormula()
    }

    Rectangle {
        id: windowSurface
        anchors.fill: parent
        color: Theme.surface
        transformOrigin: Item.Center
        Behavior on color { ColorAnimation { duration: 180 } }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Rectangle {
                id: titleBar
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                color: Theme.surface
                border.color: Theme.line
                border.width: 1

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton
                    onPressed: window.startSystemMove()
                    onDoubleClicked: window.runWindowAction("maximize")
                }

                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: 16
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 8

                    Text {
                        text: "∫"
                        color: Theme.ink
                        font.family: Theme.mathFont
                        font.pixelSize: 23
                        font.italic: true
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        text: "pix2tex"
                        color: Theme.ink
                        font.family: Theme.uiFont
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        font.letterSpacing: -0.3
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Row {
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: 1
                    height: 46
                    RailButton { text: "识别"; glyph: "⌗"; selected: window.pageIndex === 0; onClicked: window.changePage(0) }
                    RailButton { text: "历史"; glyph: "▤"; selected: window.pageIndex === 1; onClicked: window.changePage(1) }
                    RailButton { text: "设置"; glyph: "⚙"; selected: window.pageIndex === 2; onClicked: window.changePage(2) }
                }

                Row {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    height: parent.height
                    spacing: 6

                    StatusPill {
                        anchors.verticalCenter: parent.verticalCenter
                        state: appController.engineState
                        label: appController.engineState === "ready" ? "CPU 已就绪" : appController.engineDetail
                    }

                    ThemeToggleButton {
                        anchors.verticalCenter: parent.verticalCenter
                        dark: Theme.dark
                        onClicked: appController.setThemeMode(Theme.dark ? "light" : "dark")
                    }

                    Item { width: 2; height: 1 }

                    Row {
                        height: titleBar.height
                        spacing: 0

                        WindowButton {
                            role: "minimize"
                            height: titleBar.height
                            onClicked: window.runWindowAction("minimize")
                        }
                        WindowButton {
                            role: "maximize"
                            maximized: window.maximized
                            height: titleBar.height
                            onClicked: window.runWindowAction("maximize")
                        }
                        WindowButton {
                            role: "close"
                            height: titleBar.height
                            onClicked: window.runWindowAction("close")
                        }
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                Item {
                    id: recognitionPage
                    anchors.fill: parent
                    opacity: window.pageIndex === 0 ? 1 : 0
                    y: window.pageIndex === 0 ? 0 : 7
                    visible: opacity > 0
                    enabled: window.pageIndex === 0
                    Behavior on opacity { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }
                    Behavior on y { NumberAnimation { duration: 210; easing.type: Easing.OutCubic } }

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 16

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.minimumWidth: 340
                            color: Theme.panel
                            radius: Theme.radius
                            border.color: Theme.line
                            clip: true

                            ColumnLayout {
                                anchors.fill: parent
                                spacing: 0

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 36
                                    color: Theme.surfaceLow
                                    border.color: Theme.line

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 12
                                        anchors.rightMargin: 8
                                        spacing: 8

                                        Text { text: "原始图像"; color: Theme.ink; font.family: Theme.uiFont; font.pixelSize: 12; font.weight: Font.DemiBold }
                                        Text {
                                            Layout.fillWidth: true
                                            text: appController.imageName
                                            color: Theme.inkMuted
                                            font.family: Theme.monoFont
                                            font.pixelSize: 9
                                            elide: Text.ElideMiddle
                                        }
                                        ActionButton { iconOnly: true; quiet: true; glyph: "−"; enabled: appController.imageUrl.length > 0 && window.imageScale > 0.4; onClicked: window.imageScale = Math.max(0.4, window.imageScale - 0.1) }
                                        Text { text: Math.round(window.imageScale * 100) + "%"; color: Theme.inkMuted; font.family: Theme.monoFont; font.pixelSize: 9 }
                                        ActionButton { iconOnly: true; quiet: true; glyph: "+"; enabled: appController.imageUrl.length > 0 && window.imageScale < 3; onClicked: window.imageScale = Math.min(3, window.imageScale + 0.1) }
                                    }
                                }

                                Item {
                                    id: sourceStage
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true

                                    Rectangle { anchors.fill: parent; color: Theme.surfaceMid }

                                    Canvas {
                                        id: gridCanvas
                                        anchors.fill: parent
                                        opacity: 0.55
                                        onPaint: {
                                            const ctx = getContext("2d")
                                            ctx.clearRect(0, 0, width, height)
                                            ctx.strokeStyle = Theme.line
                                            ctx.lineWidth = 1
                                            for (let x = 0; x < width; x += 24) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke() }
                                            for (let y = 0; y < height; y += 24) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke() }
                                        }
                                        Connections { target: Theme; function onDarkChanged() { gridCanvas.requestPaint() } }
                                    }

                                    Column {
                                        anchors.centerIn: parent
                                        width: Math.min(370, parent.width - 48)
                                        spacing: 13
                                        visible: appController.imageUrl.length === 0
                                        opacity: visible ? 1 : 0

                                        Rectangle {
                                            width: 42; height: 42; anchors.horizontalCenter: parent.horizontalCenter
                                            color: Theme.surfaceLow; border.color: Theme.line; radius: Theme.radius
                                            Text { anchors.centerIn: parent; text: "⌗"; color: Theme.inkSoft; font.pixelSize: 20 }
                                        }
                                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "截取或导入公式"; color: Theme.ink; font.family: Theme.uiFont; font.pixelSize: 17; font.weight: Font.DemiBold }
                                        Text {
                                            width: parent.width
                                            horizontalAlignment: Text.AlignHCenter
                                            text: "框选屏幕中的公式图片，识别过程完全在本机进行。"
                                            color: Theme.inkMuted
                                            font.family: Theme.uiFont
                                            font.pixelSize: 11
                                            wrapMode: Text.WordWrap
                                        }
                                        Row {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            spacing: 7
                                            ActionButton { text: "区域截图"; primary: true; onClicked: appController.captureFormula() }
                                            ActionButton { text: "打开图片"; onClicked: appController.openImage() }
                                            ActionButton { text: "粘贴图片"; onClicked: appController.pasteImage() }
                                        }
                                        Text { anchors.horizontalCenter: parent.horizontalCenter; text: "Ctrl + A"; color: Theme.inkMuted; font.family: Theme.monoFont; font.pixelSize: 9 }
                                    }

                                    Flickable {
                                        id: sourceFlick
                                        objectName: "sourceFlick"
                                        anchors.fill: parent
                                        visible: appController.imageUrl.length > 0
                                        contentWidth: Math.max(width, imageItem.width)
                                        contentHeight: Math.max(height, imageItem.height)
                                        clip: true
                                        boundsBehavior: Flickable.StopAtBounds
                                        interactive: contentWidth > width || contentHeight > height

                                        property bool wheelZoomActive: false
                                        property real wheelAnchorX: 0.5
                                        property real wheelAnchorY: 0.5
                                        property real wheelCursorX: width / 2
                                        property real wheelCursorY: height / 2

                                        function keepWheelAnchor() {
                                            if (!wheelZoomActive || imageItem.width <= 0 || imageItem.height <= 0)
                                                return
                                            const targetX = imageItem.x + wheelAnchorX * imageItem.width - wheelCursorX
                                            const targetY = imageItem.y + wheelAnchorY * imageItem.height - wheelCursorY
                                            contentX = Math.max(0, Math.min(Math.max(0, contentWidth - width), targetX))
                                            contentY = Math.max(0, Math.min(Math.max(0, contentHeight - height), targetY))
                                        }

                                        function zoomAt(position, wheelDelta) {
                                            if (appController.imageUrl.length === 0 || imageItem.width <= 0 || imageItem.height <= 0)
                                                return
                                            const imagePointX = contentX + position.x - imageItem.x
                                            const imagePointY = contentY + position.y - imageItem.y
                                            wheelAnchorX = Math.max(0, Math.min(1, imagePointX / imageItem.width))
                                            wheelAnchorY = Math.max(0, Math.min(1, imagePointY / imageItem.height))
                                            wheelCursorX = position.x
                                            wheelCursorY = position.y
                                            wheelZoomActive = true
                                            const factor = Math.pow(1.1, wheelDelta / 120)
                                            window.imageScale = Math.max(0.4, Math.min(3, window.imageScale * factor))
                                            wheelZoomFinish.restart()
                                            Qt.callLater(keepWheelAnchor)
                                        }

                                        onContentWidthChanged: Qt.callLater(keepWheelAnchor)
                                        onContentHeightChanged: Qt.callLater(keepWheelAnchor)

                                        Timer {
                                            id: wheelZoomFinish
                                            interval: 230
                                            onTriggered: sourceFlick.wheelZoomActive = false
                                        }

                                        WheelHandler {
                                            id: imageZoomWheel
                                            target: null
                                            orientation: Qt.Vertical
                                            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                                            onWheel: event => {
                                                let delta = event.angleDelta.y !== 0
                                                    ? event.angleDelta.y
                                                    : event.pixelDelta.y * 4
                                                if (event.inverted)
                                                    delta = -delta
                                                sourceFlick.zoomAt(imageZoomWheel.point.position, delta)
                                                event.accepted = true
                                            }
                                        }

                                        Image {
                                            id: imageItem
                                            source: appController.imageUrl
                                            readonly property real fitScale: Math.min(
                                                sourceFlick.width / Math.max(1, sourceSize.width),
                                                sourceFlick.height / Math.max(1, sourceSize.height)
                                            )
                                            width: Math.max(1, sourceSize.width * fitScale * window.imageScale)
                                            height: Math.max(1, sourceSize.height * fitScale * window.imageScale)
                                            x: Math.max(0, (sourceFlick.contentWidth - width) / 2)
                                            y: Math.max(0, (sourceFlick.contentHeight - height) / 2)
                                            fillMode: Image.Stretch
                                            smooth: true
                                            mipmap: true
                                            cache: false
                                            Behavior on width { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                                            Behavior on height { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                                        }
                                    }

                                    Item {
                                        id: drawBoard
                                        objectName: "drawBoard"
                                        anchors.fill: parent
                                        visible: window.drawMode
                                        z: 50

                                        property var strokes: []
                                        property var activeStroke: []
                                        property real penWidth: 3
                                        property real eraserWidth: 18
                                        property bool erasing: false

                                        onVisibleChanged: if (visible) erasing = false

                                        function repaint() { inkCanvas.requestPaint() }
                                        function clearBoard() { strokes = []; activeStroke = []; repaint() }
                                        function undo() { var a = strokes.slice(); a.pop(); strokes = a; repaint() }
                                        function recognize() {
                                            inkSurface.grabToImage(function(result) {
                                                var path = appController.canvasImagePath()
                                                if (result.saveToFile(path)) {
                                                    appController.openPath(path)
                                                    window.drawMode = false
                                                }
                                            })
                                        }

                                        Item {
                                            id: inkSurface
                                            anchors.fill: parent

                                            Rectangle { anchors.fill: parent; color: "white" }

                                            Canvas {
                                                id: inkCanvas
                                                anchors.fill: parent
                                                onPaint: {
                                                    const ctx = getContext("2d")
                                                    ctx.clearRect(0, 0, width, height)
                                                    ctx.lineCap = "round"
                                                    ctx.lineJoin = "round"
                                                    const strokes = drawBoard.strokes
                                                    for (let s = 0; s <= strokes.length; ++s) {
                                                        const active = s === strokes.length
                                                        const pts = active ? drawBoard.activeStroke : strokes[s].points
                                                        const erase = active ? drawBoard.erasing : strokes[s].erase
                                                        if (!pts || pts.length === 0) continue
                                                        const w = erase ? drawBoard.eraserWidth : drawBoard.penWidth
                                                        ctx.strokeStyle = erase ? "white" : "black"
                                                        ctx.fillStyle = erase ? "white" : "black"
                                                        ctx.lineWidth = w
                                                        if (pts.length === 1) {
                                                            ctx.beginPath()
                                                            ctx.arc(pts[0].x, pts[0].y, w / 2, 0, 2 * Math.PI)
                                                            ctx.fill()
                                                            continue
                                                        }
                                                        ctx.beginPath()
                                                        ctx.moveTo(pts[0].x, pts[0].y)
                                                        for (let i = 1; i < pts.length; ++i) ctx.lineTo(pts[i].x, pts[i].y)
                                                        ctx.stroke()
                                                    }
                                                }
                                            }

                                            MouseArea {
                                                id: drawArea
                                                objectName: "drawArea"
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: drawBoard.erasing ? Qt.BlankCursor : Qt.CrossCursor
                                                onPressed: mouse => { drawBoard.activeStroke = [{ x: mouse.x, y: mouse.y }]; inkCanvas.requestPaint() }
                                                onPositionChanged: mouse => {
                                                    if (!pressed) return
                                                    var s = drawBoard.activeStroke.slice()
                                                    s.push({ x: mouse.x, y: mouse.y })
                                                    drawBoard.activeStroke = s
                                                    inkCanvas.requestPaint()
                                                }
                                                onReleased: {
                                                    if (drawBoard.activeStroke.length > 0) {
                                                        var a = drawBoard.strokes.slice()
                                                        a.push({ points: drawBoard.activeStroke, erase: drawBoard.erasing })
                                                        drawBoard.strokes = a
                                                        drawBoard.activeStroke = []
                                                        inkCanvas.requestPaint()
                                                    }
                                                }
                                            }

                                            Rectangle {
                                                id: eraserCursor
                                                visible: drawBoard.erasing && drawArea.containsMouse
                                                width: drawBoard.eraserWidth
                                                height: drawBoard.eraserWidth
                                                radius: width / 2
                                                color: "transparent"
                                                border.color: "#7A7A7A"
                                                border.width: 1
                                                x: drawArea.mouseX - width / 2
                                                y: drawArea.mouseY - height / 2
                                                z: 5
                                            }
                                        }

                                        Row {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            anchors.bottom: parent.bottom
                                            anchors.bottomMargin: 12
                                            spacing: 8
                                            IconButton {
                                                iconPath: "M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z M15 5l4 4"
                                                primary: !drawBoard.erasing
                                                onClicked: drawBoard.erasing = false
                                            }
                                            IconButton {
                                                iconPath: "m7 21-4.3-4.3c-1-1-1-2.5 0-3.4l9.6-9.6c1-1 2.5-1 3.4 0l5.6 5.6c1 1 1 2.5 0 3.4L13 21 M22 21H7 M5 11l9 9"
                                                primary: drawBoard.erasing
                                                onClicked: drawBoard.erasing = true
                                            }
                                            IconButton {
                                                iconPath: "M9 14 4 9l5-5 M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"
                                                buttonEnabled: drawBoard.strokes.length > 0
                                                onClicked: drawBoard.undo()
                                            }
                                            IconButton {
                                                iconPath: "M3 6h18 M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6 M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2 M10 11V17 M14 11V17"
                                                danger: true
                                                buttonEnabled: drawBoard.strokes.length > 0
                                                onClicked: drawBoard.clearBoard()
                                            }
                                            IconButton {
                                                objectName: "drawRecognizeButton"
                                                iconPath: "M3 7V5a2 2 0 0 1 2-2h2 M17 3h2a2 2 0 0 1 2 2v2 M21 17v2a2 2 0 0 1-2 2h-2 M7 21H5a2 2 0 0 1-2-2v-2 M7 12h10"
                                                primary: true
                                                buttonEnabled: drawBoard.strokes.length > 0 && !appController.busy
                                                onClicked: drawBoard.recognize()
                                            }
                                        }
                                    }

                                    DropArea {
                                        id: sourceDropArea
                                        anchors.fill: parent
                                        onDropped: drop => {
                                            if (drop.urls.length > 0) appController.openPath(drop.urls[0])
                                        }
                                    }

                                    Rectangle {
                                        anchors.fill: parent
                                        color: "transparent"
                                        border.color: Theme.ink
                                        border.width: sourceDropArea.containsDrag ? 2 : 0
                                        opacity: sourceDropArea.containsDrag ? 0.75 : 0
                                        Behavior on opacity { NumberAnimation { duration: 120 } }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 42
                                    color: Theme.surfaceLow
                                    border.color: Theme.line

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 8
                                        anchors.rightMargin: 8
                                        spacing: 6

                                        ActionButton {
                                            text: appController.busy ? "中断" : "区域截图"
                                            glyph: appController.busy ? "■" : "⌗"
                                            primary: true
                                            onClicked: appController.captureFormula()
                                        }
                                        ActionButton { text: "重试"; enabled: appController.imageUrl.length > 0 && !appController.busy; onClicked: appController.predictCurrent() }
                                        ActionButton { text: "清空"; enabled: appController.imageUrl.length > 0 && !appController.busy; onClicked: appController.clearImage() }
                                        Item { Layout.fillWidth: true }

                                        Rectangle {
                                            id: penToggle
                                            Layout.preferredWidth: 30
                                            Layout.preferredHeight: 30
                                            radius: Theme.radius
                                            color: window.drawMode ? (penMouse.containsMouse ? Theme.primaryHover : Theme.primary)
                                                                   : (penMouse.containsMouse ? Theme.surfaceHigh : Theme.panel)
                                            border.width: window.drawMode ? 0 : 1
                                            border.color: Theme.line
                                            scale: penMouse.pressed ? 0.965 : penMouse.containsMouse ? 1.015 : 1.0
                                            Behavior on color { ColorAnimation { duration: 120 } }
                                            Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }

                                            Canvas {
                                                id: penIcon
                                                anchors.centerIn: parent
                                                width: 20
                                                height: 20
                                                // upright while drawing, tilted at rest
                                                rotation: window.drawMode ? 0 : 40
                                                Behavior on rotation { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }
                                                onPaint: {
                                                    const ctx = getContext("2d")
                                                    ctx.clearRect(0, 0, width, height)
                                                    ctx.strokeStyle = window.drawMode ? Theme.primaryForeground : Theme.ink
                                                    ctx.lineWidth = 1.0
                                                    ctx.lineCap = "round"
                                                    ctx.lineJoin = "round"
                                                    // slim pencil outline: eraser end, body, tip
                                                    ctx.beginPath()
                                                    ctx.moveTo(8, 3.5)
                                                    ctx.lineTo(12, 3.5)
                                                    ctx.lineTo(12, 13)
                                                    ctx.lineTo(10, 17)
                                                    ctx.lineTo(8, 13)
                                                    ctx.closePath()
                                                    ctx.stroke()
                                                    // collar line at the tip base
                                                    ctx.beginPath()
                                                    ctx.moveTo(8, 13)
                                                    ctx.lineTo(12, 13)
                                                    ctx.stroke()
                                                }
                                                Connections { target: window; function onDrawModeChanged() { penIcon.requestPaint() } }
                                                Connections { target: Theme; function onDarkChanged() { penIcon.requestPaint() } }
                                            }

                                            MouseArea {
                                                id: penMouse
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: window.drawMode = !window.drawMode
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.minimumWidth: 390
                            spacing: 16

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                Layout.minimumHeight: 190
                                color: Theme.panel
                                radius: Theme.radius
                                border.color: Theme.line
                                clip: true

                                ColumnLayout {
                                    anchors.fill: parent
                                    spacing: 0

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 36
                                        color: Theme.surfaceLow
                                        border.color: Theme.line
                                        RowLayout {
                                            anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 7
                                            Text { text: "公式预览"; color: Theme.ink; font.family: Theme.uiFont; font.pixelSize: 12; font.weight: Font.DemiBold }
                                            Item { Layout.fillWidth: true }
                                            ActionButton { iconOnly: true; quiet: true; glyph: "⧉"; enabled: appController.latex.length > 0; onClicked: appController.copyLatex() }
                                        }
                                    }

                                    Item {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true

                                        Column {
                                            anchors.centerIn: parent
                                            spacing: 8
                                            visible: appController.latex.length === 0
                                            Text { anchors.horizontalCenter: parent.horizontalCenter; text: "∫"; color: Theme.inkMuted; font.family: Theme.mathFont; font.pixelSize: 28 }
                                            Text { text: appController.imageUrl.length > 0 ? "识别完成后在此渲染公式" : "导入图片后显示识别结果"; color: Theme.inkMuted; font.family: Theme.uiFont; font.pixelSize: 11 }
                                        }

                                        Loader {
                                            anchors.fill: parent
                                            active: appController.latex.length > 0
                                            sourceComponent: FormulaPreview {
                                                latex: appController.latex
                                                dark: Theme.dark
                                            }
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                Layout.minimumHeight: 230
                                color: Theme.panel
                                radius: Theme.radius
                                border.color: Theme.line
                                clip: true

                                ColumnLayout {
                                    anchors.fill: parent
                                    spacing: 0

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 36
                                        color: Theme.surfaceLow
                                        border.color: Theme.line

                                        RowLayout {
                                            anchors.fill: parent; anchors.leftMargin: 5; anchors.rightMargin: 7; spacing: 2
                                            FormatButton { text: "原始预测"; selected: window.editorIndex === 0; onClicked: window.editorIndex = 0 }
                                            FormatButton { text: "格式化输出"; selected: window.editorIndex === 1; onClicked: window.editorIndex = 1 }
                                            Item { Layout.fillWidth: true }
                                            ActionButton { iconOnly: true; quiet: true; glyph: "⧉"; enabled: appController.latex.length > 0; onClicked: appController.copyLatex() }
                                            ActionButton { iconOnly: true; quiet: true; glyph: "↶"; enabled: window.activeEditor().canUndo; onClicked: window.activeEditor().undo() }
                                            ActionButton { iconOnly: true; quiet: true; glyph: "↷"; enabled: window.activeEditor().canRedo; onClicked: window.activeEditor().redo() }
                                        }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 32
                                        color: Theme.surfaceLow
                                        border.color: Theme.line
                                        RowLayout {
                                            anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 6; spacing: 3
                                            Text { text: "输出格式"; color: Theme.inkMuted; font.family: Theme.uiFont; font.pixelSize: 9 }
                                            Item { Layout.fillWidth: true }
                                            FormatButton { text: "Raw"; selected: appController.formatMode === "raw"; onClicked: { appController.setFormatMode("raw"); window.editorIndex = 1 } }
                                            FormatButton { text: "LaTeX-$"; selected: appController.formatMode === "latex-inline"; onClicked: { appController.setFormatMode("latex-inline"); window.editorIndex = 1 } }
                                            FormatButton { text: "LaTeX-$$"; selected: appController.formatMode === "latex-display"; onClicked: { appController.setFormatMode("latex-display"); window.editorIndex = 1 } }
                                            FormatButton { text: "SymPy"; selected: appController.formatMode === "sympy"; onClicked: { appController.setFormatMode("sympy"); window.editorIndex = 1 } }
                                        }
                                    }

                                    Item {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        Rectangle { anchors.fill: parent; color: Theme.editor }
                                        Rectangle { width: 34; anchors.top: parent.top; anchors.bottom: parent.bottom; color: Theme.editorRail; border.color: Theme.editorLine }
                                        Text { x: 17; y: 10; text: "1"; color: Theme.editorMuted; font.family: Theme.monoFont; font.pixelSize: 10 }

                                        TextArea {
                                            id: rawEditor
                                            anchors.left: parent.left; anchors.leftMargin: 35; anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
                                            visible: opacity > 0
                                            opacity: window.editorIndex === 0 ? 1 : 0
                                            enabled: window.editorIndex === 0
                                            color: Theme.editorText
                                            placeholderText: "模型的原始预测将显示在这里"
                                            placeholderTextColor: Theme.editorMuted
                                            font.family: Theme.monoFont
                                            font.pixelSize: 11
                                            wrapMode: TextEdit.WrapAnywhere
                                            padding: 10
                                            background: Rectangle {
                                                color: rawEditor.activeFocus ? Qt.rgba(1, 1, 1, 0.025) : "transparent"
                                                border.color: Theme.editorLine
                                                border.width: rawEditor.activeFocus ? 1 : 0
                                                Behavior on color { ColorAnimation { duration: 120 } }
                                                Behavior on border.width { NumberAnimation { duration: 100 } }
                                            }
                                            Component.onCompleted: text = appController.latex
                                            onTextChanged: if (activeFocus && text !== appController.latex) appController.setLatex(text)
                                            Behavior on opacity { NumberAnimation { duration: 140 } }
                                            Connections { target: appController; function onLatexChanged() { if (rawEditor.text !== appController.latex) rawEditor.text = appController.latex } }
                                        }

                                        TextArea {
                                            id: formattedEditor
                                            anchors.left: parent.left; anchors.leftMargin: 35; anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
                                            visible: opacity > 0
                                            opacity: window.editorIndex === 1 ? 1 : 0
                                            enabled: window.editorIndex === 1
                                            color: Theme.editorText
                                            placeholderText: "按所选格式生成的输出将显示在这里"
                                            placeholderTextColor: Theme.editorMuted
                                            font.family: Theme.monoFont
                                            font.pixelSize: 11
                                            wrapMode: TextEdit.WrapAnywhere
                                            padding: 10
                                            background: Rectangle {
                                                color: formattedEditor.activeFocus ? Qt.rgba(1, 1, 1, 0.025) : "transparent"
                                                border.color: Theme.editorLine
                                                border.width: formattedEditor.activeFocus ? 1 : 0
                                                Behavior on color { ColorAnimation { duration: 120 } }
                                                Behavior on border.width { NumberAnimation { duration: 100 } }
                                            }
                                            Component.onCompleted: text = appController.formattedLatex
                                            onTextChanged: if (activeFocus && text !== appController.formattedLatex) appController.setFormattedLatex(text)
                                            Behavior on opacity { NumberAnimation { duration: 140 } }
                                            Connections { target: appController; function onFormattedLatexChanged() { if (formattedEditor.text !== appController.formattedLatex) formattedEditor.text = appController.formattedLatex } }
                                        }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 26
                                        color: Theme.surfaceLow
                                        border.color: Theme.line
                                        RowLayout {
                                            anchors.fill: parent; anchors.leftMargin: 9; anchors.rightMargin: 9
                                            Rectangle { Layout.preferredWidth: 6; Layout.preferredHeight: 6; radius: 3; color: appController.busy ? Theme.warning : appController.engineState === "error" ? Theme.danger : Theme.success }
                                            Text { text: appController.busy ? "正在识别，可中断" : appController.formatError.length > 0 ? appController.formatError : appController.notice; color: appController.formatError.length > 0 ? Theme.danger : Theme.inkMuted; font.family: Theme.uiFont; font.pixelSize: 9; elide: Text.ElideRight; Layout.fillWidth: true }
                                            Text { text: appController.lastDuration; color: Theme.inkMuted; font.family: Theme.monoFont; font.pixelSize: 9 }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Item {
                    id: historyPage
                    anchors.fill: parent
                    opacity: window.pageIndex === 1 ? 1 : 0
                    y: window.pageIndex === 1 ? 0 : 7
                    visible: opacity > 0
                    enabled: window.pageIndex === 1
                    Behavior on opacity { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }
                    Behavior on y { NumberAnimation { duration: 210; easing.type: Easing.OutCubic } }

                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 24; spacing: 16
                        RowLayout {
                            Layout.fillWidth: true
                            Column {
                                Text { text: "历史记录"; color: Theme.ink; font.family: Theme.uiFont; font.pixelSize: 22; font.weight: Font.DemiBold }
                                Text { text: "识别记录只保存在这台电脑上 · 最多 " + appController.historyLimit + " 条"; color: Theme.inkMuted; font.family: Theme.uiFont; font.pixelSize: 11 }
                            }
                            Item { Layout.fillWidth: true }
                            ActionButton { text: "清空历史"; enabled: historyList.count > 0; onClicked: appController.clearHistory() }
                        }
                        Rectangle {
                            id: historyPanel
                            Layout.fillWidth: true; Layout.fillHeight: true
                            color: Theme.panel; border.color: Theme.line; radius: Theme.radius

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 1
                                spacing: 0

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30
                                    color: Theme.surfaceLow

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 14
                                        anchors.rightMargin: 14
                                        spacing: 14

                                        Text {
                                            Layout.preferredWidth: historyList.previewColumnWidth
                                            text: "公式预览"
                                            color: Theme.inkMuted
                                            font.family: Theme.uiFont
                                            font.pixelSize: 9
                                            font.weight: Font.DemiBold
                                        }
                                        Text {
                                            Layout.fillWidth: true
                                            text: "LaTeX 源码"
                                            color: Theme.inkMuted
                                            font.family: Theme.uiFont
                                            font.pixelSize: 9
                                            font.weight: Font.DemiBold
                                        }
                                        Text {
                                            text: "耗时 · 时间"
                                            color: Theme.inkMuted
                                            font.family: Theme.uiFont
                                            font.pixelSize: 9
                                        }
                                    }
                                }

                                ListView {
                                    id: historyList
                                    readonly property real previewColumnWidth: Math.min(340, Math.max(230, width * 0.36))

                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    Layout.margins: 6
                                    clip: true
                                    spacing: 6
                                    cacheBuffer: 700
                                    model: appController.historyModel

                                    delegate: Rectangle {
                                        id: historyEntry
                                        required property int index
                                        required property string formula
                                        required property string timestamp
                                        required property string duration
                                        required property string previewLight
                                        required property string previewDark
                                        required property int previewWidth
                                        required property int previewHeight
                                        required property bool previewReady

                                        readonly property real previewAspect: previewHeight > 0 ? previewWidth / previewHeight : 2.8
                                        readonly property real previewDisplayHeight: previewReady
                                            ? Math.max(48, Math.min(160, historyList.previewColumnWidth / Math.max(0.1, previewAspect)))
                                            : 58

                                        width: historyList.width
                                        height: Math.max(82, previewDisplayHeight + 20, codeColumn.implicitHeight + 16)
                                        radius: Theme.radius
                                        color: historyMouse.containsMouse ? Theme.surfaceLow : Theme.surfaceLowClear
                                        scale: historyMouse.pressed ? 0.99 : 1
                                        Behavior on color { ColorAnimation { duration: 120 } }
                                        Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
                                        Behavior on height { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

                                        MouseArea {
                                            id: historyMouse
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            preventStealing: false
                                            onClicked: {
                                                appController.restoreHistory(historyEntry.index)
                                                window.pageIndex = 0
                                            }
                                        }

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 8
                                            spacing: 14

                                            Rectangle {
                                                Layout.preferredWidth: historyList.previewColumnWidth
                                                Layout.fillHeight: true
                                                color: Theme.surface
                                                border.color: Theme.line
                                                radius: Theme.radius
                                                clip: true

                                                Image {
                                                    anchors.fill: parent
                                                    anchors.margins: 8
                                                    source: Theme.dark ? historyEntry.previewDark : historyEntry.previewLight
                                                    visible: historyEntry.previewReady
                                                    asynchronous: true
                                                    cache: true
                                                    fillMode: Image.PreserveAspectFit
                                                    smooth: true
                                                    mipmap: true
                                                }

                                                Text {
                                                    anchors.centerIn: parent
                                                    visible: !historyEntry.previewReady
                                                    text: "正在排版…"
                                                    color: Theme.inkMuted
                                                    font.family: Theme.uiFont
                                                    font.pixelSize: 9
                                                }
                                            }

                                            ColumnLayout {
                                                id: codeColumn
                                                Layout.fillWidth: true
                                                Layout.fillHeight: true
                                                spacing: 6

                                                Text {
                                                    id: codeText
                                                    Layout.fillWidth: true
                                                    text: historyEntry.formula
                                                    color: Theme.ink
                                                    font.family: Theme.monoFont
                                                    font.pixelSize: 10
                                                    wrapMode: Text.WrapAnywhere
                                                    maximumLineCount: 5
                                                    elide: Text.ElideRight
                                                }

                                                Item { Layout.fillHeight: true }

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 10
                                                    Text { text: historyEntry.duration; color: Theme.inkMuted; font.family: Theme.monoFont; font.pixelSize: 9 }
                                                    Item { Layout.fillWidth: true }
                                                    Text { text: historyEntry.timestamp; color: Theme.inkMuted; font.family: Theme.uiFont; font.pixelSize: 9 }
                                                    ActionButton {
                                                        Layout.preferredHeight: 26
                                                        text: "复制"
                                                        onClicked: appController.copyHistoryFormula(historyEntry.index)
                                                    }
                                                    ActionButton {
                                                        Layout.preferredHeight: 26
                                                        text: "删除"
                                                        danger: true
                                                        onClicked: appController.removeHistory(historyEntry.index)
                                                    }
                                                }
                                            }
                                        }
                                    }

                                    ScrollBar.vertical: ScrollBar { }
                                    Text {
                                        anchors.centerIn: parent
                                        visible: historyList.count === 0
                                        text: "暂无识别记录"
                                        color: Theme.inkMuted
                                        font.family: Theme.uiFont
                                        font.pixelSize: 11
                                    }
                                }
                            }
                        }
                    }
                }

                Item {
                    id: settingsPage
                    anchors.fill: parent
                    opacity: window.pageIndex === 2 ? 1 : 0
                    y: window.pageIndex === 2 ? 0 : 7
                    visible: opacity > 0
                    enabled: window.pageIndex === 2
                    Behavior on opacity { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }
                    Behavior on y { NumberAnimation { duration: 210; easing.type: Easing.OutCubic } }

                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 24; spacing: 16
                        Column {
                            Text { text: "设置"; color: Theme.ink; font.family: Theme.uiFont; font.pixelSize: 22; font.weight: Font.DemiBold }
                            Text { text: "调整识别、复制和界面行为。"; color: Theme.inkMuted; font.family: Theme.uiFont; font.pixelSize: 11 }
                        }
                        Rectangle {
                            Layout.fillWidth: true; Layout.fillHeight: true
                            color: Theme.panel; border.color: Theme.line; radius: Theme.radius
                            ColumnLayout {
                                anchors.fill: parent; spacing: 0

                                component SettingLine: Rectangle {
                                    id: settingLine
                                    property string title: ""
                                    property string detail: ""
                                    default property alias controlData: controlHost.data
                                    Layout.fillWidth: true; Layout.preferredHeight: 62
                                    color: "transparent"; border.color: Theme.line
                                    RowLayout {
                                        anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16
                                        Column {
                                            Layout.fillWidth: true
                                            Text { text: settingLine.title; color: Theme.ink; font.family: Theme.uiFont; font.pixelSize: 12; font.weight: Font.DemiBold }
                                            Text { text: settingLine.detail; color: Theme.inkMuted; font.family: Theme.uiFont; font.pixelSize: 10 }
                                        }
                                        Item { id: controlHost; implicitWidth: childrenRect.width; implicitHeight: childrenRect.height }
                                    }
                                }

                                SettingLine { title: "识别设备"; detail: "当前发行版使用 CPU 推理"; ActionButton { text: "CPU"; enabled: false } }
                                SettingLine {
                                    title: "识别后自动复制"; detail: "完成识别时将格式化输出写入剪贴板"
                                    AnimatedSwitch { checked: appController.autoCopy; onToggled: appController.setAutoCopy(checked) }
                                }
                                SettingLine {
                                    title: "系统级截图快捷键"
                                    detail: appController.globalHotkeyStatus
                                    Row {
                                        spacing: 4
                                        FormatButton {
                                            height: 28
                                            text: "Ctrl+Shift+A"
                                            selected: appController.globalHotkey === "Ctrl+Shift+A"
                                            onClicked: appController.setGlobalHotkey("Ctrl+Shift+A")
                                        }
                                        FormatButton {
                                            height: 28
                                            text: "Alt+S"
                                            selected: appController.globalHotkey === "Alt+S"
                                            onClicked: appController.setGlobalHotkey("Alt+S")
                                        }
                                        FormatButton {
                                            height: 28
                                            text: "Ctrl+A"
                                            selected: appController.globalHotkey === "Ctrl+A"
                                            onClicked: appController.setGlobalHotkey("Ctrl+A")
                                        }
                                    }
                                }
                                SettingLine {
                                    title: "历史与截图缓存"
                                    detail: "超出上限时自动裁剪，并删除不再被引用的应用截图"
                                    Row {
                                        spacing: 4
                                        FormatButton { height: 28; text: "50"; selected: appController.historyLimit === 50; onClicked: appController.setHistoryLimit(50) }
                                        FormatButton { height: 28; text: "100"; selected: appController.historyLimit === 100; onClicked: appController.setHistoryLimit(100) }
                                        FormatButton { height: 28; text: "200"; selected: appController.historyLimit === 200; onClicked: appController.setHistoryLimit(200) }
                                        ActionButton { height: 28; text: "立即清理"; onClicked: appController.cleanCache() }
                                    }
                                }
                                SettingLine {
                                    title: "界面主题"; detail: "跟随系统，或固定使用亮色/暗色"
                                    Row {
                                        spacing: 4
                                        FormatButton {
                                            height: 28
                                            text: "跟随系统"
                                            selected: appController.themeMode === "system"
                                            onClicked: appController.setThemeMode("system")
                                        }
                                        FormatButton {
                                            height: 28
                                            text: "亮色"
                                            selected: appController.themeMode === "light"
                                            onClicked: appController.setThemeMode("light")
                                        }
                                        FormatButton {
                                            height: 28
                                            text: "暗色"
                                            selected: appController.themeMode === "dark"
                                            onClicked: appController.setThemeMode("dark")
                                        }
                                    }
                                }
                                SettingLine {
                                    title: "诊断信息"
                                    detail: "导出运行环境和脱敏日志，不包含公式或截图"
                                    ActionButton { text: "导出诊断包"; onClicked: appController.exportDiagnostics() }
                                }
                                Item { Layout.fillHeight: true }
                            }
                        }
                    }
                }
            }
        }
    }
}
