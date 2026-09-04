/****************************************************************************
 *
 * OTECH GroundStation — MAVLink console.
 *
 * A translucent terminal strip along the bottom of the Fly view carrying
 * STATUSTEXT traffic plus a change-driven telemetry ticker. Messages are
 * colored with the aeronautical alerting convention: red = warning (immediate
 * action), amber = caution (awareness), cyan/green/white = advisory.
 *
 * It is deliberately translucent and collapsible so it can sit over an FPV
 * video feed without hiding it, and it removes itself entirely when video
 * goes full screen.
 *
 ****************************************************************************/

import QtQuick
import QtQuick.Layouts

import QGroundControl
import QGroundControl.Controls
import QGroundControl.ScreenTools

Rectangle {
    id: root

    // Collapsed we keep only the header bar, so the console never fully
    // disappears and the user can always get it back.
    height:     expanded ? Math.round(parent.height * _expandedFraction) : header.height
    color:      "transparent"
    clip:       true

    property bool expanded: true

    /// Height taken when expanded, as a fraction of the Fly view. A fifth, per spec.
    readonly property real _expandedFraction: 0.2

    /// How much of the bottom edge this control occupies — fed into the Fly view tool insets
    /// so the other widgets stack above it instead of hiding behind it.
    readonly property real bottomEdgeInset: height

    property var  _vehicle:     globals.activeVehicle
    property var  _qgcPal:      QGroundControl.globalPalette
    property int  _maxRows:     500
    property bool _autoScroll:  true

    // ---- Aeronautical alerting palette -------------------------------------------------
    // MAV_SEVERITY 0..7 → EMERGENCY, ALERT, CRITICAL, ERROR, WARNING, NOTICE, INFO, DEBUG
    readonly property var _severityColor: [
        "#ff2d2d",  // 0 EMERGENCY — warning
        "#ff2d2d",  // 1 ALERT     — warning
        "#ff5330",  // 2 CRITICAL  — warning
        "#ff7a45",  // 3 ERROR     — warning
        "#ffbf00",  // 4 WARNING   — caution (amber)
        "#4fc3e8",  // 5 NOTICE    — advisory
        "#5fd67f",  // 6 INFO      — advisory
        "#8a94a6"   // 7 DEBUG     — advisory, de-emphasised
    ]

    readonly property var _severityLabel: [
        "EMRG", "ALRT", "CRIT", "ERR ", "WARN", "NOTE", "INFO", "DBUG"
    ]

    readonly property color _tickerColor:   "#9fb3c8"
    readonly property color _systemColor:   "#4fc3e8"

    /// smallFontPointSize (0.75x) is too small to read at a glance in flight.
    readonly property real _fontSize: ScreenTools.defaultFontPointSize * 0.95

    Behavior on height {
        NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
    }

    // ---- Backdrop: translucent gray over translucent black ------------------------------
    Rectangle {
        anchors.fill:   parent
        radius:         ScreenTools.cardBorderRadius

        // Translucent, but opaque enough that map detail underneath cannot compete with the
        // text. Below roughly 0.85 the street labels bleed through and the log becomes unreadable.
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(0.16, 0.18, 0.21, 0.88) }
            GradientStop { position: 1.0; color: Qt.rgba(0.00, 0.00, 0.00, 0.95) }
        }
    }

    Rectangle {
        anchors.left:   parent.left
        anchors.right:  parent.right
        anchors.top:    parent.top
        height:         1
        color:          Qt.rgba(1, 1, 1, 0.14)
    }

    // Keep clicks and scrolls off the map underneath.
    DeadMouseArea {
        anchors.fill: parent
    }

    function _timestamp() {
        const d = new Date()
        return Qt.formatTime(d, "hh:mm:ss")
    }

    function _append(severity, source, text, overrideColor) {
        logModel.append({
            "ts":        _timestamp(),
            "sev":       severity,
            "src":       source,
            "msg":       text,
            "colorOverride": overrideColor === undefined ? "" : String(overrideColor)
        })
        while (logModel.count > _maxRows) {
            logModel.remove(0)
        }
        if (_autoScroll) {
            logView.positionViewAtEnd()
        }
    }

    function appendSystem(text) {
        _append(5, "GCS", text, _systemColor)
    }

    function clearLog() {
        logModel.clear()
    }

    ListModel { id: logModel }

    // ---- MAVLink STATUSTEXT ------------------------------------------------------------
    Connections {
        target: _vehicle

        function onTextMessageReceived(sysid, componentid, severity, text, description) {
            const sev = Math.max(0, Math.min(7, severity))
            root._append(sev, "MAV" + sysid + "." + componentid, text)
        }
    }

    on_VehicleChanged: {
        // Drop the comparison baseline, otherwise the first sample from a new vehicle is diffed
        // against the old one and reports a pile of bogus transitions.
        _prev       = null
        _lastEmitMs = 0

        if (_vehicle) {
            appendSystem(qsTr("Vehicle %1 connected").arg(_vehicle.id))
        } else {
            appendSystem(qsTr("Vehicle disconnected"))
        }
    }

    Component.onCompleted: appendSystem(qsTr("%1 console ready").arg(QGroundControl.appName))

    // ---- Telemetry ticker --------------------------------------------------------------
    //
    // Change driven rather than once per second. A fixed-rate ticker buries real STATUSTEXT
    // traffic within seconds — a few minutes of hovering is enough to push it off the buffer
    // entirely. So a telemetry line is written only when something actually moved past a
    // threshold, with a slow heartbeat so the log never looks frozen.

    /// Snapshot of the last line we actually wrote. Drift is measured against this, not against
    /// the previous tick, otherwise a slow steady climb never trips any threshold.
    property var    _prev:          null
    property double _lastEmitMs:    0

    readonly property int _heartbeatMs: 10000

    // Thresholds below which a value is considered noise rather than news.
    readonly property real _altThreshold:   0.5     // m
    readonly property real _speedThreshold: 0.5     // m/s
    readonly property real _hdgThreshold:   5       // degrees
    readonly property real _battThreshold:  1       // percent

    function _snapshot(v) {
        const batt = v.batteries.count > 0 ? v.batteries.get(0) : null
        return {
            "mode":  v.flightMode,
            "armed": v.armed,
            "sats":  v.gps.count.rawValue,
            "fix":   v.gps.lock.rawValue,
            "alt":   v.altitudeRelative.rawValue,
            "gs":    v.groundSpeed.rawValue,
            "vs":    v.climbRate.rawValue,
            "hdg":   v.heading.rawValue,
            "batt":  batt ? batt.percentRemaining.rawValue : NaN
        }
    }

    function _moved(a, b, threshold) {
        // A value appearing or dropping out is itself news.
        if (isNaN(a) !== isNaN(b)) {
            return true
        }
        if (isNaN(a)) {
            return false
        }
        return Math.abs(a - b) >= threshold
    }

    function _headingMoved(a, b, threshold) {
        if (isNaN(a) !== isNaN(b)) {
            return true
        }
        if (isNaN(a)) {
            return false
        }
        // Shortest way round, so 359° → 1° reads as 2° and not 358°.
        let d = Math.abs(a - b) % 360
        if (d > 180) {
            d = 360 - d
        }
        return d >= threshold
    }

    function _formatTelemetry(v) {
        const batt = v.batteries.count > 0 ? v.batteries.get(0) : null
        const parts = [
            "MODE " + v.flightMode,
            v.armed ? "ARMED" : "DISARM",
            "ALT "  + v.altitudeRelative.valueString + v.altitudeRelative.units,
            "GS "   + v.groundSpeed.valueString + v.groundSpeed.units,
            "VS "   + v.climbRate.valueString + v.climbRate.units,
            "HDG "  + v.heading.valueString + "°",
            "SATS " + v.gps.count.valueString,
            "HDOP " + v.gps.hdop.valueString
        ]
        if (batt) {
            parts.push("BAT " + batt.percentRemaining.valueString + "% / " +
                       batt.voltage.valueString + batt.voltage.units)
        }
        return parts.join("  |  ")
    }

    /// Discrete state transitions get their own line, since those are the events a pilot
    /// scrolls back looking for. Returns true if anything was written.
    function _emitStateChanges(prev, cur) {
        if (prev === null) {
            return false
        }
        let emitted = false

        if (cur.mode !== prev.mode) {
            _append(5, "STATE", "MODE  " + prev.mode + "  →  " + cur.mode)
            emitted = true
        }
        if (cur.armed !== prev.armed) {
            // Armed is a caution state in its own right, so it goes out amber.
            _append(cur.armed ? 4 : 5, "STATE", cur.armed ? qsTr("ARMED") : qsTr("DISARMED"))
            emitted = true
        }
        if (cur.sats !== prev.sats) {
            _append(cur.sats >= 6 ? 5 : 4, "STATE", "SATS  " + prev.sats + "  →  " + cur.sats)
            emitted = true
        }
        if (cur.fix !== prev.fix) {
            _append(5, "STATE", "GPS FIX  " + prev.fix + "  →  " + cur.fix)
            emitted = true
        }
        return emitted
    }

    function _driftedEnough(prev, cur) {
        return _moved(cur.alt,  prev.alt,  _altThreshold)
            || _moved(cur.gs,   prev.gs,   _speedThreshold)
            || _moved(cur.vs,   prev.vs,   _speedThreshold)
            || _moved(cur.batt, prev.batt, _battThreshold)
            || _headingMoved(cur.hdg, prev.hdg, _hdgThreshold)
    }

    Timer {
        // Sampled at 1 Hz, but only writes a line when the sample says something new.
        interval:   1000
        repeat:     true
        running:    root.visible && !!_vehicle &&
                    QGroundControl.settingsManager.flyViewSettings.mavlinkConsoleTelemetryTicker.rawValue

        onTriggered: {
            const v = root._vehicle
            if (!v) {
                return
            }

            const cur = root._snapshot(v)
            const now = Date.now()

            const stateChanged  = root._emitStateChanges(root._prev, cur)
            const heartbeatDue  = (now - root._lastEmitMs) >= root._heartbeatMs
            const drifted       = root._prev !== null && root._driftedEnough(root._prev, cur)

            if (root._prev === null || stateChanged || drifted || heartbeatDue) {
                root._append(6, "TLM", root._formatTelemetry(v), root._tickerColor)
                root._lastEmitMs = now
                root._prev = cur
            }
        }
    }

    ColumnLayout {
        anchors.fill:       parent
        anchors.margins:    ScreenTools.defaultFontPixelWidth * 0.6
        spacing:            ScreenTools.defaultFontPixelHeight * 0.25

        // ---- Header ---------------------------------------------------------------------
        RowLayout {
            id:                 header
            Layout.fillWidth:   true
            spacing:            ScreenTools.defaultFontPixelWidth

            QGCLabel {
                text:               "▸ MAVLINK"
                color:              root._systemColor
                font.family:        ScreenTools.fixedFontFamily
                font.pointSize:     root._fontSize
                font.letterSpacing: 1.5
            }

            // Live status chips — a glance-able summary that stays useful while collapsed.
            Repeater {
                model: root._chips

                Rectangle {
                    Layout.preferredWidth:  chipLabel.implicitWidth + ScreenTools.defaultFontPixelWidth
                    Layout.preferredHeight: chipLabel.implicitHeight + ScreenTools.defaultFontPixelHeight * 0.2
                    radius:                 height / 2
                    color:                  Qt.rgba(1, 1, 1, 0.07)
                    border.width:           1
                    border.color:           Qt.rgba(_chipColor.r, _chipColor.g, _chipColor.b, 0.45)

                    // Declared as a color so the "#rrggbb" string from the model gains .r/.g/.b.
                    property color _chipColor: modelData.c

                    QGCLabel {
                        id:                 chipLabel
                        anchors.centerIn:   parent
                        text:               modelData.t
                        color:              parent._chipColor
                        font.family:        ScreenTools.fixedFontFamily
                        font.pointSize:     root._fontSize
                    }
                }
            }

            Item { Layout.fillWidth: true }

            QGCLabel {
                text:           qsTr("%1 msgs").arg(logModel.count)
                color:          Qt.rgba(1, 1, 1, 0.60)
                font.family:    ScreenTools.fixedFontFamily
                font.pointSize: root._fontSize
            }

            QGCButton {
                text:           root._autoScroll ? qsTr("Auto") : qsTr("Hold")
                pointSize:      root._fontSize
                onClicked: {
                    root._autoScroll = !root._autoScroll
                    if (root._autoScroll) {
                        logView.positionViewAtEnd()
                    }
                }
            }

            QGCButton {
                text:       qsTr("Clear")
                pointSize:  root._fontSize
                onClicked:  root.clearLog()
            }

            QGCButton {
                text:       root.expanded ? "▼" : "▲"
                pointSize:  root._fontSize
                onClicked:  root.expanded = !root.expanded
            }
        }

        // ---- Log ------------------------------------------------------------------------
        QGCListView {
            id:                 logView
            Layout.fillWidth:   true
            Layout.fillHeight:  true
            visible:            root.expanded
            clip:               true
            model:              logModel
            spacing:            0
            cacheBuffer:        0

            // Any manual scroll parks the view; the Auto/Hold button puts it back.
            onMovementStarted: root._autoScroll = false

            delegate: RowLayout {
                id:         logRow
                width:      logView.width
                spacing:    ScreenTools.defaultFontPixelWidth * 0.8

                property color _rowColor: model.colorOverride !== ""
                                            ? model.colorOverride
                                            : root._severityColor[model.sev]

                QGCLabel {
                    text:           model.ts
                    color:          Qt.rgba(1, 1, 1, 0.55)
                    font.family:    ScreenTools.fixedFontFamily
                    font.pointSize: root._fontSize
                }

                QGCLabel {
                    Layout.preferredWidth: ScreenTools.defaultFontPixelWidth * 5
                    text:           root._severityLabel[model.sev]
                    color:          logRow._rowColor
                    font.family:    ScreenTools.fixedFontFamily
                    font.pointSize: root._fontSize
                    font.bold:      model.sev <= 3
                }

                QGCLabel {
                    Layout.preferredWidth: ScreenTools.defaultFontPixelWidth * 9
                    text:           model.src
                    color:          Qt.rgba(1, 1, 1, 0.55)
                    font.family:    ScreenTools.fixedFontFamily
                    font.pointSize: root._fontSize
                    elide:          Text.ElideRight
                }

                QGCLabel {
                    Layout.fillWidth: true
                    text:           model.msg
                    color:          logRow._rowColor
                    font.family:    ScreenTools.fixedFontFamily
                    font.pointSize: root._fontSize
                    font.bold:      model.sev <= 2
                    wrapMode:       Text.NoWrap
                    elide:          Text.ElideRight
                }
            }
        }
    }

    // Status chips shown in the header. Recomputed whenever any input changes.
    property var _chips: {
        if (!_vehicle) {
            return [ { "t": qsTr("NO LINK"), "c": _severityColor[4] } ]
        }
        const v = _vehicle
        const batt = v.batteries.count > 0 ? v.batteries.get(0) : null
        const sats = v.gps.count.rawValue
        const pct  = batt ? batt.percentRemaining.rawValue : NaN

        const chips = [
            { "t": v.flightMode, "c": _systemColor },
            { "t": v.armed ? qsTr("ARMED") : qsTr("DISARMED"),
              "c": v.armed ? _severityColor[4] : _severityColor[6] },
            { "t": "ALT " + v.altitudeRelative.valueString + v.altitudeRelative.units, "c": _tickerColor },
            { "t": "GS " + v.groundSpeed.valueString + v.groundSpeed.units, "c": _tickerColor },
            // Fewer than 6 satellites is not a usable 3D fix — flag it amber.
            { "t": "SAT " + v.gps.count.valueString, "c": sats >= 6 ? _severityColor[6] : _severityColor[4] }
        ]
        if (batt && !isNaN(pct)) {
            chips.push({ "t": "BAT " + batt.percentRemaining.valueString + "%",
                         "c": pct > 40 ? _severityColor[6] : (pct > 20 ? _severityColor[4] : _severityColor[0]) })
        }
        return chips
    }
}
