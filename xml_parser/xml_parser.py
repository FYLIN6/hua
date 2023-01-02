import xml.etree.ElementTree as ET


class XmlParser:
    def __init__(self):
        self.__attrib_tag = ['Id', 'Type', 'From', 'To', 'ExitFrom', 'EnterTo', 'Capacity']

    def parse_to_dict(self, file_name):
        xml_element = ET.parse(file_name, parser=ET.XMLParser(encoding='utf-8'))
        root = xml_element.getroot()
        return self.parse_xml_to_dict(root)

    def parse_xml_to_dict(self, root):
        xml_dict = {root.tag: self.__get_element_value(root)}
        return xml_dict

    def __get_element_value(self, element):
        value = []
        if len(element.attrib):
            for attrib_key, attrib_value in element.attrib.items():
                attrib_dict = {}
                attrib_dict[attrib_key] = attrib_value
                value.append(attrib_dict)
        if len(element):
            for child in element:
                child_dict = {}
                child_value = self.__get_element_value(child)
                if child_value:
                    child_dict[child.tag] = child_value
                    value.append(child_dict)
        if element.text and element.text.strip():
            if len(element) == 0:
                if len(element.attrib):
                    text_dict = {}
                    text_dict['Text'] = element.text.strip()
                    value.append(text_dict)
                else:
                    value = element.text.strip()
        if type(value) is list:
            if len(value):
                value_count = len(value)
                value_key = []
                for data in value:
                    for key in data.keys():
                        value_key.append(key)
                value_key_set = set(value_key)
                if value_count == len(value_key_set):
                    value_dict = {}
                    for data in value:
                        for value_key, value_data in data.items():
                            value_dict[value_key] = value_data
                    value = value_dict
            else:
                value = None
        return value

    def parse_dict_to_xml(self, xml_dict):
        if type(xml_dict) is dict:
            root_xml_dict = {}

            if len(xml_dict) == 1:
                root_xml_dict = xml_dict
            elif len(xml_dict) > 1:
                root_xml_dict["Root"] = xml_dict

            if len(root_xml_dict) == 1:
                xml_tag = list(root_xml_dict.keys())[0]
                xml_value = list(root_xml_dict.values())[0]
                return self.__get_element(xml_tag, xml_value, 0)
            else:
                return None

    def parse_dict_to_xml_string(self, xml_dict):
        xml_element = self.parse_dict_to_xml(xml_dict)
        if xml_element is not None:
            return self.parse_xml_to_string(xml_element)
        else:
            ""

    def __get_element(self, tag, value, level):
        if type(value) is dict:
            value = [value]
        element = ET.Element(tag)
        if type(value) is list:
            xml_text = ""
            last_child_element = None
            for value_dict in value:
                for value_tag, value_data in value_dict.items():
                    if value_tag in self.__attrib_tag:
                        element.set(value_tag, str(value_data))
                    elif value_tag == 'Text':
                        xml_text = str(value_data)
                    else:
                        child_element = self.__get_element(value_tag, value_data, level + 1)
                        element.append(child_element)
                        last_child_element = child_element
            element.text = "\n"
            for i in range(0, level):
                element.text += "\t"
            if xml_text:
                element.text += "\t" + xml_text + "\n"
                for i in range(0, level):
                    element.text += "\t"
            if last_child_element is not None:
                element.text += "\t"
                last_child_element.tail = last_child_element.tail[:-1]
        else:
            element.text = str(value) if value else ""
        element.tail = "\n"
        for i in range(0, level):
            element.tail += "\t"
        return element

    def parse_xml_to_string(self, element):
        return ET.tostring(element, encoding='utf-8').decode('utf-8').expandtabs(4) if element is not None else ""
