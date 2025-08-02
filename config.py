from configparser import ConfigParser

from core.unit import UnitType, UnitClass, UnitConfig


class Config:
    def __init__(self):
        cfg = ConfigParser()
        cfg.read('config.ini')

        # get unit configs
        self.units = {}
        for unit_type in UnitType:
            name = unit_type.name
            self.units[name] = UnitConfig(
                cls=UnitClass[cfg.get(name, 'class')],
                cost=int(cfg.get(name, 'cost')),
                move=int(cfg.get(name, 'move')),
                rangemin=int(cfg.get(name, 'rangemin')),
                rangemax=int(cfg.get(name, 'rangemax')),
                max_fuel=int(cfg.get(name, 'fuel')),
                vision=int(cfg.get(name, 'vision')),
                max_hp=int(cfg.get(name, 'hp')),
                max_ammo=int(cfg.get(name, 'ammo'))
            )
