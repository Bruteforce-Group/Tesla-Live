from kivy.properties import NumericProperty
from kivy.uix.screenmanager import Screen


class FaceEnrollScreen(Screen):
    current_step = NumericProperty(1)

    def next_step(self):
        if self.current_step < 3:
            self.current_step += 1

    def prev_step(self):
        if self.current_step > 1:
            self.current_step -= 1
