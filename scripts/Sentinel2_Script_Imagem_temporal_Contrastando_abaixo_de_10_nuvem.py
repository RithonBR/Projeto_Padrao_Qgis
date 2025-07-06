import ee
from ee_plugin import Map
import calendar
from datetime import datetime

# Inicializar Earth Engine
ee.Initialize()

# ====== PARÂMETROS ======
inicio = '2025-04'
fim = '2025-06'
bands = ['B8', 'B11', 'B4']

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

            # Se nuvem for < 10%, aplicar contraste por percentis
            nuvem = imagem.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
            if nuvem < 10:
                try:
                    roi = Map.getBounds(True)
                    percentis = imagem.reduceRegion(
                        reducer=ee.Reducer.percentile([5, 98]),
                        geometry=roi,
                        scale=90,
                        bestEffort=True
                    )
                    min_vals = [percentis.get(b + '_p5').getInfo() for b in bands]
                    max_vals = [percentis.get(b + '_p98').getInfo() for b in bands]
                    
                    if None not in min_vals and None not in max_vals:
                        vis = {
                            'bands': bands,
                            'min': min_vals,
                            'max': max_vals,
                            'gamma': 1.0
                        }
                        Map.addLayer(imagem, vis, f'{label}: {data_img} (contraste 5–98%)')
                        print(f'{label} - {data_img} - nuvem {nuvem:.1f}% - contraste aplicado')
                        return
                except:
                    print(f'{label} - {data_img} - erro ao aplicar contraste')
                    continue
            
            # Caso não tenha contraste (nuvem ≥ 10%), visualização padrão
            vis = {'bands': bands, 'min': 0, 'max': 5000, 'gamma': 1.0}
            Map.addLayer(imagem, vis, f'{label}: {data_img} (nuvem {nuvem:.1f}%)')
            print(f'{label} - {data_img} - nuvem {nuvem:.1f}% - sem contraste')
            return

    print(f'{label} - Nenhuma imagem encontrada entre {data_ini} e {data_fim}')

# ====== LOOP POR MÊS E QUINZENAS ======
for ano, mes in gerar_meses(inicio, fim):
    ultimo = calendar.monthrange(ano, mes)[1]
    buscar_imagem(f"{ano}-{mes:02d}-01", f"{ano}-{mes:02d}-15", f"{ano}-{mes:02d} (1–15)")
    buscar_imagem(f"{ano}-{mes:02d}-20", f"{ano}-{mes:02d}-{ultimo}", f"{ano}-{mes:02d} (20–fim)")
