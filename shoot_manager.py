import numpy as np

wingman_reload_zeros = 19


class ShootManager(object):
    def __init__(self):
        self._frame = 0
        self._bullet = []
        self._use_bullet = []

        self._damage = []
        self._hit = []
        self._valid_damages = [0, 97, 87, 78, 73, 45, 41, 82, 74, 66, 62, 38, 35]
        self._valid_damages = np.array(self._valid_damages)

        self._reload_flag = False
        self._reload_counter = 0

    def add_info(self, bullet, damage):
        if self._reload_flag:
            if bullet == "7":
                self._reload_flag = False
                self._reload_counter = 0
                self._bullet[-1] = "8"

            bullet = "0"
            if self._reload_counter == wingman_reload_zeros:
                self._reload_flag = False
                self._reload_counter = 0
            else:
                self._reload_counter += 1

        self._bullet.append(bullet)
        if len(self._bullet) > 1:
            pre_bullet = self._bullet[self._frame - 1]
            cur_bullet = self._bullet[self._frame]
            if not pre_bullet in ["8", "9"] and cur_bullet == "8":
                # if pre_bullet != "9" and cur_bullet == "8":
                self._reload_counter += 1
                self._reload_flag = True
                self._bullet[-1] = "0"

            elif int(pre_bullet) - 1 == int(cur_bullet) and pre_bullet != cur_bullet:
                self._use_bullet.append(self._frame)

        self._damage.append(damage)
        if len(self._damage) > 1:
            pre_damage = self._damage[self._frame - 1]
            cur_damage = self._damage[self._frame]
            if pre_damage < cur_damage:
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
        # print(self._bullet)
        a = len(self._use_bullet)
        b = len(self._hit)
        if a == 0:
            return [], [], 0.0
        else:
            return self._use_bullet, self._hit, b / a
        # return a, b, b / a
