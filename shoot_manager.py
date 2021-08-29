import numpy as np


class ShootManager(object):
    def __init__(self):
        self._frame = 0
        self._bullet = []
        self._use_bullet = []

        self._damage = []
        self._hit = []
        self._valid_damages = [0, 97, 87, 78, 73, 45, 41, 82, 74, 66, 62, 38, 35]
        self._valid_damages = np.array(self._valid_damages)

    def add_info(self, bullet, damage):
        self._bullet.append(bullet)
        if len(self._bullet) > 1:
            pre_bullet = self._bullet[self._frame - 1]
            cur_bullet = self._bullet[self._frame]
            if pre_bullet != cur_bullet:
                self._use_bullet.append(self._frame)

        self._damage.append(damage)
        if len(self._damage) > 1:
            pre_damage = self._damage[self._frame - 1]
            cur_damage = self._damage[self._frame]
            if pre_damage != cur_damage:
                self._hit.append(self._frame)

        self._frame += 1

    def fix_damage(self, damage):
        if len(self._damage):
            last_damage = self._damage[-1]
            valid_damages = self._valid_damages + last_damage
            if damage in valid_damages:
                return damage
            else:
                v = valid_damages - damage
                v = np.abs(v)
                nearest_damage = valid_damages[v == np.min(v)]
                print("nv", nearest_damage[0])
                return nearest_damage[0]
        return damage

    def get_hit_percentage(self):
        a = len(self._use_bullet)
        b = len(self._hit)
        if a == 0:
            return [0], [0], 0.0
        else:
            return self._use_bullet, self._hit, b / a
        # return a, b, b / a
