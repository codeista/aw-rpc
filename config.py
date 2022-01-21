from configparser import ConfigParser

from unit import UnitType, UnitClass, UnitConfig


class Config:
    def __init__(self):
        cfg = ConfigParser()
        cfg.read('config.ini')

        # get unit configs
        self.units = {}
        for unit_type in UnitType:
            name = unit_type.name
            self.units[name] = UnitConfig(
                UnitClass[cfg.get(name, 'class')],
                int(cfg.get(name, 'cost')),
                int(cfg.get(name, 'move')),
                int(cfg.get(name, 'rangemin')),
                int(cfg.get(name, 'rangemax')),
                int(cfg.get(name, 'fuel')),
                int(cfg.get(name, 'vision')),
                int(cfg.get(name, 'hp')),
                int(cfg.get(name, 'ammo')),
                []
            )
