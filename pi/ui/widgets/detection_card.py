from kivy.properties import StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout


class DetectionCard(BoxLayout):
    timestamp = StringProperty("")
    plate = StringProperty("")
    vehicle_info = StringProperty("")
    colour = StringProperty("")
    status_icon = StringProperty("check-circle")
    status_color = ListProperty([0, 1, 0, 1])
    bg_color = ListProperty([0.1, 0.1, 0.1, 1])
