from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout


class StatCard(BoxLayout):
    title = StringProperty("")
    value = StringProperty("")
    icon = StringProperty("")
