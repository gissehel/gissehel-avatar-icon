import yaml
import math

directions = {
    '6': (1, 0),
    '8': (0, -1),
    '2': (0, 1),
    '4': (-1, 0),
    '0': 0,
    '1': 1,
}
action_types = {
    'r': 'rotation',
    'm': 'move',
    'p': 'path',
    'z': 'loop',
}


class Action(object):
    def __init__(self, direction, action_type, x, y):
        self._direction = direction
        self._action_type = action_type
        self._x = x
        self._y = y

    def x(self):
        return self._x

    def y(self):
        return self._y

    def xy(self):
        return (self._x, self._y)

    def string_point(self):
        return "[{}|{}]".format(self.xy(), self._direction)

    def __str__(self):
        return "{} : {} ({})".format(self._action_type, self._direction, self.xy())


class Form(object):
    def __init__(self):
        self._move = (0, 0)
        self._path = []
        self._is_empty = True
        self._rotation = 0

    def add_action(self, action):
        if action._action_type == 'rotation':
            self._rotation = action._direction
        if action._action_type == 'move':
            x = action.x()
            y = action.y()
            self._move = (x, y)
            self._is_empty = False
        elif action._action_type == 'path':
            self._path.append(action)
            self._is_empty = False

    def __str__(self):
        return "r{}m{}p".format(self._rotation, self._move)+''.join(str(action.string_point()) for action in self._path)


class PathMaker(object):
    def __init__(self, spherical=False, bezier=False):
        self._spherical = spherical
        self._bezier = bezier

    def read_path(self, data):
        current_action_type = None
        current_direction = None
        last_action = None
        current_x = 0
        current_y = 0
        for c in data:
            if c in action_types:
                current_action_type = action_types[c]
                current_direction = None
                if last_action is not None:
                    yield last_action
                    last_action = None
                if current_action_type in ('move', 'rotation'):
                    current_x = 0
                    current_y = 0
                if current_action_type == 'loop':
                    yield Action(current_direction, current_action_type, current_x, current_y)
                    last_action = None
            elif c in directions:
                current_direction = directions[c]
                if current_action_type in ('move', 'path'):
                    current_x += current_direction[0]
                    current_y += current_direction[1]
                if last_action is not None and last_action._action_type in ('move', 'path') and (last_action._direction != current_direction):
                    yield last_action
                    last_action = None
                last_action = Action(
                    current_direction, current_action_type, current_x, current_y)
        if last_action is not None:
            yield last_action
            last_action = None

    def make_forms(self, data):
        form = Form()
        for action in self.read_path(data):
            if action._action_type == 'loop':
                if not(form._is_empty):
                    yield form
                form = Form()
            else:
                form.add_action(action)
        if not(form._is_empty):
            yield form

    def get_anamorphic_xy_trans(self, x_min, x_max, y_min, y_max, X_min, X_max, Y_min, Y_max, proxy):
        L0 = max(X_max-X_min, Y_max-Y_min)
        l0 = max(x_max-x_min, x_max-x_min)
        x_c = (x_min+x_max)/2
        y_c = (y_min+y_max)/2
        X_c = (X_min+X_max)/2
        Y_c = (Y_min+Y_max)/2
        d = l0/proxy

        def trans(coord):
            x, y = coord
            x_l = x-x_c
            y_l = y-y_c
            l_l = math.sqrt(x_l*x_l+y_l*y_l)
            if l_l == 0:
                X_l = 0
                Y_l = 0
            else:
                L_l = L0*(math.sin(math.atan(l_l/d)/2))
                X_l = x_l * L_l/l_l
                Y_l = y_l * L_l/l_l
            return (X_c + X_l, Y_c + Y_l)
        return trans

    def make_path(self, data):
        width = 100
        round = 25
        Width = 5*100
        result = ""
        for form in self.make_forms(data):
            # print form
            x_init = form._move[0]*width + form._path[0]._direction[0]*round
            y_init = form._move[1]*width + form._path[0]._direction[1]*round
            if self._bezier and self._spherical:
                trans = self.get_anamorphic_xy_trans(0, Width, 0, Width, 0, Width, 0, Width, 3)
                # def trans(coord): return coord
            else:
                def trans(coord): return coord
            (X_init, Y_init) = trans((x_init, y_init))
            (current_x, current_y) = (x_init, y_init)
            result += "M {},{} ".format(X_init, Y_init)
            path = form._path + [form._path[0]]
            for action_index in xrange(len(form._path)):
                if self._bezier:
                    if self._spherical:
                        action = path[action_index]
                        next_action = path[action_index+1]
                        x, y = action.xy()
                        xd, yd = action._direction
                        x1, y1 = next_action.xy()
                        x1d, y1d = next_action._direction
                        (x_bezier0, y_bezier0) = (x*width-xd*round, y*width-yd*round)
                        n = 25
                        for index in xrange(n):
                            x_l = current_x + (index+1)*((x_bezier0-current_x)/n)
                            y_l = current_y + (index+1)*((y_bezier0-current_y)/n)
                            (X, Y) = trans((x_l, y_l))
                            result += "L {},{} ".format(X, Y)

                        (x_bezier1, y_bezier1) = (x*width-xd*round+xd*round*0.5523, y*width-yd*round+yd*round*0.5523)
                        (x_bezier2, y_bezier2) = (x*width+x1d*round-x1d*round*0.5523, y*width+y1d*round-y1d*round*0.5523)
                        (x_bezier3, y_bezier3) = (x*width+x1d*round, y*width+y1d*round)
                        X_bezier1, Y_bezier1 = trans((x_bezier1, y_bezier1))
                        X_bezier2, Y_bezier2 = trans((x_bezier2, y_bezier2))
                        X_bezier3, Y_bezier3 = trans((x_bezier3, y_bezier3))
                        result += "C {},{} {},{} {},{} ".format(
                            X_bezier1, Y_bezier1, X_bezier2, Y_bezier2, X_bezier3, Y_bezier3)
                        # result += "L {},{} ".format(X_bezier3, Y_bezier3)
                        (current_x, current_y) = (x_bezier3, y_bezier3)
                    else:
                        action = path[action_index]
                        next_action = path[action_index+1]
                        x, y = action.xy()
                        xd, yd = action._direction
                        x1, y1 = next_action.xy()
                        x1d, y1d = next_action._direction
                        (x_bezier0, y_bezier0) = (x*width-xd*round, y*width-yd*round)
                        (x_bezier1, y_bezier1) = (x*width-xd*round+xd*round*0.5523, y*width-yd*round+yd*round*0.5523)
                        (x_bezier2, y_bezier2) = (x*width+x1d*round-x1d*round*0.5523, y*width+y1d*round-y1d*round*0.5523)
                        (x_bezier3, y_bezier3) = (x*width+x1d*round, y*width+y1d*round)
                        result += "L {},{} ".format(x_bezier0, y_bezier0)
                        result += "C {},{} {},{} {},{} ".format(
                            x_bezier1, y_bezier1, x_bezier2, y_bezier2, x_bezier3, y_bezier3)
                        # result += "L {},{} ".format(x_bezier3, y_bezier3)
                else:
                    action = path[action_index]
                    next_action = path[action_index+1]
                    x, y = action.xy()
                    xd, yd = action._direction
                    x1, y1 = next_action.xy()
                    x1d, y1d = next_action._direction
                    result += "L {},{} ".format(x *
                                                width-xd*round, y*width-yd*round)
                    rotation = form._rotation * (xd*y1d-x1d*yd)
                    if rotation > 0:
                        rotation = 1
                    else:
                        rotation = 0
                    # result += "L {},{} ".format(x*width+x1d*round,y*width+y1d*round)
                    result += "A {0},{0} 0 0,{3} {1},{2} ".format(
                        round, x*width+x1d*round, y*width+y1d*round, rotation)
            result += "z "
        return result


