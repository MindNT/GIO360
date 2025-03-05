from reporte import ReporteRestaurantes

# 📌 Definir la URL del endpoint
API_URL = "http://127.0.0.1:5000/buscar_restaurantes?direccion=97302,+Fraccionamiento+Las+Am%C3%A9ricas,+M%C3%A9rida"

reporte = ReporteRestaurantes(API_URL)
reporte.generar_reporte()
