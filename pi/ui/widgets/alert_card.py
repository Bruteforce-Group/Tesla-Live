from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout


class AlertCard(BoxLayout):
    title = StringProperty("")
    subtitle = StringProperty("")
    priority = StringProperty("medium")
    status_color = ListProperty([1, 0.5, 0, 1])
