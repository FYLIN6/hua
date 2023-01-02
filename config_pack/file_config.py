import os

SERVER_ROOT = os.path.dirname(os.path.abspath(os.path.join(__file__, '../')))


class FileConfig(object):
    log_folder = os.path.join(SERVER_ROOT, 'log')
    log_file_path = os.path.join(log_folder, 'log.log')

    def __init__(self):
        self.__config_path = os.path.join(SERVER_ROOT, 'config_pack/')
        self.__output_folder = os.path.join(SERVER_ROOT, 'output/')
        self.__input_folder = os.path.join(SERVER_ROOT, 'input/')
        self.__transportation = os.path.join(SERVER_ROOT, 'transportation/')
        self.__animation_input_path = os.path.join(SERVER_ROOT, 'animation/InputFiles/')
        self.__animation_path = os.path.join(SERVER_ROOT, 'animation/')

    def get_input_folder(self):
        return self.__input_folder

    def get_output_folder(self):
        return self.__output_folder

    def get_animation_path(self):
        return self.__animation_path

    def get_animation_input_path(self):
        return self.__animation_input_path


if __name__ == '__main__':
    config = FileConfig()
    print(config.get_input_folder())