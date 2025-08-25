from pseudo_color_mixer_panel import PseudoColorMixerPanel
from pseudo_color_mixer import PseudoColorMixer
from color_database_visualization_panel import ColorDatabaseVisualizationPanel
from suggestion_panel import SuggestionPanel
from osw.express import OswExpress
import panel as pn


if __name__ == "__main__":
    color_mixer = PseudoColorMixer()
    osw_obj = OswExpress(
        domain="wiki-dev.open-semantic-lab.org"
    )
    mixer_panel = PseudoColorMixerPanel(color_mixer, osw_obj=osw_obj)
    pn.serve(mixer_panel, port=20200, threaded=True)

    visualizer_panel = ColorDatabaseVisualizationPanel(osw_obj=osw_obj)
    pn.serve(visualizer_panel, port=20201, threaded=True)

    suggestion_panel = SuggestionPanel(osw_obj=osw_obj)
    pn.serve(suggestion_panel, port=20202, threaded=True)

