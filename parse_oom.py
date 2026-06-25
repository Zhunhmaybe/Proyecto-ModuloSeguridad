import xml.etree.ElementTree as ET

filepath = r'c:\Users\david\Desktop\DeliveryGRA\PowerDiser\CD_Delivery.oom'
try:
    with open(filepath, 'r', encoding='utf-16') as f:
        content = f.read()
except Exception:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

content = content.replace('"UTF-16"', '"UTF-8"')

root = ET.fromstring(content)
namespaces = {'o': 'object', 'a': 'attribute', 'c': 'collection'}

print('--- Classes ---')
for cls in root.findall('.//o:Class', namespaces):
    name = cls.find('a:Name', namespaces)
    if name is not None:
        print('Class: ' + name.text)
        attrs = cls.findall('.//o:Attribute', namespaces)
        if attrs:
            for attr in attrs:
                attr_name = attr.find('a:Name', namespaces)
                if attr_name is not None:
                    print('  - Attribute: ' + attr_name.text)
