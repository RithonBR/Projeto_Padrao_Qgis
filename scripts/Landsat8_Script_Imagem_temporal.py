import ee
from ee_plugin import Map
import calendar
from datetime import datetime

# Inicializar Earth Engine
ee.Initialize()

# ====== PARÂMETROS ======
inicio = '2025-04'
fim = '2025-06'
bands = ['SR_B5', 'SR_B6', 'SR_B4']  # NIR, SWIR1, RED (equivalente ao B8, B11, B4)

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
        colecao = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                   .filterDate(data_ini, data_fim)
                   .filterBounds(Map.getCenter())
                   .filter(ee.Filter.lt('CLOUD_COVER', limite))
                   .sort('CLOUD_COVER')
                   .limit(1))

        imagem = ee.Image(colecao.first())
        if imagem is not None:
            try:
                data_img = ee.Date(imagem.get('system:time_start')).format('YYYY-MM-dd').getInfo()
            except:
                continue

            # Corrigir reflectância para valores reais
            imagem = imagem.multiply(0.0000275).add(-0.2)

            vis = {'bands': bands, 'min': 0, 'max': 0.3, 'gamma': 1.0}
            Map.addLayer(imagem, vis, f'{label}: {data_img} (≤ {limite}%)')
            print(f'{label} - {data_img} - nuvem ≤ {limite}%')
            return
    print(f'{label} - Nenhuma imagem encontrada entre {data_ini} e {data_fim}')

# ====== LOOP POR MÊS ======
for ano, mes in gerar_meses(inicio, fim):
    ultimo = calendar.monthrange(ano, mes)[1]
    buscar_imagem(f"{ano}-{mes:02d}-01", f"{ano}-{mes:02d}-15", f"{ano}-{mes:02d} (1–15)")
    buscar_imagem(f"{ano}-{mes:02d}-20", f"{ano}-{mes:02d}-{ultimo}", f"{ano}-{mes:02d} (20–fim)")
