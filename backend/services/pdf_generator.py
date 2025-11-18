from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
import os
from datetime import datetime
import json
from io import BytesIO
import base64
import tempfile

class PDFReportGenerator:
    def __init__(self):
        self.output_dir = 'reports'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_report(self, detection_data, annotated_image_data=None, output_path=None):
        """Generate comprehensive PDF report for pothole detection"""
        temp_files = []  # Track temporary files for cleanup
        
        try:
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(self.output_dir, f"pothole_report_{timestamp}.pdf")
            
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=0.5*inch)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
                alignment=1,
                textColor=colors.HexColor('#2c3e50'),
                fontName='Helvetica-Bold'
            )
            
            # Title Section
            story.append(Paragraph("POTHOLE DETECTION REPORT", title_style))
            
            # Report metadata
            meta_style = ParagraphStyle(
                'Meta',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.gray,
                alignment=1
            )
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", meta_style))
            story.append(Spacer(1, 20))
            
            # Executive Summary
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.HexColor('#34495e'),
                fontName='Helvetica-Bold'
            )
            
            story.append(Paragraph("Executive Summary", heading_style))
            
            total_potholes = len(detection_data.get('detections', []))
            high_severity = len([d for d in detection_data.get('detections', []) if d.get('severity', {}).get('level') == 'high'])
            medium_severity = len([d for d in detection_data.get('detections', []) if d.get('severity', {}).get('level') == 'medium'])
            low_severity = len([d for d in detection_data.get('detections', []) if d.get('severity', {}).get('level') == 'low'])
            
            summary_text = f"""
            This report summarizes the pothole detection analysis conducted on {datetime.now().strftime('%B %d, %Y')}. 
            The AI-powered detection system identified <b>{total_potholes}</b> potholes with varying severity levels.
            """
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Severity Summary Table
            summary_data = [
                ['Severity Level', 'Count', 'Priority'],
                ['High', str(high_severity), 'Immediate'],
                ['Medium', str(medium_severity), 'High'],
                ['Low', str(low_severity), 'Medium']
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e74c3c')),
                ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#f39c12')),
                ('BACKGROUND', (0, 3), (0, 3), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Location Information
            if detection_data.get('location'):
                story.append(Paragraph("Location Information", heading_style))
                location = detection_data['location']
                location_text = f"""
                <b>GPS Coordinates:</b> {location.get('latitude', 'N/A'):.6f}, {location.get('longitude', 'N/A'):.6f}
                """
                story.append(Paragraph(location_text, styles['Normal']))
                story.append(Spacer(1, 15))
            
            # Annotated Image - FIXED VERSION
            if annotated_image_data:
                story.append(Paragraph("Detection Results", heading_style))
                try:
                    # Handle base64 image
                    if ',' in annotated_image_data:
                        annotated_image_data = annotated_image_data.split(',')[1]
                    
                    image_data = base64.b64decode(annotated_image_data)
                    
                    # Use a proper temporary file that won't be deleted too early
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                        temp_file.write(image_data)
                        temp_file_path = temp_file.name
                        temp_files.append(temp_file_path)  # Track for cleanup
                    
                    print(f"🖼️ Temporary image created: {temp_file_path}")
                    
                    # Add image to PDF
                    img = Image(temp_file_path, width=5*inch, height=3.5*inch)
                    img.hAlign = 'CENTER'
                    story.append(img)
                    story.append(Spacer(1, 15))
                    
                except Exception as e:
                    print(f"❌ Error adding image to PDF: {e}")
                    story.append(Paragraph("<i>Annotated image unavailable for PDF generation</i>", styles['Italic']))
            
            # Severity Distribution
            if total_potholes > 0:
                story.append(Paragraph("Severity Distribution", heading_style))
                
                # Create bar chart
                drawing = Drawing(400, 200)
                chart = VerticalBarChart()
                chart.x = 50
                chart.y = 50
                chart.height = 125
                chart.width = 300
                chart.data = [[high_severity, medium_severity, low_severity]]
                chart.categoryAxis.categoryNames = ['High', 'Medium', 'Low']
                chart.bars[0].fillColor = colors.HexColor('#e74c3c')
                chart.bars[1].fillColor = colors.HexColor('#f39c12')
                chart.bars[2].fillColor = colors.HexColor('#27ae60')
                chart.valueAxis.valueMin = 0
                chart.valueAxis.valueMax = max([high_severity, medium_severity, low_severity]) + 1
                drawing.add(chart)
                story.append(drawing)
                story.append(Spacer(1, 20))
            
            # Detailed Findings
            if total_potholes > 0:
                story.append(Paragraph("Detailed Findings", heading_style))
                
                for i, detection in enumerate(detection_data.get('detections', []), 1):
                    severity = detection.get('severity', {})
                    bbox = detection.get('bbox', [0, 0, 0, 0])
                    area = bbox[2] * bbox[3] if len(bbox) >= 4 else 0
                    
                    # Severity color mapping
                    severity_colors = {
                        'high': '#e74c3c',
                        'medium': '#f39c12',
                        'low': '#27ae60'
                    }
                    
                    severity_level = severity.get('level', 'medium')
                    pothole_title = Paragraph(
                        f"Pothole #{i} - <font color='{severity_colors.get(severity_level, '#f39c12')}'>{severity_level.upper()} SEVERITY</font>",
                        ParagraphStyle(
                            'PotholeTitle',
                            parent=styles['Heading3'],
                            fontSize=12,
                            textColor=colors.black,
                            spaceAfter=6
                        )
                    )
                    story.append(pothole_title)
                    
                    pothole_data = [
                        ['Confidence', f"{detection.get('confidence', 0)*100:.1f}%"],
                        ['Size', f"{bbox[2]} × {bbox[3]} pixels" if len(bbox) >= 4 else 'Unknown'],
                        ['Area', f"{area} px²"],
                        ['Severity Score', f"{severity.get('score', 0)*100:.1f}/100"],
                        ['Description', severity.get('description', 'No description available')]
                    ]
                    
                    if detection.get('location'):
                        loc = detection['location']
                        pothole_data.append([
                            'Location', 
                            f"Lat: {loc.get('latitude', 'N/A'):.6f}<br/>Lon: {loc.get('longitude', 'N/A'):.6f}"
                        ])
                    
                    pothole_table = Table(pothole_data, colWidths=[1.5*inch, 4*inch])
                    pothole_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    story.append(pothole_table)
                    story.append(Spacer(1, 15))
            
            # Recommendations
            story.append(Paragraph("Recommendations", heading_style))
            
            recommendations = []
            if high_severity > 0:
                recommendations.append(
                    f"🚨 <b>Immediate Action Required:</b> {high_severity} high-severity potholes need urgent repair."
                )
            if medium_severity > 0:
                recommendations.append(
                    f"⚠️ <b>Schedule Repairs:</b> {medium_severity} medium-severity potholes should be addressed soon."
                )
            if low_severity > 0:
                recommendations.append(
                    f"📝 <b>Monitor:</b> {low_severity} low-severity potholes should be regularly monitored."
                )
            
            for rec in recommendations:
                story.append(Paragraph(rec, styles['Normal']))
                story.append(Spacer(1, 5))
            
            # Build PDF
            print("🔄 Building PDF document...")
            doc.build(story)
            print("✅ PDF build completed")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error in PDF generation: {str(e)}")
            raise e
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        print(f"🧹 Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    print(f"⚠️ Could not clean up {temp_file}: {e}")

# Global instance
pdf_generator = PDFReportGenerator()