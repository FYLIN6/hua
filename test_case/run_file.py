import datetime as dt
import logging

from standard.action import Action
from xml_parser.xml_parser import XmlParser
from xml_parser.element_creator import ElementCreator
from config_pack.file_config import FileConfig
from standard.sandbox import Sandbox


class RunFile(Sandbox):
    def __init__(self, xml_file_name, seed=0):
        super().__init__()
        self.__xml_file_name = xml_file_name

        file_name = self.__xml_file_name
        xml_parser = XmlParser()
        gridmvoer_system_dict = xml_parser.parse_to_dict(file_name)
        creator = self.add_child(ElementCreator())
        creator.create(gridmvoer_system_dict, seed)

        self.__on_end = Action().add(creator.gridmover_system_handler.end)

    @property
    def on_end(self):
        return self.__on_end


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    file_config = FileConfig()
    xml_file_name = file_config.get_input_folder() + '/scenario_1.xml'
    sim_start_time = dt.datetime.now()
    # You can change random_seed to get different job generation situations. For example, random_seed=1,2,...
    random_seed = 0
    main = RunFile(xml_file_name=xml_file_name, seed=random_seed)
    main.run(duration=dt.timedelta(days=10))
    main.on_end.invoke()
    sim_end_time = dt.datetime.now()
    logging.info('CPU time is {}'.format((sim_end_time - sim_start_time).total_seconds()))
