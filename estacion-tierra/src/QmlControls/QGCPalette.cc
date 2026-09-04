/****************************************************************************
 *
 * (c) 2009-2024 QGROUNDCONTROL PROJECT <http://www.qgroundcontrol.org>
 *
 * QGroundControl is licensed according to the terms in the file
 * COPYING.md in the root of the source code directory.
 *
 ****************************************************************************/


/// @file
///     @author Don Gagne <don@thegagnes.com>

#include "QGCPalette.h"
#include "QGCCorePlugin.h"

#include <QtCore/QDebug>

QList<QGCPalette*>   QGCPalette::_paletteObjects;

QGCPalette::Theme QGCPalette::_theme = QGCPalette::Dark;

QMap<int, QMap<int, QMap<QString, QColor>>> QGCPalette::_colorInfoMap;

QStringList QGCPalette::_colors;

QGCPalette::QGCPalette(QObject* parent) :
    QObject(parent),
    _colorGroupEnabled(true)
{
    if (_colorInfoMap.isEmpty()) {
        _buildMap();
    }

    // We have to keep track of all QGCPalette objects in the system so we can signal theme change to all of them
    _paletteObjects += this;
}

QGCPalette::~QGCPalette()
{
    bool fSuccess = _paletteObjects.removeOne(this);
    if (!fSuccess) {
        qWarning() << "Internal error";
    }
}

