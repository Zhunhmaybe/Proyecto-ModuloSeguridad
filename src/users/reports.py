import openpyxl
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from django.http import HttpResponse
from users.models import Usuario, Rol, Funcion
from modules.models import Modulo
from audit.models import Auditoria

def _build_pdf_response(filename, title, headers, data):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))
    
    table_data = [headers] + data
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(t)
    doc.build(elements)
    return response

def _build_xlsx_response(filename, title, headers, data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title
    ws.append(headers)
    for row in data:
        ws.append(row)
        
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

# HU10: Reporte de Roles, Funciones y Módulos
def report_roles(request):
    fmt = request.GET.get('format', 'pdf')
    rol_id = request.GET.get('rol_id')
    
    query = Rol.objects.all()
    if rol_id:
        query = query.filter(id_rol=rol_id)
        
    headers = ['ID', 'Rol', 'Estado', 'Funciones (Módulo)']
    data = []
    for r in query:
        # Funciones asociadas
        funcs = []
        for f in r.funciones.all():
            mods = ", ".join([m.nombre_modulo for m in f.modulos.all()])
            funcs.append(f"{f.nombre_funcion} ({mods})")
            
        estado = "Activo" if r.estado_rol else "Inactivo"
        data.append([str(r.id_rol), r.nombre_rol, estado, "\n".join(funcs)])
        
    if fmt == 'xlsx':
        return _build_xlsx_response('reporte_roles.xlsx', 'Roles', headers, data)
    return _build_pdf_response('reporte_roles.pdf', 'Reporte de Roles', headers, data)

# HU11: Reporte de Usuarios, Roles, Funciones y Módulos
def report_usuarios(request):
    fmt = request.GET.get('format', 'pdf')
    user_id = request.GET.get('user_id')
    
    query = Usuario.objects.all()
    if user_id:
        query = query.filter(id=user_id)
        
    headers = ['Usuario', 'Email', 'Cédula', 'Estado', 'Roles']
    data = []
    for u in query:
        roles_str = ", ".join([r.nombre_rol for r in u.roles.all()])
        estado = "Activo" if u.estado else "Inactivo"
        data.append([u.user_name, u.email, u.cedula, estado, roles_str])
        
    if fmt == 'xlsx':
        return _build_xlsx_response('reporte_usuarios.xlsx', 'Usuarios', headers, data)
    return _build_pdf_response('reporte_usuarios.pdf', 'Reporte de Usuarios', headers, data)

# HU12: Reporte de Módulos y Funciones
def report_modulos(request):
    fmt = request.GET.get('format', 'pdf')
    modulo_id = request.GET.get('modulo_id')
    
    query = Modulo.objects.all()
    if modulo_id:
        query = query.filter(id_modulo=modulo_id)
        
    headers = ['ID', 'Módulo', 'Estado', 'Funciones Disponibles']
    data = []
    for m in query:
        funcs = ", ".join([f.nombre_funcion for f in m.funciones.all()])
        estado = "Activo" if m.estado_modulo else "Inactivo"
        data.append([str(m.id_modulo), m.nombre_modulo, estado, funcs])
        
    if fmt == 'xlsx':
        return _build_xlsx_response('reporte_modulos.xlsx', 'Modulos', headers, data)
    return _build_pdf_response('reporte_modulos.pdf', 'Reporte de Módulos', headers, data)

# HU13: Reporte de Pistas de Auditoría por Usuario
def report_auditoria(request):
    fmt = request.GET.get('format', 'pdf')
    user_name = request.GET.get('user_name')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    query = Auditoria.objects.all()
    if user_name:
        query = query.filter(username__user_name=user_name)
    if fecha_inicio:
        query = query.filter(fecha_creacion__gte=fecha_inicio)
    if fecha_fin:
        query = query.filter(fecha_creacion__lte=fecha_fin)
        
    headers = ['Fecha/Hora', 'Usuario', 'Acción', 'Descripción']
    data = []
    for a in query:
        uname = a.username.user_name if a.username else 'N/A'
        dt = a.fecha_creacion.strftime("%Y-%m-%d %H:%M:%S")
        data.append([dt, uname, a.accion, str(a.descripcion)])
        
    if fmt == 'xlsx':
        return _build_xlsx_response('reporte_auditoria.xlsx', 'Auditoria', headers, data)
    return _build_pdf_response('reporte_auditoria.pdf', 'Reporte de Auditoria', headers, data)
