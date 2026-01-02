# Widget package for Kivy UI components
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView

from .alert_card import AlertCard
from .camera_preview import CameraPreview
from .detection_card import DetectionCard
from .stat_card import StatCard
from .status_bar import StatusBar

__all__ = [
    "ActionButton",
    "AlertCard",
    "CameraPreview",
    "DetectionCard",
    "DetectionList",
    "StatCard",
    "StatusBadge",
    "StatusBar",
    "StatusIcon",
    "StepIndicator",
]


class StatusBadge(BoxLayout):
    icon = StringProperty("")
    text = StringProperty("")


class StatusIcon(Label):
    icon = StringProperty("")


class ActionButton(Button):
    pass


class DetectionList(RecycleView):
    pass


class StepIndicator(BoxLayout):
    current_step = NumericProperty(1)
    total_steps = NumericProperty(3)
