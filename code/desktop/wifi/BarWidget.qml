// SPDX-License-Identifier: GPL-2.0-only
import QtQuick
import Quickshell.Io
import qs.Ui
import qs.Commons

BarWidget {
  id: root
  moduleName: "ipadlinux.wifi"
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight
  property bool connected: false
  property int signalDbm: -127
  property int frequencyMhz: 0
  property bool popupOpen: false
  readonly property bool signalKnown: signalDbm >= -120 && signalDbm <= 0
  readonly property string quality: !connected ? "Disconnected"
    : !signalKnown ? "Connected" : signalDbm >= -55 ? "Excellent"
    : signalDbm >= -67 ? "Good" : signalDbm >= -75 ? "Fair" : "Weak"
  readonly property string icon: !connected ? "󰤭" : !signalKnown || signalDbm >= -55 ? "󰤨"
    : signalDbm >= -67 ? "󰤥" : signalDbm >= -75 ? "󰤢" : "󰤟"
  readonly property string details: connected
    ? "Connected" + (signalKnown ? " · " + signalDbm + " dBm (" + quality + ")" : "")
      + (frequencyMhz > 0 ? "\n" + frequencyMhz + " MHz" : "")
    : "Not connected"
  function close() { popupOpen = false }

  FileView {
    id: statusFile
    path: "/run/user/1000/j72-wifi-status.json"
    printErrors: false
    onLoaded: {
      try {
        var value = JSON.parse(text())
        root.connected = value.connected === true
        root.signalDbm = typeof value.signal_dbm === "number" ? value.signal_dbm : -127
        root.frequencyMhz = typeof value.frequency_mhz === "number" ? value.frequency_mhz : 0
      } catch (error) { root.connected = false; root.signalDbm = -127; root.frequencyMhz = 0 }
    }
    onLoadFailed: { root.connected = false; root.signalDbm = -127; root.frequencyMhz = 0 }
  }
  Timer {
    interval: 5000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: statusFile.reload()
  }
  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.icon
    fontSize: Math.max(18, Style.font.body)
    dimmed: !root.connected
    tooltipText: "Wi-Fi · " + root.details
    onPressed: function(button) { if (button === Qt.LeftButton) root.popupOpen = !root.popupOpen }
  }
  PopupCard {
    anchorItem: root
    bar: root.bar
    owner: root
    open: root.popupOpen
    contentWidth: fittedContentWidth(Style.space(300))
    contentHeight: fittedContentHeight(column.implicitHeight)
    Column {
      id: column
      width: parent.width
      spacing: Style.space(12)
      Text {
        width: parent.width
        text: "Wi-Fi"
        color: root.bar.foreground
        font.family: root.bar.fontFamily
        font.pixelSize: Style.font.body
        font.bold: true
      }
      Text {
        width: parent.width
        text: root.details
        color: root.bar.foreground
        font.family: root.bar.fontFamily
        font.pixelSize: Style.font.body
        wrapMode: Text.WordWrap
      }
      WidgetButton { bar: root.bar; text: "Close"; onPressed: root.close() }
    }
  }
  ShellIpc {
    target: "ipadlinux.wifi"
    function status(): string {
      return JSON.stringify({connected: root.connected, signal_dbm: root.signalDbm,
        frequency_mhz: root.frequencyMhz, quality: root.quality, icon: root.icon, popup: root.popupOpen})
    }
    function toggle(): void { root.popupOpen = !root.popupOpen }
  }
}
