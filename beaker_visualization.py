
def create_beaker_svg(filling_percent:float, liquid_color, filename="beaker.svg"):
    """
    Erstellt ein SVG-Bild eines Becherglases mit Flüssigkeit.

    Args:
        filling_percent (float): Füllhöhe in Prozent (0-100)
        liquid_color (str): Farbe der Flüssigkeit (z.B. 'blue', '#FF0000', 'rgb(255,0,0)')
        filename (str): Name der zu speichernden SVG-Datei

    Returns:
        str: SVG-Code als String
    """

    # Begrenze Füllhöhe auf 0-100%
    filling_percent = max(0, min(100, filling_percent))

    # SVG-Dimensionen und Becherglas-Parameter
    width, height = 200, 300
    beaker_bottom_width = 80
    beaker_top_width = 100
    beaker_height = 200
    beaker_x = (width - beaker_bottom_width) // 2
    beaker_y = 50

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

    print(f"SVG-Datei '{filename}' wurde erstellt.")
    return svg_code


# Example usage
if __name__ == "__main__":

    # Verschiedene Beispiele erstellen
    create_beaker_svg(75, "blue", "beaker_75_blue.svg")
    #create_beaker_svg(30, "#FF6B35", "beaker_30_orange.svg")
    #create_beaker_svg(90, "rgb(50, 205, 50)", "beaker_90_green.svg")
    #create_beaker_svg(0, "red", "beaker_empty.svg")