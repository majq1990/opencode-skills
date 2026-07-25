#!/usr/bin/env python3
"""
SVG Icon Generator Core Logic
Generates SVG icons based on keyword, style, color, and size parameters.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class IconStyle(Enum):
    LINEAR = "linear"
    FILLED = "filled"


class ColorType(Enum):
    SOLID = "solid"
    GRADIENT = "gradient"


class GradientDirection(Enum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    DIAGONAL = "diagonal"


@dataclass
class IconConfig:
    keyword: str
    style: IconStyle
    color_type: ColorType
    color: str  # For solid, or first color for gradient
    color2: Optional[str] = None  # Second color for gradient
    gradient_direction: Optional[GradientDirection] = None
    size: int = 24


# Icon path library
ICON_PATHS = {
    "settings": "M12 15.5a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7zM19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.58 1.69-.98l2.49 1c.23.09.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65z",
    
    "search": "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z M21 21l-4.35-4.35",
    
    "home": "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10",
    
    "user": "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2 M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
    
    "heart": "M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z",
    
    "star": "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z",
    
    "bell": "M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9 M13.73 21a2 2 0 0 1-3.46 0",
    
    "menu": "M3 12h18 M3 6h18 M3 18h18",
    
    "arrow-right": "M5 12h14 M12 5l7 7-7 7",
    
    "arrow-left": "M19 12H5 M12 19l-7-7 7-7",
    
    "arrow-up": "M12 19V5 M5 12l7-7 7 7",
    
    "arrow-down": "M12 5v14 M19 12l-7 7-7-7",
    
    "check": "M20 6L9 17l-5-5",
    
    "close": "M18 6L6 18 M6 6l12 12",
    
    "plus": "M12 5v14 M5 12h14",
    
    "minus": "M5 12h14",
    
    "edit": "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7 M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z",
    
    "trash": "M3 6h18 M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2 M10 11v6 M14 11v6",
    
    "download": "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3",
    
    "upload": "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M17 8l-5-5-5 5 M12 3v12",
    
    "mail": "M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z M22 6l-10 7L2 6",
    
    "lock": "M19 11H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2z M7 11V7a5 5 0 0 1 10 0v4 M12 16v.01",
    
    "unlock": "M19 11H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2z M7 11V7a5 5 0 0 1 9.9-1",
    
    "calendar": "M19 4H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z M16 2v4 M8 2v4 M3 10h18",
    
    "clock": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 6v6l4 2",
    
    "camera": "M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z M12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
    
    "image": "M21 19V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2z M8.5 13.5l2.5 2.5 4-4 5 5 M3 16l5-5 4 4",
    
    "folder": "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
    
    "file": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8",
    
    "link": "M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71 M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71",
    
    "share": "M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8 M16 6l-4-4-4 4 M12 2v13",
    
    "bookmark": "M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z",
    
    "flag": "M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z M4 22v-7",
    
    "tag": "M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z M7 7h.01",
    
    "map-pin": "M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z M12 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
    
    "navigation": "M3 11l19-9-9 19-2-8-8-2z",
    
    "compass": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M16.24 7.76l-2.12 6.36-6.36 2.12 2.12-6.36 6.36-2.12z",
    
    "globe": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M2 12h20 M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z",
    
    "wifi": "M5 12.55a11 11 0 0 1 14.08 0 M1.42 9a16 16 0 0 1 21.16 0 M8.53 16.11a6 16 0 0 1 6.95 0 M12 20h.01",
    
    "battery": "M5 18H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2 M21 10v4",
    
    "sun": "M12 1v2 M12 21v2 M4.22 4.22l1.42 1.42 M18.36 18.36l1.42 1.42 M1 12h2 M21 12h2 M4.22 19.78l1.42-1.42 M18.36 5.64l1.42-1.42 M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10z",
    
    "moon": "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z",
    
    "cloud": "M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z",
    
    "umbrella": "M12 2v16 M12 18a4 4 0 0 0 4 4h0a4 4 0 0 0 4-4 M3 10a9 9 0 0 1 18 0",
    
    "music": "M9 18V5l12-2v13 M9 9l12-2",
    
    "video": "M23 7l-7 5 7 5V7z M1 5h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z",
    
    "mic": "M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z M19 10v2a7 7 0 0 1-14 0v-2 M12 19v4 M8 23h8",
    
    "volume": "M11 5L6 9H2v6h4l5 4V5z M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07",
    
    "volume-off": "M11 5L6 9H2v6h4l5 4V5z M23 9l-6 6 M17 9l6 6",
    
    "play": "M5 3l14 9-14 9V3z",
    
    "pause": "M6 4h4v16H6V4zm8 0h4v16h-4V4z",
    
    "stop": "M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z",
    
    "skip-forward": "M5 4l10 8-10 8V4z M19 5v14",
    
    "skip-back": "M19 20L9 12l10-8v16z M5 19V5",
    
    "shuffle": "M16 3h5v5 M4 20L21 3 M21 16v5h-5 M15 15l6 6 M4 4l5 5",
    
    "repeat": "M17 1l4 4-4 4 M3 11V9a4 4 0 0 1 4-4h14 M7 23l-4-4 4-4 M21 13v2a4 4 0 0 1-4 4H3",
    
    "list": "M8 6h13 M8 12h13 M8 18h13 M3 6h.01 M3 12h.01 M3 18h.01",
    
    "grid": "M3 3h7v7H3z M14 3h7v7h-7z M14 14h7v7h-7z M3 14h7v7H3z",
    
    "layers": "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
    
    "copy": "M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2 M12 2h6a2 2 0 0 1 2 2v10",
    
    "scissors": "M6 9l12 12 M18 9L6 21 M9 5a2.4 2.4 0 0 1 2-1A2.4 2.4 0 0 1 13 5a2.4 2.4 0 0 1-2 1 2.4 2.4 0 0 1-2-1z M19 13a2.4 2.4 0 0 1 2-1 2.4 2.4 0 0 1 2 1 2.4 2.4 0 0 1-2 1 2.4 2.4 0 0 1-2-1z M4 22l8-10",
    
    "filter": "M22 3H2l8 9.46V19l4 2v-8.54L22 3z",
    
    "sliders": "M4 21v-7 M4 10V3 M12 21v-9 M12 8V3 M20 21v-5 M20 12V3 M1 14h6 M9 8h6 M17 16h6",
    
    "more-horizontal": "M5 12h.01 M12 12h.01 M19 12h.01",
    
    "more-vertical": "M12 5h.01 M12 12h.01 M12 19h.01",
    
    "maximize": "M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3",
    
    "minimize": "M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3",
    
    "external-link": "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6 M15 3h6v6 M10 14L21 3",
    
    "code": "M16 18l6-6-6-6 M8 6l-6 6 6 6",
    
    "terminal": "M4 17l6-6-6-6M12 19h8",
    
    "hash": "M4 9h16 M4 15h16 M10 3L8 21 M16 3l-2 18",
    
    "at-sign": "M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z",
    
    "info": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 16v-4 M12 8h.01",
    
    "help-circle": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3 M12 17h.01",
    
    "alert-circle": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 8v4 M12 16h.01",
    
    "alert-triangle": "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z M12 9v4 M12 17h.01",
    
    "check-circle": "M22 11.08V12a10 10 0 1 1-5.93-9.14 M22 4L12 14.01l-3-3",
    
    "x-circle": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M15 9l-6 6 M9 9l6 6",
    
    "truck": "M10 17h4V5H2v12h3m15 0h2a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-5v10z M7 17v2a2 2 0 0 0 2 2h0a2 2 0 0 0 2-2v-2",
    
    "package": "M12.89 1.45l8 4A2 2 0 0 1 22 7.24v9.53a2 2 0 0 1-1.11 1.79l-8 4a2 2 0 0 1-1.79 0l-8-4a2 2 0 0 1-1.1-1.8V7.24a2 2 0 0 1 1.1-1.79l8-4a2 2 0 0 1 1.78 0z M2.32 6.16L12 11l9.68-4.84 M12 22.76V11",
    
    "shopping-cart": "M9 22a1 1 0 1 0 0-2 1 1 0 0 0 0 2z M20 22a1 1 0 1 0 0-2 1 1 0 0 0 0 2z M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6",
    
    "credit-card": "M21 4H3a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z M1 10h22",
    
    "dollar-sign": "M12 1v22 M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6",
    
    "percent": "M19 5L5 19 M6.5 4a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z M17.5 15a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z",
    
    "trending-up": "M23 6l-9.5 9.5-5-5L1 18 M17 6h6v6",
    
    "trending-down": "M23 18l-9.5-9.5-5 5L1 6 M17 18h6v-6",
    
    "activity": "M22 12h-4l-3 9L9 3l-3 9H2",
    
    "bar-chart": "M12 20V10 M18 20V4 M6 20v-4",
    
    "pie-chart": "M21.21 15.89A10 10 0 1 1 8 2.83 M22 12A10 10 0 0 0 12 2v10z",
    
    "users": "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
    
    "message-circle": "M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z",
    
    "phone": "M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z",
    
    "smartphone": "M17 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z M12 18h.01",
    
    "tablet": "M18 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z M12 18h.01",
    
    "monitor": "M20 3H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2z M8 21h8 M12 17v4",
    
    "printer": "M6 9V2h12v7 M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2 M6 14h12v8H6z",
    
    "cpu": "M4 4h16v16H4z M9 9h6v6H9z M9 1v3 M15 1v3 M9 20v3 M15 20v3 M20 9h3 M20 14h3 M1 9h3 M1 14h3",
    
    "database": "M12 2C6.48 2 2 4.24 2 7s4.48 5 10 5 10-2.24 10-5-4.48-5-10-5z M2 7v5c0 2.76 4.48 5 10 5s10-2.24 10-5V7 M2 12v5c0 2.76 4.48 5 10 5s10-2.24 10-5v-5",
    
    "server": "M22 12H2 M6 12v4 M18 12v4 M2 7h20v10H2z M22 7v10",
    
    "shield": "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
    
    "award": "M12 15a7 7 0 1 0 0-14 7 7 0 0 0 0 14z M8.56 2.75c4.37 6.03 6.02 9.42 8.03 17.72m2.54-15.38c-3.72 4.35-8.94 5.66-16.88 5.85m19.5 1.9c-3.5-.93-6.63-.82-8.94 0-2.58.92-5.01 2.86-7.44 6.32",
    
    "zap": "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
    
    "anchor": "M12 2a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z M5 12H2a10 10 0 0 0 20 0h-3 M12 2v18",
    
    "aperture": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 2v20 M2 12h20 M4.93 4.93l14.14 14.14 M19.07 4.93L4.93 19.07",
    
    "box": "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z M3.27 6.96L12 12.01l8.73-5.05 M12 22.08V12",
    
    "briefcase": "M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16",
    
    "cast": "M2 16.1A5 5 0 0 1 5.9 20M2 12.05A9 9 0 0 1 9.95 20M2 8V6a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-6 M2 20h.01",
    
    "chrome": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 8v8 M2.05 12H12 M12 2.05c4.95 0 9.09 3.43 10.18 8.05",
    
    "circle": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z",
    
    "square": "M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z",
    
    "triangle": "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z",
    
    "hexagon": "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z",
    
    "octagon": "M7.86 2h8.28L22 7.86v8.28L16.14 22H7.86L2 16.14V7.86L7.86 2z",
    
    "diamond": "M6 2L2 8l10 14L22 8l-4-6H6z",
    
    "crosshair": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 2v4 M12 18v4 M2 12h4 M18 12h4",
    
    "target": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12z M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
    
    "rss": "M4 11a9 9 0 0 1 9 9 M4 4a16 16 0 0 1 16 16 M5 19a1 1 0 1 0 0-2 1 1 0 0 0 0 2z",
    
    "bluetooth": "M6.5 6.5l11 11L12 23V1l5.5 5.5-11 11",
    
    "airplay": "M5 17H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-1 M12 15l5 6H7l5-6z",
    
    "command": "M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z",
    
    "feather": "M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z M16 8L2 22 M17.5 15H9",
    
    "figma": "M5 5.5A3.5 3.5 0 0 1 8.5 2H12v7H8.5A3.5 3.5 0 0 1 5 5.5z M12 2h3.5a3.5 3.5 0 1 1 0 7H12V2z M12 9.5h3.5a3.5 3.5 0 1 1 0 7H12v-7z M5 12.5A3.5 3.5 0 0 1 8.5 9H12v7H8.5A3.5 3.5 0 0 1 5 12.5z M5 19.5A3.5 3.5 0 0 1 8.5 16H12v3.5a3.5 3.5 0 1 1-7 0z",
    
    "github": "M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22",
    
    "gitlab": "M22.65 14.39L12 22.13 1.35 14.39a.84.84 0 0 1-.3-.94l1.22-3.78 2.44-7.51A.42.42 0 0 1 4.82 2a.43.43 0 0 1 .58 0 .42.42 0 0 1 .11.18l2.44 7.49h8.1l2.44-7.51A.42.42 0 0 1 18.6 2a.43.43 0 0 1 .58 0 .42.42 0 0 1 .11.18l2.44 7.51L23 13.45a.84.84 0 0 1-.35.94z",
    
    "twitter": "M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z",
    
    "facebook": "M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z",
    
    "instagram": "M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z M17.5 6.5h.01 M7.5 2h9a5.5 5.5 0 0 1 5.5 5.5v9a5.5 5.5 0 0 1-5.5 5.5h-9A5.5 5.5 0 0 1 2 16.5v-9A5.5 5.5 0 0 1 7.5 2z",
    
    "linkedin": "M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z M2 9h4v12H2z M4 6a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
    
    "youtube": "M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z M9.75 15.02V8.48l5.75 3.27-5.75 3.27z",
    
    "slack": "M14.5 10c-.83 0-1.5-.67-1.5-1.5v-5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5z M19.5 10H17V5.5a2.5 2.5 0 1 1 5 0v2a2.5 2.5 0 0 1-2.5 2.5z M10 14.5c0-.83.67-1.5 1.5-1.5h5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5h-5c-.83 0-1.5-.67-1.5-1.5z M10 19.5v-2.5h4.5a2.5 2.5 0 1 1 0 5H12.5a2.5 2.5 0 0 1-2.5-2.5z M9.5 10c.83 0 1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5S8 17.33 8 16.5v-5C8 10.67 8.67 10 9.5 10z M4.5 10H7v4.5a2.5 2.5 0 1 1-5 0V12.5A2.5 2.5 0 0 1 4.5 10z M10 9.5c0 .83-.67 1.5-1.5 1.5h-5c-.83 0-1.5-.67-1.5-1.5S2.67 8 3.5 8h5c.83 0 1.5.67 1.5 1.5z M10 4.5v2.5H5.5a2.5 2.5 0 1 1 0-5h2A2.5 2.5 0 0 1 10 4.5z",
    
    "trello": "M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z M10 7v10 M14 7v7",
    
    "twitch": "M21 2H3v16h5v4l4-4h5l4-4V2z M11 11V7 M16 11V7",
    
    "dribbble": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M8.56 2.75c4.37 6.03 6.02 9.42 8.03 17.72m2.54-15.38c-3.72 4.35-8.94 5.66-16.88 5.85m19.5 1.9c-3.5-.93-6.63-.82-8.94 0-2.58.92-5.01 2.86-7.44 6.32",
    
    "figma": "M5 5.5A3.5 3.5 0 0 1 8.5 2H12v7H8.5A3.5 3.5 0 0 1 5 5.5z M12 2h3.5a3.5 3.5 0 1 1 0 7H12V2z M12 9.5h3.5a3.5 3.5 0 1 1 0 7H12v-7z M5 12.5A3.5 3.5 0 0 1 8.5 9H12v7H8.5A3.5 3.5 0 0 1 5 12.5z M5 19.5A3.5 3.5 0 0 1 8.5 16H12v3.5a3.5 3.5 0 1 1-7 0z",
    
    "anchor": "M12 2a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z M5 12H2a10 10 0 0 0 20 0h-3 M12 2v18",
    
    "aperture": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 2v20 M2 12h20 M4.93 4.93l14.14 14.14 M19.07 4.93L4.93 19.07",
    
    "box": "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z M3.27 6.96L12 12.01l8.73-5.05 M12 22.08V12",
}


def get_icon_path(keyword: str) -> Optional[str]:
    """Get icon path data by keyword."""
    keyword = keyword.lower().strip()
    
    # Direct match
    if keyword in ICON_PATHS:
        return ICON_PATHS[keyword]
    
    # Try common variations
    variations = {
        "setting": "settings",
        "gear": "settings",
        "find": "search",
        "magnifier": "search",
        "house": "home",
        "main": "home",
        "person": "user",
        "profile": "user",
        "account": "user",
        "love": "heart",
        "like": "heart",
        "favorite": "star",
        "favourite": "star",
        "rate": "star",
        "notification": "bell",
        "alert": "bell",
        "hamburger": "menu",
        "bars": "menu",
        "nav": "menu",
        "right": "arrow-right",
        "left": "arrow-left",
        "up": "arrow-up",
        "down": "arrow-down",
        "next": "arrow-right",
        "prev": "arrow-left",
        "previous": "arrow-left",
        "back": "arrow-left",
        "forward": "arrow-right",
        "tick": "check",
        "done": "check",
        "ok": "check",
        "success": "check",
        "x": "close",
        "cancel": "close",
        "remove": "close",
        "delete": "close",
        "clear": "close",
        "add": "plus",
        "create": "plus",
        "new": "plus",
        "subtract": "minus",
        "reduce": "minus",
        "write": "edit",
        "modify": "edit",
        "change": "edit",
        "update": "edit",
        "bin": "trash",
        "garbage": "trash",
        "rubbish": "trash",
        "save": "download",
        "export": "download",
        "import": "upload",
        "send": "upload",
        "email": "mail",
        "envelope": "mail",
        "letter": "mail",
        "secure": "lock",
        "password": "lock",
        "private": "lock",
        "date": "calendar",
        "schedule": "calendar",
        "event": "calendar",
        "time": "clock",
        "watch": "clock",
        "hour": "clock",
        "photo": "camera",
        "picture": "camera",
        "gallery": "image",
        "photo": "image",
        "directory": "folder",
        "dir": "folder",
        "document": "file",
        "doc": "file",
        "paper": "file",
        "url": "link",
        "hyperlink": "link",
        "connection": "link",
        "send": "share",
        "distribute": "share",
        "distribute": "share",
        "bookmark": "bookmark",
        "save": "bookmark",
        "flag": "flag",
        "mark": "flag",
        "tag": "tag",
        "label": "tag",
        "location": "map-pin",
        "place": "map-pin",
        "pin": "map-pin",
        "gps": "map-pin",
        "navigate": "navigation",
        "direction": "navigation",
        "compass": "compass",
        "world": "globe",
        "earth": "globe",
        "internet": "globe",
        "web": "globe",
        "wireless": "wifi",
        "signal": "wifi",
        "network": "wifi",
        "battery": "battery",
        "power": "battery",
        "charge": "battery",
        "sun": "sun",
        "day": "sun",
        "brightness": "sun",
        "moon": "moon",
        "night": "moon",
        "dark": "moon",
        "cloud": "cloud",
        "weather": "cloud",
        "rain": "umbrella",
        "protection": "umbrella",
        "music": "music",
        "song": "music",
        "audio": "music",
        "video": "video",
        "movie": "video",
        "film": "video",
        "microphone": "mic",
        "voice": "mic",
        "record": "mic",
        "sound": "volume",
        "speaker": "volume",
        "audio": "volume",
        "mute": "volume-off",
        "silent": "volume-off",
        "play": "play",
        "start": "play",
        "pause": "pause",
        "stop": "stop",
        "end": "stop",
        "skip": "skip-forward",
        "next": "skip-forward",
        "previous": "skip-back",
        "back": "skip-back",
        "random": "shuffle",
        "mix": "shuffle",
        "loop": "repeat",
        "cycle": "repeat",
        "list": "list",
        "items": "list",
        "grid": "grid",
        "tiles": "grid",
        "layers": "layers",
        "stack": "layers",
        "duplicate": "copy",
        "clone": "copy",
        "cut": "scissors",
        "filter": "filter",
        "sort": "filter",
        "sliders": "sliders",
        "adjust": "sliders",
        "more": "more-horizontal",
        "options": "more-horizontal",
        "expand": "maximize",
        "fullscreen": "maximize",
        "contract": "minimize",
        "exit": "minimize",
        "external": "external-link",
        "open": "external-link",
        "code": "code",
        "programming": "code",
        "dev": "code",
        "terminal": "terminal",
        "console": "terminal",
        "command": "terminal",
        "hash": "hash",
        "number": "hash",
        "at": "at-sign",
        "mention": "at-sign",
        "info": "info",
        "information": "info",
        "about": "info",
        "help": "help-circle",
        "question": "help-circle",
        "support": "help-circle",
        "warning": "alert-triangle",
        "caution": "alert-triangle",
        "error": "alert-circle",
        "danger": "alert-circle",
        "success": "check-circle",
        "fail": "x-circle",
        "failed": "x-circle",
        "delivery": "truck",
        "shipping": "truck",
        "transport": "truck",
        "package": "package",
        "parcel": "package",
        "box": "package",
        "cart": "shopping-cart",
        "basket": "shopping-cart",
        "shop": "shopping-cart",
        "payment": "credit-card",
        "card": "credit-card",
        "money": "dollar-sign",
        "cash": "dollar-sign",
        "currency": "dollar-sign",
        "percent": "percent",
        "percentage": "percent",
        "discount": "percent",
        "growth": "trending-up",
        "increase": "trending-up",
        "rise": "trending-up",
        "decline": "trending-down",
        "decrease": "trending-down",
        "fall": "trending-down",
        "activity": "activity",
        "pulse": "activity",
        "chart": "bar-chart",
        "graph": "bar-chart",
        "statistics": "bar-chart",
        "pie": "pie-chart",
        "distribution": "pie-chart",
        "group": "users",
        "team": "users",
        "people": "users",
        "chat": "message-circle",
        "message": "message-circle",
        "comment": "message-circle",
        "talk": "message-circle",
        "phone": "phone",
        "call": "phone",
        "mobile": "smartphone",
        "cell": "smartphone",
        "tablet": "tablet",
        "ipad": "tablet",
        "monitor": "monitor",
        "desktop": "monitor",
        "screen": "monitor",
        "display": "monitor",
        "print": "printer",
        "cpu": "cpu",
        "processor": "cpu",
        "database": "database",
        "storage": "database",
        "server": "server",
        "host": "server",
        "shield": "shield",
        "security": "shield",
        "protect": "shield",
        "award": "award",
        "trophy": "award",
        "prize": "award",
        "achievement": "award",
        "bolt": "zap",
        "flash": "zap",
        "lightning": "zap",
        "power": "zap",
        "energy": "zap",
        "anchor": "anchor",
        "link": "anchor",
        "aperture": "aperture",
        "camera": "aperture",
        "lens": "aperture",
        "package": "box",
        "container": "box",
        "briefcase": "briefcase",
        "work": "briefcase",
        "business": "briefcase",
        "suitcase": "briefcase",
        "cast": "cast",
        "stream": "cast",
        "broadcast": "cast",
        "chrome": "chrome",
        "browser": "chrome",
        "google": "chrome",
        "circle": "circle",
        "round": "circle",
        "square": "square",
        "rectangle": "square",
        "triangle": "triangle",
        "pyramid": "triangle",
        "hexagon": "hexagon",
        "octagon": "octagon",
        "diamond": "diamond",
        "rhombus": "diamond",
        "crosshair": "crosshair",
        "aim": "crosshair",
        "focus": "crosshair",
        "target": "target",
        "goal": "target",
        "objective": "target",
        "rss": "rss",
        "feed": "rss",
        "subscribe": "rss",
        "bluetooth": "bluetooth",
        "wireless": "bluetooth",
        "airplay": "airplay",
        "screen": "airplay",
        "mirror": "airplay",
        "command": "command",
        "cmd": "command",
        "key": "command",
        "feather": "feather",
        "pen": "feather",
        "write": "feather",
        "github": "github",
        "git": "github",
        "gitlab": "gitlab",
        "twitter": "twitter",
        "x": "twitter",
        "tweet": "twitter",
        "facebook": "facebook",
        "fb": "facebook",
        "instagram": "instagram",
        "ig": "instagram",
        "linkedin": "linkedin",
        "youtube": "youtube",
        "yt": "youtube",
        "slack": "slack",
        "trello": "trello",
        "twitch": "twitch",
        "dribbble": "dribbble",
        "figma": "figma",
    }
    
    if keyword in variations:
        mapped = variations[keyword]
        return ICON_PATHS.get(mapped)
    
    return None


def generate_linear_icon(path_data: str, color: str, size: int = 24) -> str:
    """Generate a linear/outline style SVG icon."""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="{path_data}"/>
</svg>'''
    return svg


def generate_filled_solid_icon(path_data: str, color: str, size: int = 24) -> str:
    """Generate a filled solid color SVG icon."""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="{color}">
  <path d="{path_data}"/>
</svg>'''
    return svg


def generate_filled_gradient_icon(
    path_data: str, 
    color1: str, 
    color2: str, 
    direction: GradientDirection,
    size: int = 24
) -> str:
    """Generate a filled gradient SVG icon."""
    
    # Determine gradient coordinates based on direction
    if direction == GradientDirection.VERTICAL:
        x1, y1, x2, y2 = "0", "0", "0", "1"
    elif direction == GradientDirection.HORIZONTAL:
        x1, y1, x2, y2 = "0", "0", "1", "0"
    else:  # DIAGONAL
        x1, y1, x2, y2 = "0", "0", "1", "1"
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none">
  <defs>
    <linearGradient id="grad" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">
      <stop offset="0%" stop-color="{color1}"/>
      <stop offset="100%" stop-color="{color2}"/>
    </linearGradient>
  </defs>
  <path fill="url(#grad)" d="{path_data}"/>
</svg>'''
    return svg


def generate_icon(config: IconConfig) -> str:
    """Generate an SVG icon based on configuration."""
    
    # Get icon path
    path_data = get_icon_path(config.keyword)
    if not path_data:
        raise ValueError(f"Unknown icon keyword: {config.keyword}")
    
    # Generate based on style
    if config.style == IconStyle.LINEAR:
        return generate_linear_icon(path_data, config.color, config.size)
    else:  # FILLED
        if config.color_type == ColorType.SOLID:
            return generate_filled_solid_icon(path_data, config.color, config.size)
        else:  # GRADIENT
            if not config.color2:
                raise ValueError("Gradient requires two colors")
            return generate_filled_gradient_icon(
                path_data, 
                config.color, 
                config.color2,
                config.gradient_direction or GradientDirection.VERTICAL,
                config.size
            )


def generate_filename(config: IconConfig) -> str:
    """Generate a filename for the icon."""
    style_str = config.style.value
    size_str = config.size
    
    if config.color_type == ColorType.SOLID:
        color_str = config.color.replace("#", "")
    else:
        color_str = f"grad-{config.gradient_direction.value if config.gradient_direction else 'vert'}"
    
    return f"{config.keyword}-{style_str}-{color_str}-{size_str}.svg"


if __name__ == "__main__":
    # Example usage
    config = IconConfig(
        keyword="settings",
        style=IconStyle.FILLED,
        color_type=ColorType.GRADIENT,
        color="#ffffff",
        color2="#2563eb",
        gradient_direction=GradientDirection.VERTICAL,
        size=24
    )
    
    svg = generate_icon(config)
    print(svg)
    print(f"\nFilename: {generate_filename(config)}")
