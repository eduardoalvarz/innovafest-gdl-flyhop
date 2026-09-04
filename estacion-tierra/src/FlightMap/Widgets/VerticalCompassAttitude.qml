/****************************************************************************
 *
 * (c) 2009-2020 QGROUNDCONTROL PROJECT <http://www.qgroundcontrol.org>
 *
 * QGroundControl is licensed according to the terms in the file
 * COPYING.md in the root of the source code directory.
 *
 ****************************************************************************/

import QtQuick

import QGroundControl
import QGroundControl.Controls
import QGroundControl.ScreenTools
import QGroundControl.FactSystem
import QGroundControl.FlightMap
import QGroundControl.Palette

Rectangle {
    // This instrument is twice as tall as it is wide. On a dense phone/radio screen the
    // font-derived width alone makes it taller than the room left between the toolbar and the
    // MAVLink console, and it runs off the top of the view — so cap it against the window.
    width:  Math.min(ScreenTools.defaultFontPixelHeight * 10, _maxAllowedHeight / 2)
    height: _outerRadius * 4
    radius: _outerRadius

    readonly property real _maxAllowedHeight: mainWindow.height * 0.55
    // Tinted rather than faded with `opacity`, which would wash out the instruments themselves.
    color:  Qt.rgba(QGroundControl.globalPalette.window.r,
                    QGroundControl.globalPalette.window.g,
                    QGroundControl.globalPalette.window.b,
                    ScreenTools.overlayOpacity)
    border.width:   1
    border.color:   Qt.rgba(QGroundControl.globalPalette.text.r,
                            QGroundControl.globalPalette.text.g,
                            QGroundControl.globalPalette.text.b, 0.12)

    property real extraInset:           0
    property real extraValuesWidth:     _outerRadius

    property real _outerMargin: (width * 0.05) / 2
    property real _outerRadius: width / 2
    property real _innerRadius: _outerRadius - _outerMargin

    // Prevent all clicks from going through to lower layers
    DeadMouseArea {
        anchors.fill: parent
    }

    QGCAttitudeWidget {
        id:                         attitude
        anchors.horizontalCenter:   parent.horizontalCenter
        anchors.topMargin:          _outerMargin
        anchors.top:                parent.top
        size:                       _innerRadius * 2
        vehicle:                    globals.activeVehicle
    }

    QGCCompassWidget {
        id:                         compass
        anchors.horizontalCenter:   parent.horizontalCenter
        anchors.topMargin:          _outerMargin * 2
        anchors.top:                attitude.bottom
        size:                       _innerRadius * 2
        vehicle:                    globals.activeVehicle
    }
}
