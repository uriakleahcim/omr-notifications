import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

Panel {
  id: root
  moduleName: "uriak.omr-notifications"
  ipcTarget: "uriak.omr-notifications"
  manageIpc: false

  readonly property var svc: bar && bar.shell && bar.shell.serviceFor ? bar.shell.serviceFor(moduleName) : null
  readonly property bool ready: svc !== null && svc.available
  readonly property color foreground: bar ? bar.foreground : Color.foreground
  readonly property color urgent: bar ? bar.urgent : Color.urgent
  readonly property string fontFamily: bar ? bar.fontFamily : Style.font.family
  readonly property string stateText: !svc ? "Service unavailable"
    : !svc.running ? "Companion stopped"
    : svc.paused ? "Paused"
    : !svc.impact.ready ? "Needs acknowledgement"
    : "Listening"
  readonly property string glyph: !ready ? "󰅙" : (svc.paused ? "󰏤" : "󰂚")

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  onOpenedChanged: if (opened && svc) svc.refresh()

  IpcHandler {
    target: root.ipcTarget
    function open(): void { root.open() }
    function close(): void { root.close() }
    function toggle(): void { root.toggle() }
    function pause(): void { if (root.svc) root.svc.pause() }
    function resume(): void { if (root.svc) root.svc.resume() }
    function reload(): void { if (root.svc) root.svc.reload() }
    function status(): string { return root.stateText }
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.glyph
    active: root.ready && !root.svc.paused
    foreground: root.ready ? root.foreground : root.urgent
    tooltipText: "OmR Notifications · " + root.stateText
    Accessible.role: Accessible.Button
    Accessible.name: tooltipText
    onPressed: function(buttonCode) {
      if (buttonCode === Qt.RightButton && root.svc) root.svc.togglePaused()
      else root.toggle()
    }
  }

  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(360))
    contentHeight: panel.fittedContentHeight(content.implicitHeight + keys.implicitHeight + Style.spacing.xs, Style.space(520))

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onActivateRequested: if (root.svc) root.svc.togglePaused()
      onTextKey: function(text) {
        if (!root.svc) return
        if (text === "p" || text === "P") root.svc.togglePaused()
        else if (text === "r" || text === "R") root.svc.reload()
      }

      Column {
        id: content
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Style.spacing.md

        PanelHero {
          width: parent.width
          title: "OmR Notifications"
          meta: root.stateText
          foreground: root.foreground
          fontFamily: root.fontFamily
          iconComponent: Component {
            Text {
              text: root.glyph
              color: root.ready ? root.foreground : root.urgent
              font.family: root.fontFamily
              font.pixelSize: Style.font.display
            }
          }
        }

        Text {
          width: parent.width
          text: !root.svc ? "The source service is not loaded."
            : root.svc.listenersActive + " of " + root.svc.listenersConfigured + " listeners active · "
              + root.svc.policiesActive + " policies\n"
              + root.svc.acceptedEvents + " accepted · " + root.svc.droppedEvents + " dropped · "
              + root.svc.failedActions + " action failures"
          color: root.foreground
          font.family: root.fontFamily
          font.pixelSize: Style.font.body
          wrapMode: Text.Wrap
          textFormat: Text.PlainText
        }

        Text {
          visible: root.svc && root.svc.lastEventType.length > 0
          width: parent.width
          text: "Last event  " + (root.svc ? root.svc.lastEventType : "")
          color: Qt.darker(root.foreground, 1.35)
          font.family: root.fontFamily
          font.pixelSize: Style.font.caption
          elide: Text.ElideRight
          textFormat: Text.PlainText
        }

        Text {
          visible: root.svc && (!root.svc.impact.ready || root.svc.lastError.length > 0)
          width: parent.width
          text: root.svc && root.svc.lastError.length > 0
            ? root.svc.lastError
            : "Some listeners are inactive until their resource/privacy impact is acknowledged."
          color: root.urgent
          font.family: root.fontFamily
          font.pixelSize: Style.font.caption
          wrapMode: Text.Wrap
          textFormat: Text.PlainText
        }

        Button {
          width: parent.width
          enabled: root.svc !== null
          text: root.svc && root.svc.paused ? "Resume actions  (p)" : "Pause actions  (p)"
          iconText: root.svc && root.svc.paused ? "󰐊" : "󰏤"
          foreground: root.foreground
          fontFamily: root.fontFamily
          onClicked: if (root.svc) root.svc.togglePaused()
        }

        Button {
          width: parent.width
          enabled: root.svc !== null
          text: "Reload configuration  (r)"
          iconText: "󰑐"
          foreground: root.foreground
          fontFamily: root.fontFamily
          onClicked: if (root.svc) root.svc.reload()
        }
      }
    }

    Text {
      id: keys
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.bottom: parent.bottom
      text: "p  " + (root.svc && root.svc.paused ? "resume" : "pause") + "    r  reload    esc  close"
      textFormat: Text.PlainText
      color: Qt.darker(root.foreground, 1.35)
      font.family: root.fontFamily
      font.pixelSize: Style.font.caption
      horizontalAlignment: Text.AlignHCenter
    }
  }
}
