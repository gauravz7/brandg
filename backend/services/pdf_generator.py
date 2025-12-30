import os
import traceback
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDFGenerator:
    def generate_pdf(self, task_id: str, base_dir: str, title: str, report_text: str, color_assets: list = None, brand_assets: list = None, css_assets: list = None):
        path = os.path.join(base_dir, task_id, f"{title}_Brand_Report.pdf")
        
        try:
            doc = SimpleDocTemplate(path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            story.append(Paragraph(f"Brand Identity Report: {title}", styles['Title']))
            story.append(Spacer(1, 12))
            
            # Add Snapshot if available
            snapshot_path = os.path.join(base_dir, task_id, "Snapshot", "homepage.png")
            if os.path.exists(snapshot_path):
                story.append(Paragraph("Website Homepage Snapshot", styles['Heading2']))
                img = Image(snapshot_path, width=450, height=280) 
                story.append(img)
                story.append(Spacer(1, 20))
            
            # Add Color Palette if available
            if color_assets:
                story.append(Paragraph("Primary Brand Colors", styles['Heading2']))
                story.append(Spacer(1, 10))
                
                # Flowables for colors: small swatch + hex code
                from reportlab.platypus import Table, TableStyle
                color_data = []
                row = []
                for i, item in enumerate(color_assets):
                    hex_code = item['hex']
                    swatch_path = item['path']
                    
                    if os.path.exists(swatch_path):
                        img = Image(swatch_path, width=30, height=30)
                        row.append([img, Paragraph(hex_code, styles['BodyText'])])
                    
                    if len(row) == 4 or i == len(color_assets) - 1:
                        # Convert partial row to actual table rows
                        processed_row = []
                        for cell in row:
                            processed_row.extend(cell)
                        color_data.append(processed_row)
                        row = []
                
                if color_data:
                    t = Table(color_data, colWidths=[40, 60] * 4)
                    t.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 20))

            # Add Brand Assets if available
            if brand_assets:
                story.append(Paragraph("Captured Brand Assets (Logos & Icons)", styles['Heading2']))
                story.append(Spacer(1, 10))
                
                asset_data = []
                current_row = []
                for i, asset_path in enumerate(brand_assets):
                    try:
                        if asset_path.lower().endswith('.svg'):
                            from svglib.svglib import svg2rlg
                            from reportlab.graphics import renderPDF
                            drawing = svg2rlg(asset_path)
                            if drawing:
                                # Scale the drawing
                                scaling_factor = 60.0 / max(drawing.width, drawing.height)
                                drawing.width *= scaling_factor
                                drawing.height *= scaling_factor
                                drawing.scale(scaling_factor, scaling_factor)
                                current_row.append(drawing)
                        elif asset_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                            img = Image(asset_path, width=60, height=60, kind='proportional')
                            current_row.append(img)
                    except Exception as e:
                        print(f"Failed to process asset {asset_path} for PDF: {e}")
                        continue
                    
                    if len(current_row) == 5 or i == len(brand_assets) - 1:
                        if current_row:
                            asset_data.append(current_row)
                        current_row = []
                
                if asset_data:
                    t = Table(asset_data, colWidths=[80]*5)
                    t.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 20))

            # Add CSS Assets if available
            if css_assets:
                story.append(Paragraph("Technical Identity (CSS Stylesheets)", styles['Heading2']))
                story.append(Spacer(1, 10))
                
                # Code style for CSS
                code_style = ParagraphStyle(
                    'CodeStyle',
                    parent=styles['BodyText'],
                    fontName='Courier',
                    fontSize=8,
                    leading=10,
                    leftIndent=20,
                    rightIndent=20,
                    spaceAfter=10,
                    borderPadding=5,
                    backColor=colors.whitesmoke
                )
                
                for css_path in css_assets:
                    if os.path.exists(css_path):
                        filename = os.path.basename(css_path)
                        story.append(Paragraph(f"File: {filename}", styles['Heading3']))
                        
                        try:
                            with open(css_path, 'r', encoding='utf-8') as f:
                                css_content = f.read()
                            
                            # Limit CSS content to avoid massive PDFs, but keep relevant parts
                            if len(css_content) > 2000:
                                css_content = css_content[:2000] + "\n... (truncated for brevity)"
                            
                            # Basic XML escaping for Paragraph
                            from xml.sax.saxutils import escape
                            escaped_css = escape(css_content).replace('\n', '<br/>').replace(' ', '&nbsp;')
                            story.append(Paragraph(escaped_css, code_style))
                        except Exception as e:
                            story.append(Paragraph(f"Error reading CSS file: {e}", styles['BodyText']))
                        
                story.append(Spacer(1, 20))

            # Report Content (from Gemini)
            story.append(Paragraph("Detailed Analysis & Guidelines", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            style_body = styles['BodyText']
            for line in report_text.split('\n'):
                line = line.strip()
                if not line: continue
                
                if line.startswith('# '):
                    story.append(Paragraph(line.replace('# ', ''), styles['Heading1']))
                elif line.startswith('## '):
                    story.append(Paragraph(line.replace('## ', ''), styles['Heading2']))
                elif line.startswith('### '):
                    story.append(Paragraph(line.replace('### ', ''), styles['Heading3']))
                elif line.startswith('- ') or line.startswith('* '):
                    story.append(Paragraph(f"• {line[2:]}", style_body))
                else:
                    # Basic cleaning of bold/italic markdown for ReportLab Paragraph
                    import re
                    # Bold
                    clean_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                    clean_line = re.sub(r'__(.*?)__', r'<b>\1</b>', clean_line)
                    # Italic
                    clean_line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', clean_line)
                    clean_line = re.sub(r'_(.*?)_', r'<i>\1</i>', clean_line)
                    
                    try:
                        story.append(Paragraph(clean_line, style_body))
                    except:
                        # If XML parsing still fails, try plain text
                        story.append(Paragraph(line, style_body))
                story.append(Spacer(1, 6))
            
            doc.build(story)
            return path
        except Exception as e:
            print(f"PDF Generation failed: {traceback.format_exc() if 'traceback' in globals() else e}")
            return None
