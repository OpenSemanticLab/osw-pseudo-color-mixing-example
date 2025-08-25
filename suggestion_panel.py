### a panel that helps to find parameters for the next experiment
from ax.service.ax_client import AxClient, ObjectiveProperties
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
from ax.modelbridge.factory import Models
from ax.plot.contour import interact_contour_plotly

import panel as pn
from osw.model.entity import RGBValue, PseudoColorMixing, PseudoColoredLiquid
from osw.express import OswExpress
from datetime import datetime

def color_rating(measured_rgb:RGBValue, target_rgb) -> float:
    """rates a color based on measured color_mixer_output and ColorOptimizerInput. Lower is better"""
    target_r = target_rgb.red_value     # Fraunhofer-Green: 0,151,117; Bigmap-Green: 4,92,97
    target_g = target_rgb.green_value
    target_b = target_rgb.blue_value

    r = measured_rgb.red_value
    g = measured_rgb.green_value
    b = measured_rgb.blue_value

    max_error = 3*255
    r_error = abs(r-target_r)
    g_error = abs(g-target_g)
    b_error = abs(b-target_b)

    rating = sum([r_error, g_error, b_error])/max_error
    return rating

def hex_to_RGBValue(hex_color: str) -> RGBValue:
    """Converts a hex color string to an RGBValue object."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return RGBValue(red_value=r, green_value=g, blue_value=b)

class SuggestionPanel:
    def __init__(self, osw_obj = None):
        self.osw_obj = osw_obj
        self.build_panel()
        self.finished_processes = []
        self.finished_rgb_values = []
        self.suggested_process:PseudoColorMixing = None

    def build_panel(self):

        self.target_color_picker = pn.widgets.ColorPicker(name="Target Color", value="#009777",width=200)
      #  self.batch_size_input = pn.widgets.IntInput(name="batch size", value = 1, start = 1)
      #  self.budget_input = pn.widgets.IntInput(name="budget", value = 10, start = 0)
        self.ploty_panel = pn.pane.Plotly(width=800)
        self.best_tried_parameters_alert = pn.pane.Alert( "No parameters loaded yet.",
                                                          name= "Best tried parameters",
                                                          alert_type="info")
        # self.best_predicted_parameters_alert = pn.pane.Alert( "No parameters loaded yet.",
        #                                                       name="Best predicted parameters",
        #                                                       alert_type="info")
        self.best_tried_parameters = None
        self.visualization_col = pn.Column(self.target_color_picker,self.ploty_panel,
                                           self.best_tried_parameters_alert,
                                          # self.best_predicted_parameters_alert
                                           )

        self.suggestion_text = pn.pane.Alert("No suggestions yet.", alert_type="info")
        self.suggestion_button = pn.widgets.Button(name="Get Suggestion", button_type="primary")
        self.suggestion_button.on_click(self.get_suggestions_callback)

        self.execute_suggestion_button = pn.widgets.Button(name="Hand in Suggestion", button_type="primary")
        self.execute_suggestion_button.on_click(self.execute_suggestions_callback)

        self.suggestion_preview = pn.pane.Alert()
        self.target_color_col = pn.Column(self.target_color_picker,
                                          #self.batch_size_input,
                                          #self.budget_input
                                          )

        self.control_column = pn.Column(self.suggestion_text, self.suggestion_button,
                                        self.suggestion_preview,
                                        self.execute_suggestion_button)

        self.main_row = pn.Row(#self.target_color_col,
                               self.visualization_col, self.control_column)

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

        self.finished_processes = []
        self.finished_rgb_values = []
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
                self.finished_processes.append(process)
                self.finished_rgb_values.append(rgb_value)

            except Exception as e:
                print(f"Error processing {fullpagename}: {e}")
    def get_suggestions_callback(self, event):
        # get current database
        self.suggestion_text.object = "Re-Building Database..."
        self.suggestion_text.alert_type= "warning"
        #build model
        gs = GenerationStrategy(
            steps=[
               # GenerationStep(
               #     model=Models.SOBOL,
               #     num_trials=4,  # how many sobol trials to perform (rule of thumb: 2 * number of params)
               #     min_trials_observed=3,
               #     max_parallelism=5,
               #     model_kwargs={"seed": 999},
               # ),
                GenerationStep(
                    #model=Models.SAASBO, #a bit slow
                    model=Models.BOTORCH_MODULAR,
                    num_trials=-1,
                    max_parallelism=3,
                    model_kwargs={},
                ),
            ]
        )

        self.ax_client = AxClient(
            generation_strategy=gs
            )

        self.ax_client.create_experiment(
            name="color_mixing_simulation",
            parameters=[
                {"name": "red_fraction", "type": "range", "bounds": [0.0, 1.0]},
                {"name": "green_fraction", "type": "range", "bounds": [0.0, 1.0]},
                {"name": "blue_fraction", "type": "range", "bounds": [0.0, 1.0]},
            ],
            objectives={
                "rating": ObjectiveProperties(minimize=True),
            },
            parameter_constraints=["red_fraction + green_fraction + blue_fraction <= 1.0"]
        )

        self.get_inputs_outputs()




        for i, (process, rgb) in enumerate(zip(self.finished_processes, self.finished_rgb_values)):
            self.ax_client.attach_trial(parameters={"red_fraction": process.red_fraction,
                                               "green_fraction": process.green_fraction,
                                               "blue_fraction": process.blue_fraction},
                                        run_metadata={"uuid": process.uuid}
                                        )
            # calculate (new) rating with (old) raw data
            rating = color_rating(rgb, target_rgb = hex_to_RGBValue(self.target_color_picker.value))
            self.ax_client.complete_trial(trial_index=i, raw_data={"rating": rating})


        self.suggestion_text.object = "Database successfully rebuilt. Getting suggestions with Bayesian Optimization..."
        self.suggestion_text.alert_type = "warning"

        # get suggestions using bayesian optimization from ax-platform
        #self.suggestion_dict, completed = self.ax_client.get_next_trials(max_trials = self.batch_size_input.value)
        self.parametrization, completed = self.ax_client.get_next_trial()

        # visualize the model belief:
        self.contour_plot = self.ax_client.get_contour_plot(param_x="red_fraction", param_y="green_fraction",
                                                  metric_name="rating")

        self.plotly_fig = interact_contour_plotly(
            model = self.ax_client.generation_strategy.model,
            metric_name = "rating",
        )

        self.ploty_panel.object = self.plotly_fig
        print("type of fig_r_g:", type(self.plotly_fig))
        # format suggested processes

        self.suggested_process = PseudoColorMixing(
                label = [{"language":"en", "text": f"Pseudo Color Mixing Suggested by Bayesian Optimizer "
                                                   f"{datetime.now()}"}],
                red_fraction=self.parametrization["red_fraction"],
                green_fraction=self.parametrization["green_fraction"],
                blue_fraction=self.parametrization["blue_fraction"],
                execution_trigger=True
            )



        self.suggestion_text.object = "Suggestions successfully generated."
        self.suggestion_text.alert_type = "success"
        self.suggestion_preview.object = str(f"suggestd process: "
                                             f"<br>red_fraction = "
                                             f" {self.suggested_process.red_fraction} <br>"
                                             f"green_fraction = "
                                                f" {self.suggested_process.green_fraction} <br>"
                                                f"blue_fraction = "
                                                f" {self.suggested_process.blue_fraction} <br>"
                                             )

        self.best_tried_parameters = self.ax_client.get_best_parameters(
            use_model_predictions=False
        )
        self.best_tried_parameters_alert.object = (f"Best tried parameters so far: {self.best_tried_parameters[0]} ")
        self.best_tried_parameters_alert.alert_type = "success"

    #   self.best_predicted_parameters_alert.object = (f"Best predicted parameters so far:
    #   {self.best_predicted_parameters[0]}")
    #    self.best_predicted_parameters_alert.alert_type="success"


    def execute_suggestions(self):
        if self.suggested_process is None:
            self.suggestion_text.object = "No suggestions to execute."
            self.suggestion_text.alert_type = "danger"
            return

        self.suggestion_text.object = "Uploading suggestions ..."
        self.suggestion_text.alert_type = "warning"

        self.osw_obj.store_entity(self.suggested_process)

        self.suggestion_text.object = "Suggestions successfully uploaded"
        self.suggestion_text.alert_type = "success"



    def execute_suggestions_callback(self, event):
        self.execute_suggestions()




if __name__ == "__main__":
    osw_obj = OswExpress(
        # domain="demo.open-semantic-lab.org"
        # domain = "mat-o-lab.open-semantic-lab.org",
        domain="wiki-dev.open-semantic-lab.org"
    )
    suggestion_panel = SuggestionPanel(osw_obj = osw_obj)
    pn.serve(suggestion_panel, port=20202, threaded=True)
    print("Suggestion Panel is running on port 20202")