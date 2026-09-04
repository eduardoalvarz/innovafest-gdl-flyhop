/****************************************************************************
 *
 * OTECH GroundStation branded startup screen.
 *
 * Shows the OTECH mark beating like a heartbeat over a progress bar, then
 * dissolves away. Colors are intentionally hardcoded to the brand palette
 * rather than taken from QGCPalette: this is a brand asset and should look
 * identical no matter which theme the user has selected.
 *
 ****************************************************************************/

import QtQuick
import QtQuick.Layouts

import QGroundControl
import QGroundControl.Controls
import QGroundControl.ScreenTools

Item {
    id: splash

    anchors.fill:   parent
    z:              10000
    visible:        opacity > 0

    /// Emitted once the splash has fully faded out and is no longer covering the UI.
    signal finished()

    /// How long the logo beats before the progress bar completes and we fade out.
    property int    holdDuration:   2400
    property int    fadeDuration:   550

    readonly property color _deepBlue:  "#0b1430"
    readonly property color _midBlue:   "#12224b"
    readonly property color _accent:    "#1e98c1"
    readonly property color _accentDim: "#155f7a"

    property real   _progress:  0

    // Swallow anything aimed at the UI underneath while we are covering it.
    MouseArea {
        anchors.fill:   parent
        enabled:        splash.opacity > 0
        hoverEnabled:   true
        onWheel:        (wheel) => wheel.accepted = true
    }

    Rectangle {
        anchors.fill: parent

        gradient: Gradient {
            GradientStop { position: 0.0; color: splash._midBlue }
            GradientStop { position: 0.55; color: splash._deepBlue }
            GradientStop { position: 1.0; color: "#060b1c" }
        }
    }

    // Soft vignette so the corners fall away and the center reads as lit.
    Rectangle {
        anchors.fill: parent
        opacity:      0.55

        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#000000" }
            GradientStop { position: 0.5; color: "transparent" }
            GradientStop { position: 1.0; color: "#000000" }
        }
    }

    ColumnLayout {
        anchors.centerIn:   parent
        width:              Math.min(parent.width * 0.6, ScreenTools.defaultFontPixelWidth * 46)
        spacing:            ScreenTools.defaultFontPixelHeight * 1.2

        // ---- Logo with pulsing halo ------------------------------------------------
        Item {
            Layout.alignment:       Qt.AlignHCenter
            Layout.preferredWidth:  _logoSize * 2.1
            Layout.preferredHeight: _logoSize * 2.1

            property real _logoSize: Math.min(splash.width, splash.height) * 0.17

            // Outer halo — expands and dissipates on each beat.
            Rectangle {
                anchors.centerIn:   parent
                width:              parent._logoSize * 1.65
                height:             width
                radius:             width / 2
                color:              "transparent"
                border.color:       splash._accent
                border.width:       Math.max(1, parent._logoSize * 0.012)
                // scale/opacity are driven entirely by the value sources below; setting them
                // statically here as well would be a duplicate binding on the same property.

                SequentialAnimation on scale {
                    loops:      Animation.Infinite
                    running:    splash.visible
                    NumberAnimation { from: 0.82; to: 1.35; duration: 1100; easing.type: Easing.OutQuad }
                    PauseAnimation { duration: 300 }
                }

                SequentialAnimation on opacity {
                    loops:      Animation.Infinite
                    running:    splash.visible
                    NumberAnimation { from: 0.0; to: 0.5; duration: 260; easing.type: Easing.OutQuad }
                    NumberAnimation { from: 0.5; to: 0.0; duration: 840; easing.type: Easing.InQuad }
                    PauseAnimation { duration: 300 }
                }
            }

            // Inner glow disc sitting behind the mark.
            Rectangle {
                anchors.centerIn:   parent
                width:              parent._logoSize * 1.28
                height:             width
                radius:             width / 2
                color:              splash._accentDim
                opacity:            0.20
            }

            Image {
                id:                 logo
                anchors.centerIn:   parent
                width:              parent._logoSize
                height:             parent._logoSize
                // Circular, feathered-alpha cut of the mark. The shipped logo artwork sits on an
                // opaque square, which read as a hard box against the round halo.
                source:             "/res/OtechSplashLogo.png"
                sourceSize.width:   width
                sourceSize.height:  height
                fillMode:           Image.PreserveAspectFit
                smooth:             true

                // Heartbeat: a strong beat followed by a softer one, then a rest.
                SequentialAnimation on scale {
                    loops:      Animation.Infinite
                    running:    splash.visible
                    NumberAnimation { from: 1.00; to: 1.14; duration: 150; easing.type: Easing.OutQuad }
                    NumberAnimation { from: 1.14; to: 1.00; duration: 170; easing.type: Easing.InOutQuad }
                    NumberAnimation { from: 1.00; to: 1.08; duration: 130; easing.type: Easing.OutQuad }
                    NumberAnimation { from: 1.08; to: 1.00; duration: 200; easing.type: Easing.InOutQuad }
                    PauseAnimation  { duration: 550 }
                }
            }
        }

        // ---- Wordmark --------------------------------------------------------------
        QGCLabel {
            Layout.alignment:   Qt.AlignHCenter
            text:               QGroundControl.appName
            color:              "white"
            font.pointSize:     ScreenTools.largeFontPointSize * 1.15
            font.letterSpacing: ScreenTools.defaultFontPixelWidth * 0.22
            font.weight:        Font.DemiBold
        }

        QGCLabel {
            Layout.alignment:   Qt.AlignHCenter
            Layout.topMargin:   -ScreenTools.defaultFontPixelHeight * 0.7
            text:               QGroundControl.qgcVersion
            color:              splash._accent
            font.pointSize:     ScreenTools.smallFontPointSize
            font.letterSpacing: ScreenTools.defaultFontPixelWidth * 0.12
        }

        // ---- Progress bar ----------------------------------------------------------
        Rectangle {
            id:                     track
            Layout.fillWidth:       true
            Layout.topMargin:       ScreenTools.defaultFontPixelHeight * 0.6
            Layout.preferredHeight: Math.max(3, ScreenTools.defaultFontPixelHeight * 0.28)
            radius:                 height / 2
            color:                  Qt.rgba(1, 1, 1, 0.12)

            Rectangle {
                id:         fill
                width:      parent.width * splash._progress
                height:     parent.height
                radius:     parent.radius

                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: splash._accentDim }
                    GradientStop { position: 1.0; color: splash._accent }
                }
            }

            // Travelling highlight so the bar reads as active rather than static.
            Rectangle {
                height:     parent.height
                width:      parent.width * 0.18
                radius:     parent.radius
                opacity:    0.35
                visible:    splash._progress < 1

                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "transparent" }
                    GradientStop { position: 0.5; color: "white" }
                    GradientStop { position: 1.0; color: "transparent" }
                }

                XAnimator on x {
                    loops:      Animation.Infinite
                    running:    splash.visible
                    from:       -track.width * 0.18
                    to:         track.width
                    duration:   1150
                }
            }
        }

        QGCLabel {
            Layout.alignment:   Qt.AlignHCenter
            text:               qsTr("Starting up…")
            color:              Qt.rgba(1, 1, 1, 0.65)
            font.pointSize:     ScreenTools.smallFontPointSize
        }
    }

    // ---- Sequencing ----------------------------------------------------------------

    NumberAnimation {
        id:         progressAnimation
        target:     splash
        property:   "_progress"
        from:       0
        to:         1
        duration:   splash.holdDuration
        easing.type: Easing.InOutQuad
        running:    true
        onFinished: fadeOut.start()
    }

    SequentialAnimation {
        id: fadeOut

        NumberAnimation {
            target:     splash
            property:   "opacity"
            from:       1
            to:         0
            duration:   splash.fadeDuration
            easing.type: Easing.InQuad
        }

        ScriptAction {
            script: splash.finished()
        }
    }
}
