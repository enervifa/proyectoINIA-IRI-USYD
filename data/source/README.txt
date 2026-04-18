Excel -> JSON (GMIC Uruguay)

1) Mantene los datos en Excel con 4 hojas:
   - models
   - resources
   - keywords
   - institutions
   - projects (opcional)

2) Exporta cada hoja a CSV (UTF-8) en esta carpeta:
   - data/source/models.csv
   - data/source/resources.csv
   - data/source/keywords.csv
   - data/source/institutions.csv

   Para proyectos activos:
   - data/projects.csv (se lee directo por el sitio)

3) Genera los JSON del sitio:
   python tools/build_data_from_csv.py

Los archivos generados son:
   - data/models.json
   - data/resources.json
   - data/keywords.json
   - data/institutions.json

Notas:
   - En listas (keywords), usa separador ";" o ",".
   - En data/projects.csv, "model_id" y "cuenca" pueden tener multiples valores (separados por ";" o "|")
     para vincular un mismo proyecto a mas de una cuenca/modelo. Esos nombres se muestran como tags
     debajo del titulo del proyecto en la seccion "Proyectos activos".
   - Si "id" o "table_order" estan vacios en models.csv, se autocompletan.
