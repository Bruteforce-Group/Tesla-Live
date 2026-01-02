# Widget package for Kivy UI components
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.properties import StringProperty, ListProperty, NumericProperty

from .status_bar import StatusBar
from .stat_card import StatCard
from .detection_card import DetectionCard
from .alert_card import AlertCard
from .camera_preview import CameraPreview


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
