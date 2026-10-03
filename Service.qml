import QtQuick
import Quickshell
import Quickshell.Io

Item {
  id: root

  property var shell: null
  property var manifest: null
  readonly property string pluginRoot: decodeURIComponent(String(Qt.resolvedUrl(".")).replace(/^file:\/\//, "").replace(/\/$/, ""))
  readonly property string commandPath: pluginRoot + "/bin/omr-notifications"
  readonly property string runtimeBase: Quickshell.env("XDG_RUNTIME_DIR") || "/tmp"
  readonly property string statusPath: runtimeBase + "/omr-notifications/status.json"

  property bool available: false
  property bool running: daemon.running || available
  property bool paused: false
  property int listenersActive: 0
  property int listenersConfigured: 0
  property int policiesActive: 0
  property int acceptedEvents: 0
  property int droppedEvents: 0
  property int failedActions: 0
  property string lastEventType: ""
  property string lastError: ""
  property string startedAt: ""
  property var impact: ({ ready: true, missingAcknowledgements: [] })
  property bool stopping: false

  function applyStatus(raw) {
    try {
      var status = JSON.parse(String(raw || "{}"))
      available = status.running === true
      paused = status.paused === true
      listenersActive = Number(status.listenersActive || 0)
      listenersConfigured = Number(status.listenersConfigured || 0)
      policiesActive = Number(status.policiesActive || 0)
      acceptedEvents = Number(status.acceptedEvents || 0)
      droppedEvents = Number(status.droppedEvents || 0)
      failedActions = Number(status.failedActions || 0)
      lastEventType = status.lastEvent ? String(status.lastEvent.type || "") : ""
      lastError = String(status.lastError || (status.configRejected ? status.configRejected.error : ""))
      startedAt = String(status.startedAt || "")
      impact = status.preflight || { ready: true, missingAcknowledgements: [] }
    } catch (error) {
      available = false
      lastError = "Invalid runtime status: " + error
    }
  }

  function invoke(command) {
    Quickshell.execDetached(["python3", commandPath, command])
    refreshTimer.restart()
  }

  function pause() { invoke("pause") }
  function resume() { invoke("resume") }
  function reload() { invoke("reload") }
  function togglePaused() { paused ? resume() : pause() }
  function refresh() { statusView.reload() }

  Process {
    id: daemon
    command: ["python3", root.commandPath, "run"]
    running: true
    stdout: SplitParser { onRead: function(data) { /* Runtime logs are intentionally quiet. */ } }
    stderr: SplitParser {
      onRead: function(data) {
        var message = String(data || "").trim()
        if (message.length > 0) root.lastError = message.substring(0, 512)
      }
    }
    onExited: function(exitCode) {
      if (exitCode === 75) {
        root.refresh()
        return
      }
      root.available = false
      if (!root.stopping) {
        root.lastError = "Companion exited with code " + exitCode
        restartTimer.restart()
      }
    }
  }

  FileView {
    id: statusView
    path: root.statusPath
    watchChanges: true
    blockLoading: false
    printErrors: false
    onFileChanged: reload()
    onLoaded: root.applyStatus(text())
    onLoadFailed: function(error) { root.available = false }
  }

  Timer {
    id: restartTimer
    interval: 3000
    repeat: false
    onTriggered: if (!root.stopping && !daemon.running) daemon.running = true
  }

  Timer {
    id: refreshTimer
    interval: 350
    repeat: false
    onTriggered: root.refresh()
  }

  Component.onDestruction: {
    stopping = true
    daemon.running = false
  }
}
