import datetime
import logging

from standard.action import Action
from xml_parser.xml_parser import XmlParser
from xml_parser.element_creator import ElementCreator
from config_pack.file_config import FileConfig
from standard.sandbox import Sandbox
from animation.animation_main import AnimationMain


class RunFileWithAnimation(Sandbox):
    def __init__(self, xml_file_name=None, seed=0):
        super().__init__()
        self.__xml_file_name = xml_file_name
        if self.__xml_file_name is not None:
            xml_parser = XmlParser()
            gridmover_system_dict = xml_parser.parse_to_dict(self.__xml_file_name)
            element_creator = self.add_child(ElementCreator())
            element_creator.create(gridmover_system_dict, seed)
            self.__on_end = Action().add(element_creator.gridmover_system_handler.end)
            transportation_network_dict = gridmover_system_dict['GridMoverSystem']['TransportationNetwork'] if \
                'TransportationNetwork' in gridmover_system_dict['GridMoverSystem'] else dict()
            self.dimension = eval(
                transportation_network_dict['Dimension']) if 'Dimension' in transportation_network_dict else (
                30, 35)

    @property
    def on_end(self):
        return self.__on_end


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    file_config = FileConfig()
    xml_file_name = file_config.get_input_folder() + '/scenario_1.xml'
    # You can change random_seed to get different job generation situations. For example, random_seed=1,2,...
    random_seed = 0
    animation_test = RunFileWithAnimation(xml_file_name=xml_file_name, seed=random_seed)
    animation_test.run(duration=datetime.timedelta(days=10))
    animation_test.on_end.invoke()
    animation_main = AnimationMain(animation_test.dimension, random_seed)
    animation_main.run()



