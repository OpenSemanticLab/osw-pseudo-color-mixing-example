import uuid

from pydantic.v1 import BaseModel, Field
from beaker_visualization import create_beaker_svg
from typing import Optional
from osw.core import OSW
from osw.express import OswExpress
from osw.model.entity import PseudoColoredLiquid, PseudoColorMixing, Label, RGBValue
from osw.controller.file.local import LocalFileController
from osw.controller.file.wiki import WikiFileController
from osw.utils.wiki import get_full_title
from datetime import datetime
from io import BytesIO
import time
from threading import Thread


class ColorMixerInput(BaseModel):
    """
    Input of Color Mixer:
    ratios of Food Color (each 100 Droplets per 1l distilled Water)
    Remainder of r/g/b fractions is filled up with water.
    volume_ml is the total volume used in an experiment (not material specific but effects result)
    """

    #volume_ml: float = Field(default = 30, le=100, description="total volume in ml")    ### default changed by matthias due to larger beaker
    red_fraction: float = Field(le=1, description="fraction of red liquid")
    green_fraction: float = Field(le=1, description="fraction of green liquid")
    blue_fraction: float = Field(le=1, description="fraction of blue liquid")


def rgb_to_hex(rgb_value: RGBValue):
    """
    Convert an RGBValue to hexadecimal color format with validation.

    Args:
        rgb_tuple: RGBValue

    Returns:
        String: Hexadecimal color code (e.g., '#FF5733')

    Raises:
        ValueError: If RGB values are not in valid range (0-255)
    """
    r = int(round(rgb_value.red_value))
    g = int(round(rgb_value.green_value))
    b = int(round(rgb_value.blue_value))

    # Validate RGB values
    for value in [r, g, b]:
        if not (0 <= value <= 255):
            raise ValueError(f"RGB values must be between 0-255, got {value}")

    return f"#{r:02x}{g:02x}{b:02x}".upper()

class ColorMixerOutput(BaseModel):
    extracted_color: RGBValue
    raw_image: Optional[str] = Field(description="link to raw image of the color mixing experiment")


class ColorOptimizerInput(BaseModel):
    """
    Input of Color Optimizer:
    target r/g/b values for which a mixing ratio shall be found
    """
    target_color: RGBValue
    iterations: int = Field(ge=0, default=20, description="number of iterations to be performed")

