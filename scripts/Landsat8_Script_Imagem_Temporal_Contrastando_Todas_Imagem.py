import ee
from ee_plugin import Map
import calendar
from datetime import datetime

ee.Initialize()

inicio = '2025-04'
fim = '2025-06'
bands = ['SR_B5', 'SR_B6', 'SR_B4']  # Landsat 8: NIR, SWIR1, RED

def gerar_meses(inicio, fim):
    atual = datetime.strptime(inicio, "%Y-%m")
    fim_dt = datetime.strptime(fim, "%Y-%m")
    while atual <= fim_dt:
        yield atual.year, atual.month
        atual = atual.replace(month=atual.month % 12 + 1, year=atual.year + (atual.month // 12))

def buscar_imagem(data_ini, data_fim, label):
    for limite in range(10, 101, 10):
        colecao = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                   .filterDate(data_ini, data_fim)
                   .filterBounds(Map.getCenter())
                   .filter(ee.Filter.lt('CLOUD_COVER', limite))
                   .sort('CLOUD_COVER')
                   .limit(1))
        imagem = ee.Image(colecao.first())
        if imagem is None:
            continue
        try:
            data_img = ee.Date(imagem.get('system:time_start')).format('YYYY-MM-dd').getInfo()
            nuvem = imagem.get('CLOUD_COVER').getInfo()
        except:
            continue

        imagem = imagem.multiply(0.0000275).add(-0.2)  # Corrigir reflectância

        try:
            roi = Map.getBounds(True)
            percentis = imagem.reduceRegion(
                reducer=ee.Reducer.percentile([5, 98]),
                geometry=roi,
                scale=30,
                bestEffort=True
            )
            min_vals = [percentis.get(b + '_p5').getInfo() for b in bands]
            max_vals = [percentis.get(b + '_p98').getInfo() for b in bands]

            if None not in min_vals and None not in max_vals:
                vis = {'bands': bands, 'min': min_vals, 'max': max_vals, 'gamma': 1.0}
                Map.addLayer(imagem, vis, f'{label}: {data_img} (contraste aplicado)')
                print(f'{label} - {data_img} - nuvem {nuvem:.1f}% - contraste aplicado')
                return
        except Exception as e:
            print(f'{label} - {data_img} - erro no contraste: {e}')

        # Se der problema, visualização padrão
        vis = {'bands': bands, 'min': 0, 'max': 0.3, 'gamma': 1.0}
        Map.addLayer(imagem, vis, f'{label}: {data_img} (nuvem {nuvem if nuvem is not None else "?"}%) - sem contraste')
        print(f'{label} - {data_img} - nuvem {nuvem if nuvem is not None else "?"}% - sem contraste')
        return

    print(f'{label} - Nenhuma imagem encontrada entre {data_ini} e {data_fim}')

for ano, mes in gerar_meses(inicio, fim):
    ultimo = calendar.monthrange(ano, mes)[1]
    buscar_imagem(f"{ano}-{mes:02d}-01", f"{ano}-{mes:02d}-15", f"{ano}-{mes:02d} (1–15)")
    buscar_imagem(f"{ano}-{mes:02d}-20", f"{ano}-{mes:02d}-{ultimo}", f"{ano}-{mes:02d} (20–fim)")
