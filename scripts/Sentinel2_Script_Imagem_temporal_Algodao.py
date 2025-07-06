import ee
from ee_plugin import Map
import calendar
from datetime import datetime

# Inicializar Earth Engine
ee.Initialize()

# ====== PARÂMETROS ======
inicio = '2025-04'
fim = '2025-06'
bands_8114 = ['B8', 'B11', 'B4']
bands_rgb = ['B4', 'B3', 'B2']  # RGB

# ====== GERAR LISTA DE (ANO, MÊS) ======
def gerar_meses(inicio, fim):
    atual = datetime.strptime(inicio, "%Y-%m")
    fim_dt = datetime.strptime(fim, "%Y-%m")
    while atual <= fim_dt:
        yield atual.year, atual.month
        atual = atual.replace(month=atual.month % 12 + 1, year=atual.year + (atual.month // 12))

# ====== BUSCAR MELHOR IMAGEM POR PERÍODO ======
def buscar_imagem(data_ini, data_fim, label):
    for limite in range(10, 101, 10):
        colecao = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                   .filterDate(data_ini, data_fim)
                   .filterBounds(Map.getCenter())
                   .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', limite))
                   .sort('CLOUDY_PIXEL_PERCENTAGE')
                   .limit(1))

        imagem = ee.Image(colecao.first())
        if imagem is not None:
            props = imagem.select(0).get('system:time_start')
            try:
                data_img = ee.Date(props).format('YYYY-MM-dd').getInfo()
            except:
                continue

            # Visualização 8114
            vis_8114 = {'bands': bands_8114, 'min': 0, 'max': 5000, 'gamma': 1.0}
            Map.addLayer(imagem, vis_8114, f'{label} (8114): {data_img} (≤ {limite}%)')

            # Visualização RGB
            vis_rgb = {'bands': bands_rgb, 'min': 0, 'max': 3000, 'gamma': 1.2}
            Map.addLayer(imagem, vis_rgb, f'{label} (RGB): {data_img} (≤ {limite}%)')

            print(f'{label} - {data_img} - nuvem ≤ {limite}%')
            return
    print(f'{label} - Nenhuma imagem encontrada entre {data_ini} e {data_fim}')

# ====== LOOP POR MÊS ======
for ano, mes in gerar_meses(inicio, fim):
    ultimo = calendar.monthrange(ano, mes)[1]
    buscar_imagem(f"{ano}-{mes:02d}-01", f"{ano}-{mes:02d}-15", f"{ano}-{mes:02d} (1–15)")
    buscar_imagem(f"{ano}-{mes:02d}-20", f"{ano}-{mes:02d}-{ultimo}", f"{ano}-{mes:02d} (20–fim)")
