from pseudo_color_mixer import PseudoColorMixer, ColorMixerInput, PseudoColorMixing
from osw.model.entity import RGBValue
from osw.express import OswExpress
from osw.core import OSW
import panel as pn
import plotly.express as px
import numpy as np
from io import BytesIO
import time
from threading import Thread
from datetime import datetime

class ColorDatabaseVisualizationPanel():
    def __init__(self, osw_obj:OSW=None):
        self.osw_obj = osw_obj
        self.build_panel()
        self.update_visualization()

    def build_panel(self):

        self.visualization_panel = pn.pane.Plotly()

        self.visualization_col = pn.Column(self.visualization_panel)
        self.update_visualization_button = pn.widgets.Button(name = "update visualization")
        self.update_visualization_button.on_click(self.update_visualization_callback)


        self.controls_col = pn.Column(self.update_visualization_button)
        self.main_row = pn.Row(self.visualization_col , self.controls_col)

    def __panel__(self):
        return self.main_row

    def get_inputs_outputs(self):
        ## query for all PseudoColorMixing processes
        query = """[[Category:OSW25e748d2fa7a4b19a6a74e0b7f2d0211]]
               |?ShallBeExecuted=execute
               |?HasRedMixtureFraction=red_fraction
               |?HasGreenMixtureFraction=green_fraction
               |?HasBlueMixtureFraction=blue_fraction
               |?HasOutput.HasColor.HasRedValue=red_value
               |?HasOutput.HasColor.HasGreenValue=green_value
               |?HasOutput.HasColor.HasBlueValue=blue_value"""
        res = self.osw_obj.mw_site.api("ask", query=query, format="json", limit=1000)
        print(res)

        res_dict = res["query"]["results"]

        ## convert them to PseudoColorMixing objects and RGBValue objects

        self.processes = []
        self.rgb_values = []
        for fullpagename, process_dict in res_dict.items():
            printout_dict = process_dict["printouts"]

            try:
                process = PseudoColorMixing(
                    label = [{"language":"en", "text": "a temporary pseudo color mixing process"}],
                    red_fraction=printout_dict["red_fraction"][0],
                    green_fraction=printout_dict["green_fraction"][0],
                    blue_fraction=printout_dict["blue_fraction"][0],
                    name=fullpagename)


                rgb_value = RGBValue(red_value=printout_dict["red_value"][0],
                                        green_value=printout_dict["green_value"][0],
                                        blue_value=printout_dict["blue_value"][0],
                                        name=f"{fullpagename}/HasOutput.HasColor")
                self.processes.append(process)
                self.rgb_values.append(rgb_value)

            except Exception as e:
                print(f"Error processing {fullpagename}: {e}")

    def update_visualization(self):
        """Updates the visualization panel with the current processes and RGB values."""

        self.get_inputs_outputs()

        self.fig = px.scatter_3d(x=[process.red_fraction for process in self.processes],
                                 y=[process.green_fraction for process in self.processes],
                                 z=[process.blue_fraction for process in self.processes],
                                 color = [f"rgb({int(rgb_value.red_value)}, {int(rgb_value.green_value)},"
                                          f" {int(rgb_value.blue_value)}) {i}" for
                                          i,rgb_value in enumerate(self.rgb_values)], # i added index to color to avoid duplicates
                                 color_discrete_sequence = [f"rgb({int(rgb_value.red_value)}, {int(rgb_value.green_value)},"
                                          f" {int(rgb_value.blue_value)})" for
                                          rgb_value in self.rgb_values],
                                 labels = [str(i) for i in range(len(self.processes))],
                            )

        #TODO: add planned experiments as black thick dots!
        #TODO: make dots clickable

        self.fig.update_layout(showlegend=False,
                          scene=dict(xaxis_title="red fraction",
                                     yaxis_title="green fraction",
                                     zaxis_title="blue fraction"))

        old_panel = self.visualization_panel

        self.visualization_panel = pn.pane.Plotly(self.fig,
                                     #**widget_args,
                                    )
        self.visualization_col.remove(old_panel)
        self.visualization_col.append(self.visualization_panel)  # Add the new visualization panel


    def update_visualization_callback(self,event):
        self.update_visualization()







if __name__ == "__main__":

    ## test query that gets all inputs and outputs
    test_query = False
    if test_query:
        osw_obj = OswExpress(# domain="demo.open-semantic-lab.org"
            # domain = "mat-o-lab.open-semantic-lab.org",
            domain="wiki-dev.open-semantic-lab.org"
        )
        ## query for all PseudoColorMixing processes
        query = """[[Category:OSW25e748d2fa7a4b19a6a74e0b7f2d0211]]
        |?ShallBeExecuted=execute
        |?HasRedMixtureFraction=red_fraction
        |?HasGreenMixtureFraction=green_fraction
        |?HasBlueMixtureFraction=blue_fraction
        |?HasOutput.HasColor.HasRedValue=red_value
        |?HasOutput.HasColor.HasGreenValue=green_value
        |?HasOutput.HasColor.HasBlueValue=blue_value"""
        res = osw_obj.mw_site.api("ask",query=query, format = "json", limit = 1000)
        print(res)

        res_dict = res["query"]["results"]

    osw_obj = OswExpress(  # domain="demo.open-semantic-lab.org"
        # domain = "mat-o-lab.open-semantic-lab.org",
        domain="wiki-dev.open-semantic-lab.org"
    )

    color_database_visualization_panel = ColorDatabaseVisualizationPanel(osw_obj=osw_obj)

    pn.serve(color_database_visualization_panel, port = 20201, threaded=True)