class PseudoColorMixer():
    def __init__(self, tool_id = "Item:OSW10960c5f551f4697b0b472315a78699a"):
        self.last_svg_code = None
        self.last_rgb_value: RGBValue = None
        self.last_input: ColorMixerInput = None
        self.thread:Thread = None
        self.stop_flag = False
        self.tool_id=tool_id

    def subtractive_color_mixing(self, inp: ColorMixerInput):

        r = (1 - inp.green_fraction - inp.blue_fraction) * 255
        g = (1 - inp.red_fraction - inp.blue_fraction) * 255
        b = (1 - inp.red_fraction - inp.green_fraction) * 255

        self.last_input = inp
        self.last_rgb_value = RGBValue(red_value=r, green_value=g, blue_value=b)
        return self.last_rgb_value

    def create_beaker_svg(self, filling_percent: float, rgb_value: RGBValue, filename="beaker.svg"):
        """
        Erstellt ein SVG-Bild eines Becherglases mit Flüssigkeit.

        Args:
            filling_percent (float): Füllhöhe in Prozent (0-100)
            liquid_color (str): Farbe der Flüssigkeit (z.B. 'blue', '#FF0000', 'rgb(255,0,0)')
            filename (str): Name der zu speichernden SVG-Datei

        Returns:
            str: SVG-Code als String
        """

        liquid_color = rgb_to_hex(rgb_value)

        # Begrenze Füllhöhe auf 0-100%
        filling_percent = max(0, min(100, filling_percent))

        # SVG-Dimensionen und Becherglas-Parameter


        width, height = 100, 150
        beaker_bottom_width = 40
        beaker_top_width = 50
        beaker_height = 100
        beaker_x = (width - beaker_bottom_width) // 2
        beaker_y = 25

        # Berechne Flüssigkeitshöhe
        liquid_height = (filling_percent / 100) * beaker_height
        liquid_y = beaker_y + beaker_height - liquid_height

        # Berechne Breite der Flüssigkeit basierend auf der trapezförmigen Form
        width_diff = beaker_top_width - beaker_bottom_width
        liquid_bottom_width = beaker_bottom_width
        liquid_top_width = beaker_bottom_width + (width_diff * (liquid_height / beaker_height))

        # SVG-Code generieren
        svg_code = f'''<?xml version="1.0" encoding="UTF-8"?>
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <!-- Hintergrund -->
        <rect width="{width}" height="{height}" fill="white"/>

        <!-- Becherglas (Trapezform) -->
        <polygon points="{beaker_x},{beaker_y + beaker_height} 
                         {beaker_x + beaker_bottom_width},{beaker_y + beaker_height}
                         {beaker_x + (beaker_top_width - beaker_bottom_width) // 2 + beaker_bottom_width},{beaker_y}
                         {beaker_x - (beaker_top_width - beaker_bottom_width) // 2},{beaker_y}"
                 fill="none" 
                 stroke="black" 
                 stroke-width="3"/>

        <!-- Flüssigkeit (falls vorhanden) -->'''

        if filling_percent > 0:
            liquid_x_left = beaker_x - (beaker_top_width - beaker_bottom_width) // 2 * (liquid_height / beaker_height)
            liquid_x_right = beaker_x + beaker_bottom_width + (beaker_top_width - beaker_bottom_width) // 2 * (
                    liquid_height / beaker_height)

            svg_code += f'''
        <polygon points="{beaker_x},{beaker_y + beaker_height}
                         {beaker_x + beaker_bottom_width},{beaker_y + beaker_height}
                         {liquid_x_right},{liquid_y}
                         {liquid_x_left},{liquid_y}"
                 fill="{liquid_color}"
                 opacity="0.8"/>'''

        svg_code += f'''

        <!-- Becherrand (oben) -->
        <line x1="{beaker_x - (beaker_top_width - beaker_bottom_width) // 2 - 5}" 
              y1="{beaker_y}" 
              x2="{beaker_x + (beaker_top_width - beaker_bottom_width) // 2 + beaker_bottom_width + 5}" 
              y2="{beaker_y}" 
              stroke="black" 
              stroke-width="4"/>

        <!-- Ausgießer -->
        <path d="M {beaker_x + (beaker_top_width - beaker_bottom_width) // 2 + beaker_bottom_width + 5} {beaker_y}
                 Q {beaker_x + (beaker_top_width - beaker_bottom_width) // 2 + beaker_bottom_width + 15} {beaker_y - 5}
                 {beaker_x + (beaker_top_width - beaker_bottom_width) // 2 + beaker_bottom_width + 20} {beaker_y + 5}"
              fill="none"
              stroke="black"
              stroke-width="2"/>

        <!-- Füllstand-Text 
        <text x="{width - 30}" y="{beaker_y + beaker_height - 10}" 
              font-family="Arial" font-size="12" fill="black">
              {filling_percent:.1f}%
        </text>
        -->
    </svg>'''

        # SVG in Datei speichern
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(svg_code)
        self.last_svg_code = svg_code
        print(f"SVG-Datei '{filename}' wurde erstellt.")
        return svg_code

    def document_color_mixing(self,rgb_value: RGBValue, beaker_svg: str):
        """
        Document the color mixing process in open semantic lab
        """
        ## create an image of the beaker with the color
        beaker_svg = create_beaker_svg(
            filling_percent=80,

            liquid_color=rgb_to_hex(rgb_value),
            filename="color_mixing_beaker.svg"
        )

    def document_last_color_mixing(self, osw_obj:OSW, process_instance:PseudoColorMixing = None):
        """
        Document the last color mixing process in open semantic lab
        """
        if self.last_svg_code is None:
            print("No color mixing has been performed yet.")
            return

        self.document_color_mixing(rgb_value=self.last_rgb_value, beaker_svg=self.last_svg_code)

        # upload image
        beaker_image_uuid = uuid.uuid4()
        beaker_image_wf = WikiFileController(
            label = [Label(text=f"Beaker Image {datetime.now().strftime('%y-%m-%d %H:%M.%S')}", lang="en")],
            title = f"OSW{str(beaker_image_uuid).replace("-","")}.svg",
            uuid=beaker_image_uuid,

            osw=osw_obj)

        beaker_image_io = BytesIO()
        beaker_image_io.write(self.last_svg_code.encode('utf-8'))
        beaker_image_io.name = "beaker_image.svg"

        try:
            beaker_image_wf.put(beaker_image_io, overwrite=True)
        except Exception as e:
            print("Error uploading bar chart file: ", e)

        output_instance = PseudoColoredLiquid(
            uuid = str(uuid.uuid4()),
            label = [Label(text=f"Pseudo Colored Liquid {datetime.now().strftime('%y-%m-%d %H:%M.%S')}", lang="en")],
            color=self.last_rgb_value,
            image = get_full_title(beaker_image_wf),
        )


        if process_instance is None:
            process_uuid = str(uuid.uuid4())
            process_instance = PseudoColorMixing(
                label=[Label(text=f"Pseudo Color Mixing {datetime.now().strftime('%y-%m-%d %H:%M.%S')}", lang="en")],
                uuid=str(process_uuid),
                red_fraction=self.last_input.red_fraction,
                green_fraction=self.last_input.green_fraction,
                blue_fraction=self.last_input.blue_fraction,
                output=[get_full_title(output_instance)],
                image=get_full_title(beaker_image_wf),
                tool=[self.tool_id]
            )
        else:
            process_instance.output = [get_full_title(output_instance)]
            process_instance.execution_trigger=False
            process_instance.image= get_full_title(beaker_image_wf)
            process_instance.tool= [self.tool_id]

        osw_obj.store_entity(OSW.StoreEntityParam(entities=[process_instance, output_instance],
                                                  overwrite=True))

        process_link = f"https://{osw_obj.domain}/wiki/{get_full_title(process_instance)}"
        output_link = f"https://{osw_obj.domain}/wiki/{get_full_title(output_instance)}"

        return(process_link, output_link)

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
                print("mixing_process:", mixing_process)
            else:
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


