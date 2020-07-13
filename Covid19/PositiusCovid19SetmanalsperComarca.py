# ----- Importació de llibreries ------

import numpy as np
import pandas as pd
import geopandas as gpd
import time
import xml.etree.ElementTree as et
import os
import requests

from bokeh.io import show
from bokeh.models import (ColorBar, GeoJSONDataSource, HoverTool, LinearColorMapper)
from bokeh.palettes import brewer
from bokeh.plotting import figure


# ----- Importació de dades ------

# Directori de treball
dir_path = os.path.dirname(os.path.realpath(__file__))

# Casos de covid per municipi
covid = pd.read_csv(dir_path + '/Registre_de_casos_de_COVID-19_realitzats_a_Catalunya._Segregaci__per_sexe_i_municipi.csv',
                   dtype = {'MunicipiCodi':str, 'NumCasos':np.int32, 'ComarcaCodi': str})
# Comarques de Catalunya
comarques = gpd.read_file(dir_path + '/../Dades/CatalunyaComarques/bm5mv21sh0tpc1_20200601_0.shp')

# Població de Catalunya per comarca
responses = requests.get('https://api.idescat.cat/emex/v1/dades.xml?i=f171&tipus=com')
root = et.fromstring(responses.content)
poblacio = root[1][0][1].text.split(", ")
poblacio = [ int(x) for x in poblacio ]
codi = []
comarca = []
for node in root.iter('col'):
    codi.append(node.attrib['id'])
    comarca.append(node.text)
poblacioComarques = pd.DataFrame({'codi': codi, 'comarca': comarca, 'poblacio':poblacio})


# ----- Preparació de dades ------

# Selecció positius
covid = covid.loc[covid['TipusCasDescripcio']!='Sospitós',:]

# Selecció de dades geolocalitzades
covid = covid.loc[covid['MunicipiCodi'].notna(), ['TipusCasData','ComarcaCodi', 'ComarcaDescripcio','NumCasos']]

# Càlcul del número de setmana
def week_number(date):
    d = time.strptime(date, "%d/%m/%Y")
    week = time.strftime("%U",d)
    return int(week)

covid['Setmana'] = covid['TipusCasData'].apply(week_number)

# Selecció de la setmana
last_week = max(covid['Setmana']) - 1
covid = covid.loc[covid['Setmana']==last_week,]

# Agrupació de dades per comarca
covid = covid.groupby(['ComarcaCodi','ComarcaDescripcio','Setmana'], as_index = False).sum()


# ----- Integració de dades -----

# Comarques amb població
comarques = comarques.merge(poblacioComarques[['codi','poblacio']], left_on='CODICOMAR', right_on='codi', how='left')

# Municipis amb covid
dades_mapa = comarques.merge(covid, left_on='CODICOMAR', right_on='ComarcaCodi', how='left')

# Omplir valors nuls
dades_mapa.loc[dades_mapa['NumCasos'].isna(), 'NumCasos'] = 0

# Càlcul del percentatge de casos
dades_mapa['PercentatgeCasos'] = round(dades_mapa['NumCasos'] * 100000 / dades_mapa['poblacio'],0)

# ----- Visualització de dades ------

# Creació de la font de dades
geosource = GeoJSONDataSource(geojson = dades_mapa.to_json())

# Paleta de colors
palette = brewer['OrRd'][6]
palette = palette[::-1]
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 300)

# Valors de la llegenda
tick_labels = {'0': '0', '50': '50',  '100': '100', '150': '150', '200':'200', '250':'250', '300':'300+'}

# Llegenda
color_bar = ColorBar(color_mapper = color_mapper,
                     title = "Positius de COVID19 per cada 100.000 habitants",
                     label_standoff = 8,
                     width = 500, height = 20,
                     border_line_color = None,
                     location = (0,0),
                     orientation = 'horizontal',
                     major_label_overrides = tick_labels)

# Figura
p = figure(title = 'Afectació del COVID a Catalunya: Positius confirmats (setmana ' + str(last_week) + ")",
           toolbar_location = 'below',
           tools = 'pan, box_zoom, reset')

# Graella
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Representació gràfica
p_comarques = p.patches('xs','ys', source = geosource,
                        fill_color = {'field' :'PercentatgeCasos', 'transform' : color_mapper},
                        line_color = 'gray',
                        line_width = 0.25, fill_alpha = 1)

p.add_tools(HoverTool(renderers = [p_comarques],
                      tooltips = [('Comarca','@NOMCOMAR'),
                                  ('Positius per 100.000 hab','@PercentatgeCasos'),
                                  ('Nombre de positius','@NumCasos'),]))
p.add_layout(color_bar, 'below')

show(p)

