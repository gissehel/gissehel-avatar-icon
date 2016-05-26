import yaml

directions = {
    '6':(1,0),
    '8':(0,-1),
    '2':(0,1),
    '4':(-1,0),
    '0':0,
    '1':1,
    }
action_types = {
    'r':'rotation',
    'm':'move',
    'p':'path',
    'z':'loop',
    }

class Action(object):
    def __init__(self, direction, action_type):
        self._direction = direction
        self._action_type = action_type
        self._len = 1
    def v(self):
        return (self._direction[0]*self._len, self._direction[1]*self._len)
    def __str__(self):
        return "{} : {} {}".format(self._action_type, self._direction, self._len)

class Form(object):
    def __init__(self):
        self._move = (0,0)
        self._path = []
        self._is_empty = True
        self._rotation = 0
        
    def add_action(self, action):
        if action._action_type == 'rotation':
            self._rotation = action._direction
        if action._action_type == 'move':
            x,y = self._move
            x += action._direction[0]*action._len
            y += action._direction[1]*action._len
            self._move = (x,y)
            self._is_empty = False
        elif action._action_type == 'path':
            self._path.append(action)
            self._is_empty = False
    def __str__(self):
        return "r{}m{}p".format(self._rotation,self._move)+''.join(str(action.v()) for action in self._path)
        
class PathMaker(object):
    def __init__(self):
        pass

    def read_path(self, data):
        current_action_type = None
        current_direction = None
        last_action = None
        for c in data:
            if c in action_types:
                current_action_type = action_types[c]
                current_direction = None
                if last_action is not None:
                    yield last_action
                    last_action = None
                if current_action_type == 'rotation':
                    yield Action(current_direction, current_action_type)
                if current_action_type == 'loop':
                    yield Action(current_direction, current_action_type)
            elif c in directions:
                current_direction = directions[c]
                if last_action is not None and last_action._action_type in ('move','path'):
                    if last_action._direction == current_direction:
                        last_action._len += 1
                    else:
                        yield last_action
                        last_action = Action(current_direction, current_action_type)
                else:
                    last_action = Action(current_direction, current_action_type)
            
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
                
    def make_path(self, data):
        width=100
        round=25
        result = ""
        for form in self.make_forms(data):
            result += "M {},{} ".format(form._move[0]*width + form._path[0]._direction[0]*round,form._move[1]*width + form._path[0]._direction[1]*round)
            path = form._path + [ form._path[0] ]
            for action_index in xrange(len(form._path)):
                action = path[action_index]
                next_action = path[action_index+1]
                x,y = action.v()
                xd,yd = action._direction
                x1,y1 = next_action.v()
                x1d,y1d = next_action._direction
                result += "l {},{} ".format(x*width-2*xd*round,y*width-2*yd*round)
                rotation = form._rotation * (x*y1-x1*y)
                if rotation>0:
                    rotation = 1
                else:
                    rotation = 0
                result += "a {0},{0} 0 0,{3} {1},{2} ".format(round, (xd+x1d)*round, (yd+y1d)*round, rotation)
            result += "z "
        return result

class AvaterGenerator(object):
    def __init__(self):
        pass

    def get_colors(self, color):
        rgbs = map(lambda x:int(x,16),(color[1:3],color[3:5],color[5:7]))
        dark_rgbs = map(lambda x:x/2,rgbs)
        color, dark_color = ('#'+''.join(map(lambda x:"%02x"%x,color_items)) for color_items in (rgbs, dark_rgbs))
        return list('#'+''.join(map(lambda x:"%02x"%x,color_items)) for color_items in (rgbs, dark_rgbs))
        
    def generate(self, name, color, data):
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
<rect width="584" height="584" rx="25" ry="25" x="8" y="8" stroke-width="8" stroke="#333333" fill="url(#back)">
</rect>
<use xlink:href="#form" fill="{color_dark}" x="50" y="35" />
<use xlink:href="#form" fill="#ffffff" x="50" y="65" />
<use xlink:href="#form" fill="{color}" x="50" y="50" />
</svg>'''
        avatar = pattern.format( color=color, color_dark=color_dark, path=PathMaker().make_path(data), source=data )
        with open("{name}.svg".format(name=name), 'wb') as handle:
            handle.write(avatar)
    
def main():
    ag = AvaterGenerator()
    # print ag.generate('test1','#76d26d',"r1p6248z r1m662p626262424448486868z r0m666222p4268z r1m6666p6248z")
    # print ag.generate('test2','#6492cc',"r1p222662442668626684486688842248424884z")
    # print ag.generate('test3','#d595e6',"r1m6p6248z r1m666p6248z r1m6222p6662624844424868z")
    print ag.generate('git-avatar','#4d61d9',"r1m6662p626244266244842448668448686862z")
    
main()