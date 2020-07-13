
import requests
import xml.etree.ElementTree as et
import pandas as pd
import os

# Consulta a la API
responses = requests.get('https://api.idescat.cat/emex/v1/dades.xml?i=f171&tipus=com')

# Parser
root = et.fromstring(responses.content)

# Poblacions
poblacio = root[1][0][1].text.split(", ")
poblacio = [ int(x) for x in poblacio ]

# Codi i nom de comarca
codi = []
comarca = []
for node in root.iter('col'):
    codi.append(node.attrib['id'])
    comarca.append(node.text)

# Creació del dataframe
poblacioComarques = pd.DataFrame({'codi': codi, 'comarca': comarca, 'poblacio':poblacio})

# Exportació de dades
dir_path = os.path.dirname(os.path.realpath(__file__))
poblacioComarques.to_csv(dir_path + '/PoblacioComarques.csv', index=False)
