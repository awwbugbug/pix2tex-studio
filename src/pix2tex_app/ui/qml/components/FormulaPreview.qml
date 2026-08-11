import QtQuick
import QtWebEngine
import ".."

WebEngineView {
    id: root

    property string latex: ""
    property bool dark: false

    backgroundColor: Theme.surface
    settings.localContentCanAccessFileUrls: true

    function renderFormula() {
        if (!latex.length)
            return
        const math = JSON.stringify(latex)
        const foreground = dark ? "#F0F1F2" : "#191C1E"
        const background = dark ? "#121416" : "#F7F9FB"
        const html = `<!doctype html><html><head><meta charset="utf-8">
          <script src="MathJax.js"><\/script>
          <script>MathJax.Hub.Config({messageStyle:'none',showMathMenu:false,tex2jax:{preview:'none'}});<\/script>
          <style>html,body{width:100%;height:100%;margin:0;background:${background};color:${foreground}}
          html{overflow:hidden}body{overflow:auto;font-size:20px;font-family:'Cambria Math',serif}
          #viewport{min-width:100%;min-height:100%;display:flex;align-items:safe center;justify-content:safe center;
          padding:26px;box-sizing:border-box}#equation{flex:none;box-sizing:border-box;max-width:none}
          .MathJax_Display{margin:0!important}<\/style></head>
          <body><div id="viewport"><div id="equation"></div></div><script>
          document.getElementById('equation').textContent='$$'+${math}+'$$';
          MathJax.Hub.Queue(['Typeset',MathJax.Hub,document.getElementById('equation')]);
          <\/script></body></html>`
        root.loadHtml(html, Qt.resolvedUrl("../../assets/"))
    }

    onLatexChanged: renderFormula()
    onDarkChanged: renderFormula()
    Component.onCompleted: renderFormula()
}
