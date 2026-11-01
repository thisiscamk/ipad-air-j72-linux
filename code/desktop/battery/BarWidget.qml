// SPDX-License-Identifier: GPL-2.0-only
import QtQuick
import Quickshell.Io
import qs.Ui
import qs.Commons

BarWidget {
  id: root
  moduleName: "ipadlinux.battery"
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  property int capacity: -1
  property string batteryStatus: "Unknown"
  readonly property bool charging: batteryStatus === "Charging"
  readonly property string label: (charging ? "󰂄 " : "󰁹 ")
    + (capacity >= 0 ? capacity + "%" : "—")
  readonly property string batteryPath: "/sys/class/power_supply/j72-bq27545-battery/"

  FileView {
    id: capacityFile
    path: root.batteryPath + "capacity"
    printErrors: false
    onLoaded: {
      var raw = text().trim()
      var value = Number(raw)
      root.capacity = /^[0-9]{1,3}$/.test(raw) && value <= 100 ? value : -1
    }
    onLoadFailed: root.capacity = -1
  }

  FileView {
    id: statusFile
    path: root.batteryPath + "status"
    printErrors: false
    onLoaded: {
      var value = text().trim()
      root.batteryStatus = ["Charging", "Discharging", "Full", "Not charging"].indexOf(value) >= 0
        ? value : "Unknown"
    }
    onLoadFailed: root.batteryStatus = "Unknown"
  }

  Timer {
    interval: 5000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: {
      capacityFile.reload()
      statusFile.reload()
    }
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: root.label
    fontSize: Math.max(13, Style.font.body)
    active: root.capacity >= 0 && root.capacity <= 15 && !root.charging
    pressable: false
    tooltipText: root.batteryStatus + (root.capacity >= 0 ? " · " + root.capacity + "%" : " · battery reading unavailable")
  }

  ShellIpc {
    target: "ipadlinux.battery"
    function status(): string {
      return JSON.stringify({capacity: root.capacity, status: root.batteryStatus, label: root.label})
    }
  }
}
