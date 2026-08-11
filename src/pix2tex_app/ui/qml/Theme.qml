pragma Singleton
import QtQuick

QtObject {
    property bool dark: false

    readonly property color surface: dark ? "#121416" : "#F7F9FB"
    readonly property color surfaceLow: dark ? "#181B1E" : "#F2F4F6"
    readonly property color surfaceMid: dark ? "#202428" : "#ECEEF0"
    readonly property color surfaceHigh: dark ? "#292D31" : "#E6E8EA"
    readonly property color surfaceHighest: dark ? "#32373C" : "#E0E3E5"
    readonly property color surfaceLowClear: Qt.rgba(surfaceLow.r, surfaceLow.g, surfaceLow.b, 0)
    readonly property color surfaceMidClear: Qt.rgba(surfaceMid.r, surfaceMid.g, surfaceMid.b, 0)
    readonly property color surfaceHighClear: Qt.rgba(surfaceHigh.r, surfaceHigh.g, surfaceHigh.b, 0)
    readonly property color panel: dark ? "#171A1D" : "#FFFFFF"
    readonly property color ink: dark ? "#F0F1F2" : "#191C1E"
    readonly property color inkSoft: dark ? "#C4C7CA" : "#45464D"
    readonly property color inkMuted: dark ? "#92979C" : "#76777D"
    readonly property color line: dark ? "#3B4045" : "#C6C6CD"
    readonly property color primary: dark ? "#F1F2F3" : "#111214"
    readonly property color primaryHover: dark ? "#D9DCDE" : "#2D3133"
    readonly property color primaryForeground: dark ? "#111315" : "#FFFFFF"
    readonly property color switchKnob: dark ? "#2A2F33" : "#AEB4B9"
    readonly property color success: dark ? "#48B987" : "#16875B"
    readonly property color warning: dark ? "#D8A74E" : "#B7791F"
    readonly property color danger: dark ? "#FF8179" : "#BA1A1A"
    readonly property color editor: dark ? "#0B0E13" : "#0F172A"
    readonly property color editorRail: dark ? "#111722" : "#172135"
    readonly property color editorLine: dark ? "#293345" : "#334155"
    readonly property color editorText: dark ? "#E6EDF5" : "#E2E8F0"
    readonly property color editorMuted: dark ? "#748197" : "#64748B"

    readonly property string uiFont: "Segoe UI Variable"
    readonly property string monoFont: "Cascadia Code"
    readonly property string mathFont: "Cambria Math"

    readonly property int radius: 4
}
