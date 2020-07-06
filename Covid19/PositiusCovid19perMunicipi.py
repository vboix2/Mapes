# ----- Importació de llibreries ------

import numpy as np
import pandas as pd
import geopandas as gpd

from bokeh.io import show
from bokeh.models import (ColorBar, GeoJSONDataSource, HoverTool, LinearColorMapper)
from bokeh.palettes import brewer
from bokeh.plotting import figure


# ----- Importació de dades ------

# Casos de covid per municipi
covid = pd.read_csv('Registre_de_casos_de_COVID-19_realitzats_a_Catalunya._Segregaci__per_sexe_i_municipi.csv',
                   dtype = {'MunicipiCodi':str, 'NumCasos':np.int32})
# Municipis de Catalunya
municipis = gpd.read_file('../Dades/CatalunyaMunicipis/bm5mv21sh0tpm1_20200601_0.shp')

# Població de Catalunya per municipi
poblacio = pd.read_csv('../Dades/Població/Poblaci__de_Catalunya_per_municipi__rang_d_edat_i_sexe.csv',
                      dtype = {'Codi':str})


# ----- Preparació de dades ------

# Selecció segons tipus de cas
covid = covid.loc[covid['TipusCasDescripcio']!='Sospitós',:]

# Selecció de dades geolocalitzades
covid = covid.loc[covid['MunicipiCodi'].notna(), ['MunicipiCodi','NumCasos']]

# Agrupació de dades per municipi
covid = covid.groupby('MunicipiCodi', as_index = False).sum()

# Població per municipi
poblacio = poblacio[:947]
poblacio['Total'] = poblacio.iloc[:,8:11].apply(sum,1)

# Correcció codi municipi
def correct_code(codi):
    while len(codi)<6:
        codi = '0' + codi
    return codi

poblacio['Codi'] = poblacio['Codi'].apply(correct_code).str[:5]

municipis['CODIMUNI'] = municipis['CODIMUNI'].str[:5]


# ----- Integració de dades -----

# Municipis amb població
municipis = municipis.merge(poblacio[['Codi','Total']], left_on='CODIMUNI', right_on='Codi', how='left')

# Municipis amb covid
dades_mapa = municipis.merge(covid, left_on='CODIMUNI', right_on='MunicipiCodi', how='left')

# Omplir valors nuls
dades_mapa.loc[dades_mapa['NumCasos'].isna(), 'NumCasos'] = 0

# Càlcul del percentatge de casos
dades_mapa['PercentatgeCasos'] = round(dades_mapa['NumCasos'] * 100 / dades_mapa['Total'],1)


# ----- Visualització de dades ------

# Creació de la font de dades
geosource = GeoJSONDataSource(geojson = dades_mapa.to_json())

# Paleta de colors
palette = brewer['OrRd'][7]
palette = palette[::-1]
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 7)

# Valors de la llegenda
tick_labels = {'0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
               '5': '5', '6': '6', '7': '7'}

# Llegenda
color_bar = ColorBar(color_mapper = color_mapper,
                     title = "Percentatge de població amb positiu confirmat de COVID19 (%)",
                     label_standoff = 8,
                     width = 500, height = 20,
                     border_line_color = None,
                     location = (0,0),
                     orientation = 'horizontal',
                     major_label_overrides = tick_labels)

# Figura
p = figure(title = 'Afectació del COVID a Catalunya: Positius confirmats',
           toolbar_location = 'below',
           tools = 'pan, box_zoom, reset')

# Graella
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Representació gràfica
p_municipis = p.patches('xs','ys', source = geosource,
                        fill_color = {'field' :'PercentatgeCasos', 'transform' : color_mapper},
                        line_color = 'gray',
                        line_width = 0.25, fill_alpha = 1)

p.add_tools(HoverTool(renderers = [p_municipis],
                      tooltips = [('Municipi','@NOMMUNI'),
                                  ('Població afectada (%)','@PercentatgeCasos{1.1}'),
                                  ('Positius acumulats','@NumCasos'),]))
p.add_layout(color_bar, 'below')

show(p)