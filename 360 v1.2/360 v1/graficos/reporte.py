from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from PIL import Image
import requests

class ReporteRestaurantes:
    def __init__(self, api_url):
        self.api_url = api_url
        self.pdf_path = "reporte_personalizado.pdf"
        self.logo_path = "MIND.jpg"  # Ruta de la imagen subida
        self.datos = self.obtener_datos()

    def obtener_datos(self):
        try:
            response = requests.get(self.api_url, timeout=1000)
            response.raise_for_status()
            data = response.json()
            return data.get("restaurants", [])
        except Exception as e:
            print(f"Error obteniendo datos: {e}")
            return []

    def crear_encabezado(self, c, titulo):
        """Dibuja el encabezado con fondo azul inclinado y logo."""
        c.setFillColorRGB(0.0, 0.2, 0.6)
        c.rect(0, 750, 612, 70, fill=True, stroke=False)  # Fondo azul
        
        # Dibujar forma inclinada (75 grados con degradado diagonal)
        c.setFillColorRGB(0.0, 0.2, 0.6)
        c.setStrokeColorRGB(0.0, 0.2, 0.6)
        path = c.beginPath()
        path.moveTo(0, 800)
        path.lineTo(40, 800)
        path.lineTo(612, 730)
        path.lineTo(612, 800)
        path.lineTo(0, 800)
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        
        # Insertar la imagen en lugar del texto
        c.drawImage(self.logo_path, 30, 765, width=60, height=40, mask='auto')  # Ajustar posición y tamaño
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(220, 765, titulo)

    def generar_reporte(self):
        """Genera el PDF estructurado con diseño personalizado."""
        c = canvas.Canvas(self.pdf_path, pagesize=letter)
        self.crear_encabezado(c, "Descripción General")
        
        # Cuadro para Descripción General
        c.setFillColor(colors.lightgrey)
        c.rect(50, 660, 230, 60, fill=True, stroke=False)
        c.setFillColor(colors.black)
        c.drawString(60, 690, "Descripción General")
        
        # Tabla de Restaurantes
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 630, "Calificación de Negocios Más Cercanos")
        
        # Construcción de tabla
        tabla_datos = [["Nombre", "Calificación", "Distancia"]]
        for r in self.datos[:10]:
            tabla_datos.append([r["name"], r.get("rating", "N/A"), f"{r['distance_meters']} m"])
        
        tabla = Table(tabla_datos, colWidths=[250, 100, 100])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey)
        ]))
        tabla.wrapOn(c, 50, 300)
        tabla.drawOn(c, 50, 300)
        
        # Pie de página
        c.setFont("Helvetica", 10)
        c.drawString(270, 50, "Página 1")
        
        c.showPage()  # Nueva página
        self.crear_encabezado(c, "Clasificación de Comentarios")

        # Sección de Comentarios
        c.setFillColor(colors.green)
        c.rect(50, 600, 200, 30, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.drawString(60, 610, "Comentarios Positivos")

        c.setFillColor(colors.red)
        c.rect(300, 600, 200, 30, fill=True, stroke=False)
        c.setFillColor(colors.white)
        c.drawString(310, 610, "Comentarios Negativos")
        
        # Sección de análisis
        c.setFillColor(colors.lightgrey)
        c.rect(50, 400, 400, 80, fill=True, stroke=False)
        c.setFillColor(colors.black)
        c.drawString(60, 460, "Análisis")
        
        # Sección de calificación promedio
        c.setFillColor(colors.yellow)
        c.rect(400, 200, 100, 50, fill=True, stroke=False)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(420, 220, "★ 5")
        c.setFont("Helvetica", 12)
        c.drawString(390, 190, "Calificación Promedio")
        
        # Pie de página
        c.setFont("Helvetica", 10)
        c.drawString(270, 50, "Página 2")
        
        c.save()
        print(f"✅ PDF generado correctamente en {self.pdf_path}")

# Uso del generador
API_URL = "http://127.0.0.1:5000/buscar_restaurantes?direccion=97302,+Fraccionamiento+Las+Américas,+Mérida"
reporte = ReporteRestaurantes(API_URL)
reporte.generar_reporte()