void QGCPalette::_buildMap()
{
    //                                      Light                 Dark
    //                                      Disabled   Enabled    Disabled   Enabled
    DECLARE_QGC_COLOR(window,               "#eaf3fb", "#eaf3fb", "#0f1b3d", "#0f1b3d")
    DECLARE_QGC_COLOR(windowShadeLight,     "#a9c3dd", "#8fb3d6", "#3d5580", "#2c4472")
    DECLARE_QGC_COLOR(windowShade,          "#d3e6f5", "#d3e6f5", "#16294d", "#16294d")
    DECLARE_QGC_COLOR(windowShadeDark,      "#b9d7ee", "#b9d7ee", "#0b1730", "#0b1730")
    DECLARE_QGC_COLOR(text,                 "#7893ab", "#10233d", "#5d7398", "#ffffff")
    DECLARE_QGC_COLOR(warningText,          "#cc0808", "#cc0808", "#f85761", "#f85761")
    DECLARE_QGC_COLOR(button,               "#ffffff", "#ffffff", "#3d5580", "#1c2f57")
    DECLARE_QGC_COLOR(buttonBorder,         "#7893ab", "#1e98c1", "#3d5580", "#4fc3e8")
    DECLARE_QGC_COLOR(buttonText,           "#7893ab", "#10233d", "#7893ab", "#ffffff")
    DECLARE_QGC_COLOR(buttonHighlight,      "#c7ddf0", "#1e98c1", "#233a63", "#1e98c1")
    DECLARE_QGC_COLOR(buttonHighlightText,  "#0f1b3d", "#ffffff", "#0f1b3d", "#ffffff")
    DECLARE_QGC_COLOR(primaryButton,        "#5c7896", "#0d3b66", "#5c7896", "#1e98c1")
    DECLARE_QGC_COLOR(primaryButtonText,    "#0f1b3d", "#ffffff", "#0f1b3d", "#000000")
    DECLARE_QGC_COLOR(textField,            "#ffffff", "#ffffff", "#3d5580", "#16294d")
    DECLARE_QGC_COLOR(textFieldText,        "#7893ab", "#10233d", "#0f1b3d", "#ffffff")
    DECLARE_QGC_COLOR(mapButton,            "#5c7896", "#10233d", "#5c7896", "#0b1730")
    DECLARE_QGC_COLOR(mapButtonHighlight,   "#5c7896", "#1e98c1", "#5c7896", "#1e98c1")
    DECLARE_QGC_COLOR(mapIndicator,         "#5c7896", "#1e98c1", "#5c7896", "#1e98c1")
    DECLARE_QGC_COLOR(mapIndicatorChild,    "#5c7896", "#4fc3e8", "#5c7896", "#4fc3e8")
    DECLARE_QGC_COLOR(colorGreen,           "#008f2d", "#008f2d", "#00e04b", "#00e04b")
    DECLARE_QGC_COLOR(colorYellow,          "#a2a200", "#a2a200", "#ffff00", "#ffff00")
    DECLARE_QGC_COLOR(colorYellowGreen,     "#799f26", "#799f26", "#9dbe2f", "#9dbe2f")
    DECLARE_QGC_COLOR(colorOrange,          "#bf7539", "#bf7539", "#de8500", "#de8500")
    DECLARE_QGC_COLOR(colorRed,             "#b52b2b", "#b52b2b", "#f32836", "#f32836")
    DECLARE_QGC_COLOR(colorGrey,            "#808080", "#808080", "#bfbfbf", "#bfbfbf")
    DECLARE_QGC_COLOR(colorBlue,            "#1a72ff", "#1a72ff", "#536dff", "#536dff")
    DECLARE_QGC_COLOR(alertBackground,      "#eecc44", "#eecc44", "#eecc44", "#eecc44")
    DECLARE_QGC_COLOR(alertBorder,          "#808080", "#808080", "#808080", "#808080")
    DECLARE_QGC_COLOR(alertText,            "#000000", "#000000", "#000000", "#000000")
    DECLARE_QGC_COLOR(missionItemEditor,    "#5c7896", "#dbfef8", "#5c7896", "#233a63")
    DECLARE_QGC_COLOR(toolStripHoverColor,  "#5c7896", "#1e98c1", "#5c7896", "#233a63")
    DECLARE_QGC_COLOR(statusFailedText,     "#7893ab", "#000000", "#5d7398", "#ffffff")
    DECLARE_QGC_COLOR(statusPassedText,     "#7893ab", "#000000", "#5d7398", "#ffffff")
    DECLARE_QGC_COLOR(statusPendingText,    "#7893ab", "#000000", "#5d7398", "#ffffff")
    DECLARE_QGC_COLOR(toolbarBackground,    "#eaf3fb", "#eaf3fb", "#0f1b3d", "#0f1b3d")
    DECLARE_QGC_COLOR(groupBorder,          "#a9c3dd", "#1e98c1", "#3d5580", "#3d5580")

    // Colors not affecting by theming
    //                                              Disabled    Enabled
    DECLARE_QGC_NONTHEMED_COLOR(brandingPurple,     "#0d3b66", "#0d3b66")
    DECLARE_QGC_NONTHEMED_COLOR(brandingBlue,       "#4fc3e8", "#1e98c1")
    DECLARE_QGC_NONTHEMED_COLOR(toolStripFGColor,   "#5d7398", "#ffffff")

    // Colors not affecting by theming or enable/disable
    DECLARE_QGC_SINGLE_COLOR(mapWidgetBorderLight,          "#ffffff")
    DECLARE_QGC_SINGLE_COLOR(mapWidgetBorderDark,           "#000000")
    DECLARE_QGC_SINGLE_COLOR(mapMissionTrajectory,          "#be781c")
    DECLARE_QGC_SINGLE_COLOR(surveyPolygonInterior,         "green")
    DECLARE_QGC_SINGLE_COLOR(surveyPolygonTerrainCollision, "red")

// Colors for UTM Adapter
#ifdef QGC_UTM_ADAPTER
    DECLARE_QGC_COLOR(switchUTMSP,        "#b0e0e6", "#b0e0e6", "#b0e0e6", "#b0e0e6");
    DECLARE_QGC_COLOR(sliderUTMSP,        "#9370db", "#9370db", "#9370db", "#9370db");
    DECLARE_QGC_COLOR(successNotifyUTMSP, "#3cb371", "#3cb371", "#3cb371", "#3cb371");
#endif
}

void QGCPalette::setColorGroupEnabled(bool enabled)
{
    _colorGroupEnabled = enabled;
    emit paletteChanged();
}

void QGCPalette::setGlobalTheme(Theme newTheme)
{
    // Mobile build does not have themes
    if (_theme != newTheme) {
        _theme = newTheme;
        _signalPaletteChangeToAll();
    }
}

void QGCPalette::_signalPaletteChangeToAll()
{
    // Notify all objects of the new theme
    for (QGCPalette *palette : std::as_const(_paletteObjects)) {
        palette->_signalPaletteChanged();
    }
}

void QGCPalette::_signalPaletteChanged()
{
    emit paletteChanged();
}
