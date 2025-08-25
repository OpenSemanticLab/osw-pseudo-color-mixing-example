from pseudo_color_mixer import PseudoColorMixer, ColorMixerInput, PseudoColorMixing
from osw.model.entity import RGBValue
from osw.express import OswExpress
from osw.core import OSW
import panel as pn
from io import BytesIO
import time
from threading import Thread
from datetime import datetime

class PseudoColorMixerPanel:
    def __init__(self, color_mixer: PseudoColorMixer, osw_obj:OSW=None):
        self.color_mixer = color_mixer
        self.osw_obj = osw_obj
        self.current_input = ColorMixerInput(red_fraction=0, green_fraction=0, blue_fraction=0)
        self.last_beaker_svg = None
        self.build_panel()

    def build_panel(self):

        # a panel to specify an input mix
        self.r_input = pn.widgets.FloatInput(name='Red Fraction', value=self.current_input.red_fraction, start=0.0,
                                             end=1.0, step=0.1)
        self.g_input = pn.widgets.FloatInput(name='Green Fraction', value=self.current_input.green_fraction, start=0.0, end=1.0, step=0.1)
        self.b_input = pn.widgets.FloatInput(name='Blue Fraction', value=self.current_input.blue_fraction, start=0.0, end=1.0, step=0.1)

        # a button to trigger the color mixing
        self.mix_button = pn.widgets.Button(name='Start mixing', button_type='primary')
        self.mix_button.on_click(self.color_mixing_callback)

        self.input_column = pn.Column(self.r_input, self.g_input, self.b_input, self.mix_button)

        # an image panel to display the color mixing results
        self.image_panel = pn.pane.SVG( width=300, height=300)
        self.result_markdown = pn.pane.Markdown("No Result Yet")
        self.result_column = pn.Column( self.image_panel, self.result_markdown,)

        self.document_result_button = pn.widgets.Button(name='Document last result', button_type='primary')
        self.document_result_button.on_click(self.document_last_result_callback)
        self.document_result_alert = pn.pane.Alert("Click the button to document the last result in the OSW.",
                                                      alert_type='info')

        self.start_continuous_button = pn.widgets.Button(name='Start continuous loop', button_type='primary')
        self.start_continuous_button.on_click(self.start_loop_callback)

        self.stop_continuous_button = pn.widgets.Button(name='Stop continuous loop', button_type='primary')
        self.stop_continuous_button.on_click(self.stop_loop_callback)

        self.continuous_loop_alert = pn.pane.Alert("Click the button to start the continuous loop for checking open tasks in the OSW.",
                                                      alert_type='info')

        self.osw_column = pn.Column(self.document_result_button, self.document_result_alert,
                                    self.start_continuous_button, self.stop_continuous_button, self.continuous_loop_alert)

        self.main_row = pn.Row(self.input_column, self.result_column, self.osw_column)

        self.header_markdown = pn.pane.Markdown(
            """
            # Pseudo Color Mixer
            This panel allows you to simulate mixing colors using RGB fractions. (rest: white, subtractive color 
            mixing)
            Adjust the fractions and click 'Start mixing' to see the result.        
            """
        )
        self.main_column = pn.Column(self.header_markdown, self.main_row)

    def __panel__(self):
        return self.main_column

    def input_callback(self):
        self.current_input = RGBValue(red_value = self.r_input.value
                                      , green_value = self.g_input.value
                                      , blue_value = self.b_input.value)

    def color_mixing_callback(self, event):
        self.input_callback()
        color_mixed = self.color_mixer.subtractive_color_mixing(ColorMixerInput(
            red_fraction=self.r_input.value,
            green_fraction=self.g_input.value,
            blue_fraction=self.b_input.value
        ))
        self.last_beaker_svg = self.color_mixer.create_beaker_svg(80, color_mixed)

        svg_bytes = BytesIO()
        svg_bytes.write(self.last_beaker_svg.encode('utf-8'))

        self.image_panel.object = svg_bytes#self.last_beaker_svg
        self.result_markdown.object = (f"**Resulting Color:**\nRed: {color_mixed.red_value}, "
                                       f"Green: {color_mixed.green_value},Blue: {color_mixed.blue_value}")
        self.document_result_alert.object = (f"Click the button to document the last result in the OSW.")
        self.document_result_alert.alert_type = "info"

    def document_last_result_callback(self, event, process_instance = None):
        print("documenting last result")
        self.document_result_alert.object = (f"documentation in progress...")
        self.document_result_alert.alert_type  = "warning"

        try:
            process_link, output_link = self.color_mixer.document_last_color_mixing(self.osw_obj, process_instance =
            process_instance)

            ## write the links to the result in the markdown
            self.document_result_alert.object = (f"Documentation of last Result:\n"
                                                f"[Link]({process_link})\n"
                                                )

            self.document_result_alert.alert_type = "success"
        except Exception as e:
            self.document_result_alert.object = (f"Error documenting last result: {e}")
            self.document_result_alert.alert_type = "danger"
            print("Error documenting last result:", e)

    def check_for_open_tasks(self, osw_obj):
        """Checks if there is an instance of PseudoColorMixing that has its flag"""
        open_tasks = osw_obj.site.semantic_search("[[Category:OSW25e748d2fa7a4b19a6a74e0b7f2d0211]][["
                                                       "ShallBeExecuted::true]]")

        return open_tasks

    def continuous_loop(self, osw_obj: OSW):
        self.stop_flag = False
        while not self.stop_flag:
            open_tasks = self.check_for_open_tasks(osw_obj)
            if len(open_tasks) > 0:
                # download task and work on it
                mixing_process: PseudoColorMixing = osw_obj.load_entity(open_tasks[0])

                self.continuous_loop_alert.object = (f"Found open task at {datetime.now()}. "
                                                     f"Working on it now: {mixing_process}")
                self.continuous_loop_alert.alert_type = "success"

                print("mixing_process:", mixing_process)
                self.r_input.value = mixing_process.red_fraction
                self.g_input.value = mixing_process.green_fraction
                self.b_input.value = mixing_process.blue_fraction
                self.color_mixing_callback(event=None)

                self.document_last_result_callback(event=None, process_instance=mixing_process)

            else:
                self.continuous_loop_alert.object = (f"No open tasks found at {datetime.now()}. Waiting for 2 "
                                                     f"seconds "
                                                     f"before "
                                                     f"checking again.")
                self.continuous_loop_alert.alert_type = "success"
                time.sleep(2)

    def start_continuous_loop(self, osw_obj):
        self.thread = Thread(target=self.continuous_loop, args=(osw_obj,))
        if self.thread is not None:
            if self.thread.is_alive():
                print("Thread is already running.")
                return
        self.thread.start()

    def stop_continuous_loop(self):
        self.stop_flag = True

    def start_loop_callback(self,event):
        try:
            self.start_continuous_loop(osw_obj=self.osw_obj)
            self.continuous_loop_alert.object = (f"Continuous loop started. It will check for open tasks every 2 seconds.")
            self.continuous_loop_alert.alert_type = "success"
        except Exception as e:
            self.continuous_loop_alert.object = (f"Error starting continuous loop: {e}")
            self.continuous_loop_alert.alert_type = "danger"

    def stop_loop_callback(self, event):
        self.stop_continuous_loop()

        ## wait for thread to be finished
        while True:
            if self.thread is None:
                break
            if not self.thread.is_alive():
                break
            time.sleep(0.1)
        self.continuous_loop_alert.object = (f"Continuous loop stopped. Click on 'Start continuous loop' to start it again.")
        self.continuous_loop_alert.alert_type = "info"




if __name__ == '__main__':

    serve_app= True
    if serve_app:
        color_mixer = PseudoColorMixer()
        osw_obj = OswExpress(
            # domain="demo.open-semantic-lab.org"
            # domain = "mat-o-lab.open-semantic-lab.org",
            domain="wiki-dev.open-semantic-lab.org"
        )
        mixer_panel = PseudoColorMixerPanel(color_mixer, osw_obj = osw_obj)

        pn.serve(mixer_panel, port = 20200, threaded=True)

    test_check_for_open_tasks = False

    if test_check_for_open_tasks:
        color_mixer = PseudoColorMixer()
        osw_obj = OswExpress(
            # domain="demo.open-semantic-lab.org"
            # domain = "mat-o-lab.open-semantic-lab.org",
            domain="wiki-dev.open-semantic-lab.org"
        )
        mixer_panel = PseudoColorMixerPanel(color_mixer, osw_obj=osw_obj)

        open_tasks = color_mixer.check_for_open_tasks(osw_obj)
        print(f"Open tasks found: {len(open_tasks)}")
        print(open_tasks)

