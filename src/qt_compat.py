"""Small PyQt6 compatibility layer for the migrated Qt widget code.

The application source historically used PySide6's flat enum aliases. PyQt6
keeps the same enum values but exposes most of them through scoped enums. The
aliases below let the existing UI modules migrate incrementally while keeping
the public code on PyQt6.
"""

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QFont, QPainter
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialogButtonBox,
    QDialog,
    QFrame,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QListView,
    QListWidget,
    QMessageBox,
    QSizePolicy,
    QSlider,
    QStyle,
    QTreeWidget,
    QGraphicsView,
)
from PyQt6.QtGui import QFontDatabase, QImage


def _alias(owner, name, value):
    if not hasattr(owner, name):
        setattr(owner, name, value)


for name in (
    'AlignCenter', 'AlignRight', 'AlignLeft', 'AlignTop', 'AlignBottom',
    'AlignVCenter', 'AlignHCenter',
):
    _alias(Qt, name, getattr(Qt.AlignmentFlag, name))

for name in ('Checked', 'Unchecked'):
    _alias(Qt, name, getattr(Qt.CheckState, name))

for name in ('Horizontal', 'Vertical'):
    _alias(Qt, name, getattr(Qt.Orientation, name))

for name in ('UserRole', 'DisplayRole'):
    _alias(Qt, name, getattr(Qt.ItemDataRole, name))

for name in ('PointingHandCursor', 'ArrowCursor', 'CrossCursor'):
    _alias(Qt, name, getattr(Qt.CursorShape, name))

for name in ('KeepAspectRatio', 'IgnoreAspectRatio'):
    _alias(Qt, name, getattr(Qt.AspectRatioMode, name))
_alias(Qt, 'SmoothTransformation', Qt.TransformationMode.SmoothTransformation)

for name in (
    'WA_TranslucentBackground', 'WA_TransparentForMouseEvents',
    'WA_StyledBackground', 'WA_ShowWithoutActivating', 'WA_Hover',
    'WA_DeleteOnClose',
):
    _alias(Qt, name, getattr(Qt.WidgetAttribute, name))

for name in (
    'Window', 'FramelessWindowHint', 'WindowStaysOnTopHint', 'Tool',
    'Widget', 'Dialog', 'Popup', 'ToolTip',
):
    _alias(Qt, name, getattr(Qt.WindowType, name))

_alias(Qt, 'ApplicationModal', Qt.WindowModality.ApplicationModal)
for name in ('ScrollBarAlwaysOff', 'ScrollBarAsNeeded'):
    _alias(Qt, name, getattr(Qt.ScrollBarPolicy, name))
for name in ('ControlModifier', 'ShiftModifier', 'NoModifier'):
    _alias(Qt, name, getattr(Qt.KeyboardModifier, name))
for name in ('LeftButton', 'RightButton', 'NoButton'):
    _alias(Qt, name, getattr(Qt.MouseButton, name))
for name in ('ItemIsUserCheckable', 'ItemIsEditable', 'ItemIsSelectable', 'ItemIsEnabled'):
    _alias(Qt, name, getattr(Qt.ItemFlag, name))
for name in ('Key_Escape', 'Key_E', 'Key_F', 'Key_Q', 'Key_A', 'Key_C', 'Key_L', 'Key_F5'):
    _alias(Qt, name, getattr(Qt.Key, name))
_alias(Qt, 'FindChildrenRecursively', Qt.FindChildOption.FindChildrenRecursively)
_alias(Qt, 'MoveAction', Qt.DropAction.MoveAction)
_alias(Qt, 'FlatCap', Qt.PenCapStyle.FlatCap)
_alias(Qt, 'RoundJoin', Qt.PenJoinStyle.RoundJoin)
_alias(Qt, 'NoBrush', Qt.BrushStyle.NoBrush)
_alias(Qt, 'NoPen', Qt.PenStyle.NoPen)
_alias(Qt, 'DashLine', Qt.PenStyle.DashLine)
for name in ('black', 'blue', 'green', 'red', 'white', 'yellow', 'transparent'):
    _alias(Qt, name, getattr(Qt.GlobalColor, name))
_alias(Qt, 'RichText', Qt.TextFormat.RichText)
_alias(Qt, 'CustomContextMenu', Qt.ContextMenuPolicy.CustomContextMenu)
_alias(Qt, 'AscendingOrder', Qt.SortOrder.AscendingOrder)
_alias(Qt, 'NoFocus', Qt.FocusPolicy.NoFocus)
for name in ('LinksAccessibleByMouse', 'TextSelectableByMouse'):
    _alias(Qt, name, getattr(Qt.TextInteractionFlag, name))