if __name__ == '__main__':
    # Example usage
    color_mixer = PseudoColorMixer()
    mixer_input = ColorMixerInput(red_fraction=0.7, green_fraction=0.1, blue_fraction=0.2)
    result_rgb = color_mixer.subtractive_color_mixing(mixer_input)
    print(result_rgb)
    beaker_svg = color_mixer.create_beaker_svg(80, result_rgb)

    test_documentation = False
    if test_documentation:

        osw_obj = OswExpress(
           # domain="demo.open-semantic-lab.org"
            #domain = "mat-o-lab.open-semantic-lab.org",
            domain="wiki-dev.open-semantic-lab.org"
        )
        color_mixer.document_last_color_mixing(osw_obj)

        osw_obj.load_entity()

    test_check_for_open_tasks = False
    if test_check_for_open_tasks:
        osw_obj = OswExpress(
            # domain="demo.open-semantic-lab.org"
            # domain = "mat-o-lab.open-semantic-lab.org",
            domain="wiki-dev.open-semantic-lab.org"
        )
        open_tasks = color_mixer.check_for_open_tasks(osw_obj)
        print(f"Open tasks found: {len(open_tasks)}")
        print(open_tasks)

    test_continuous_loop = True
    if test_continuous_loop:
        osw_obj = OswExpress(
            # domain="demo.open-semantic-lab.org"
            # domain = "mat-o-lab.open-semantic-lab.org",
            domain="wiki-dev.open-semantic-lab.org"
        )
        color_mixer.start_continuous_loop(osw_obj)
        time.sleep(10)
        color_mixer.stop_continuous_loop()
