import os,glob,csv,re,json,unicodedata
from aqt.qt import *
from datetime import datetime

class Corpus():
    re_csv_name = re.compile('._(?P<series_name>[^_]+)_S(?P<season>\d+)E(?P<episode>\d+)\.csv')
    re_limpia_claves = re.compile('[.,;:¿?¡!"-]*(?P<key>[^.,;:¿?¡!"-]+-?[^.,;:¿?¡!"-]*)[.,;:¿?¡!"-]*', re.UNICODE)

    def __init__(self, idioma):
        with open(os.path.join(os.path.dirname(__file__), "dic_palabras_" + idioma.lower() + ".json")) as f_palabras:
            self.dic_palabras = json.load(f_palabras)
        with open(os.path.join(os.path.dirname(__file__), "dic_ficheros_" + idioma.lower() + ".json")) as f_ficheros:
            self.dic_ficheros = json.load(f_ficheros)

    def buscar_palabra(self, palabra, desde, num_ejemplos, force_lower):
        palabra = unicodedata.normalize('NFD', palabra)
        if force_lower:
            palabra = palabra.lower()
        if palabra not in self.dic_palabras:
            # Intentamos encontrar una clave con expresión regular
            try:
                re_palabra = re.compile(palabra)
                encontrada = False
                for key in self.dic_palabras:
                    if re_palabra.fullmatch(key):
                        palabra = key
                        encontrada = True
                        break
                if not encontrada:
                    return None
            except:
                return None
        lista_ejemplos = list()
        for index in range(desde, desde + num_ejemplos):
            try:
                tupla = self.dic_palabras[palabra][index] #del dic_palabras la tupla formada por (ruta_excel, linea_excel_donde_se_encuentra_palabra)
                contenido_tarjeta = self.dic_ficheros[tupla[0]][tupla[1]]
                lista_ejemplos.append((contenido_tarjeta[0], contenido_tarjeta[1], contenido_tarjeta[2], tupla[0], tupla[1]))
            except:
                break
        return lista_ejemplos

    @staticmethod
    def indexar_corpus(ventana):
        reply = QMessageBox.question(ventana, "Confirmar", "Esta operación eliminará el corpus actual. ¿Quieres seguir?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return
        # Borrar los ficheros .json actuales
        for f in glob.glob(os.path.join(os.path.dirname(__file__), '*.json')):
            os.remove(f)
        # Pedir la ruta del repositorio multimedia
        ruta = QFileDialog.getExistingDirectory(ventana, 'Seleccionar directorio',
                                                os.path.dirname(__file__),
                                                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if ruta:
            t1 = datetime.now()
            # Escanear directorios
            dirs = os.listdir(ruta)
            for idioma in dirs:
                ruta_completa = os.path.join(ruta, idioma)
                force_lower = True
                if idioma.upper() == 'ALEMAN':
                    force_lower = False
                if os.path.isdir(ruta_completa):
                    dic_palabras = dict()
                    dic_ficheros = dict()
                    Corpus.indexar_ruta(ruta_completa, dic_palabras, dic_ficheros, force_lower)
                    f_palabras = open(os.path.join(os.path.dirname(__file__), "dic_palabras_" + idioma.lower() + ".json"), mode="w", encoding='utf-8')
                    json.dump(dic_palabras, f_palabras)
                    f_palabras.close()
                    f_ficheros = open(os.path.join(os.path.dirname(__file__), "dic_ficheros_" + idioma.lower() + ".json"), mode="w", encoding='utf-8')
                    json.dump(dic_ficheros, f_ficheros)
                    f_ficheros.close()
                    print('='*40)
                    print('Archivos de',idioma,'grabados')
            t2 = datetime.now()
            delta = t2 - t1
            return delta.total_seconds()
        return 0

    @staticmethod
    def indexar_ruta(ruta, dic_palabras, dic_ficheros, force_lower):
        dirs = os.listdir(ruta)
        for file in dirs:
            ruta_completa = os.path.join(ruta, file)
            if os.path.isdir(ruta_completa):
                Corpus.indexar_ruta(ruta_completa, dic_palabras, dic_ficheros, force_lower)
            else:
                m = Corpus.re_csv_name.fullmatch(file.strip())
                if m:
                    Corpus.analiza_csv(ruta_completa, dic_palabras, dic_ficheros, force_lower)

    @staticmethod
    def analiza_csv(ruta, dic_palabras, dic_ficheros, force_lower):
        print(ruta)
        dic_ficheros[ruta] = list()
        csvfile = open(ruta, newline='', encoding='utf-8')
        reader = csv.reader(csvfile, dialect='excel', delimiter=';', quotechar='"')
        contador = 0
        for row in reader:
            if contador != 0:
                subtitles = unicodedata.normalize('NFD', row[1])
                for palabra in subtitles.split():
                    m = Corpus.re_limpia_claves.fullmatch(palabra)
                    if m:
                        if force_lower:
                            clave = m['key'].lower()
                        else:
                            clave = m['key']
                        if clave not in dic_palabras:
                            dic_palabras[clave] = list()
                        if (ruta, contador - 1) not in dic_palabras[clave]:
                            dic_palabras[clave].append((ruta, contador - 1))  # tupla de 2 valores
                dic_ficheros[ruta].append((row[0], row[1], row[2]))  # lista de 3 valores
            contador += 1
        csvfile.close()