class AvaterGenerator(object):
    def __init__(self):
        pass

    def get_colors(self, color):
        rgbs = map(lambda x: int(x, 16), (color[1:3], color[3:5], color[5:7]))
        dark_rgbs = map(lambda x: x/2, rgbs)
        color, dark_color = ('#'+''.join(map(lambda x: "%02x" % x, color_items))
                             for color_items in (rgbs, dark_rgbs))
        return list('#'+''.join(map(lambda x: "%02x" % x, color_items)) for color_items in (rgbs, dark_rgbs))

    def generate(self, name, color, data, spherical=False, bezier=False):
        color, color_dark = self.get_colors(color)

        pattern = '''<?xml version="1.0" encoding="utf-8"?>
<svg 
    xmlns="http://www.w3.org/2000/svg" 
    xmlns:xlink="http://www.w3.org/1999/xlink"
    version="1.1"
    width="600" 
    height="600"
>
<title>Avatar</title>
<g>
<defs>
<linearGradient gradientUnits="userSpaceOnUse" x1="300" x2="300" y1="600" y2="0" id="back">
<stop offset="0%" stop-color="#e0e0e0"/>
<stop offset="100%" stop-color="#f0f0f0"/>
</linearGradient>
<g id="form">
<!--
based on sequence [{source}]
-->
<path 
    d="{path}" />
</g>
</defs>
</g>
<{back_pattern} x="8" y="8" stroke-width="8" stroke="#333333" fill="url(#back)" />
<use xlink:href="#form" fill="{color_dark}" x="50" y="35" />
<use xlink:href="#form" fill="#ffffff" x="50" y="65" />
<use xlink:href="#form" fill="{color}" x="50" y="50" />
</svg>'''
        avatar = pattern.format(
            color=color,
            color_dark=color_dark,
            back_pattern='circle cx="300" cy="300" r="292"' if spherical else 'rect width="584" height="584" rx="25" ry="25"',
            path=PathMaker(spherical, bezier).make_path(data), source=data)
        with open("{name}.svg".format(name=name), 'wb') as handle:
            handle.write(avatar)

    def generate_all(self, name, color, data):
        self.generate(name + '-rect', color, data, spherical=False, bezier=True)
        self.generate(name + '-circle', color, data, spherical=True, bezier=True)
    
def main():
    ag = AvaterGenerator()
    print ag.generate_all('test1', '#76d26d', "r1p6248z r1m662p626262424448486868z r0m666222p4268z r1m6666p6248z")
    print ag.generate_all('test2','#6492cc',"r1p222662442668626684486688842248424884z")
    print ag.generate_all('test3','#d595e6',"r1m6p6248z r1m666p6248z r1m6222p6662624844424868z")
    print ag.generate_all('git-avatar','#4d61d9',"r1m6662p626244266244842448668448686862z")
    print ag.generate_all('championship','#da1682',"r1p62686268622424266244444866848488z")


main()