_alias(Qt, 'ElideRight', Qt.TextElideMode.ElideRight)

_alias(QDialog, 'Accepted', QDialog.DialogCode.Accepted)
for name in ('Yes', 'No', 'Ok'):
    _alias(QMessageBox, name, getattr(QMessageBox.StandardButton, name))
for name in ('Question', 'Warning', 'Critical', 'Information'):
    _alias(QMessageBox, name, getattr(QMessageBox.Icon, name))
for name in ('AcceptRole', 'RejectRole', 'DestructiveRole'):
    _alias(QMessageBox, name, getattr(QMessageBox.ButtonRole, name))

_alias(QStyle, 'CE_PushButton', QStyle.ControlElement.CE_PushButton)
for name in ('State_MouseOver', 'State_Selected'):
    _alias(QStyle, name, getattr(QStyle.StateFlag, name))
for name in ('Stretch', 'ResizeToContents'):
    _alias(QHeaderView, name, getattr(QHeaderView.ResizeMode, name))
for name in ('StyledPanel', 'Box', 'HLine', 'VLine', 'NoFrame'):
    _alias(QFrame, name, getattr(QFrame.Shape, name))
for name in ('Raised', 'Sunken'):
    _alias(QFrame, name, getattr(QFrame.Shadow, name))
_alias(QSlider, 'TicksBelow', QSlider.TickPosition.TicksBelow)
for name in ('NoSelection', 'SingleSelection', 'ExtendedSelection', 'SelectRows', 'NoDragDrop'):
    for owner in (QAbstractItemView, QTreeWidget):
        if hasattr(owner, name):
            continue
        enum = QAbstractItemView.SelectionMode if name in ('NoSelection', 'SingleSelection', 'ExtendedSelection') else (
            QAbstractItemView.SelectionBehavior if name == 'SelectRows' else QAbstractItemView.DragDropMode
        )
        _alias(owner, name, getattr(enum, name))
for name in ('Adjust', 'IconMode'):
    _alias(QListWidget, name, getattr(QListView.ResizeMode if name == 'Adjust' else QListView.ViewMode, name))
for name in ('IntInput', 'TextInput'):
    _alias(QInputDialog, name, getattr(QInputDialog.InputMode, name))
for name in ('Resize', 'Leave', 'MouseButtonPress', 'Close', 'Hide', 'Wheel'):
    _alias(QEvent, name, getattr(QEvent.Type, name))
for name in ('Antialiasing', 'TextAntialiasing', 'SmoothPixmapTransform'):
    _alias(QPainter, name, getattr(QPainter.RenderHint, name))
for name in ('DestinationIn', 'Plus'):
    _alias(QPainter, f'CompositionMode_{name}', getattr(QPainter.CompositionMode, f'CompositionMode_{name}'))
_alias(QFont, 'Bold', QFont.Weight.Bold)
for name in ('Fixed', 'Minimum', 'Maximum', 'Preferred', 'MinimumExpanding', 'Expanding', 'Ignored'):
    _alias(QSizePolicy, name, getattr(QSizePolicy.Policy, name))
_alias(QLineEdit, 'Normal', QLineEdit.EchoMode.Normal)
_alias(QDialogButtonBox, 'Ok', QDialogButtonBox.StandardButton.Ok)
for name in ('AnchorUnderMouse',):
    _alias(QGraphicsView, name, getattr(QGraphicsView.ViewportAnchor, name))
_alias(QGraphicsView, 'ScrollHandDrag', QGraphicsView.DragMode.ScrollHandDrag)
from PyQt6.QtWidgets import QGraphicsItem as _QGraphicsItem
for name in ('ItemIgnoresTransformations', 'ItemIsSelectable', 'ItemIsMovable', 'ItemIsFocusable',
             'ItemSendsGeometryChanges', 'ItemUsesExtendedStyleOption'):
    _alias(_QGraphicsItem, name, getattr(_QGraphicsItem.GraphicsItemFlag, name))
_alias(QFontDatabase, 'FixedFont', QFontDatabase.SystemFont.FixedFont)
_alias(QImage, 'Format_RGBA8888', QImage.Format.Format_RGBA8888)
