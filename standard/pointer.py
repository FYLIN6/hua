import math


class Pointer:
    def __init__(self, x=0, y=0, angle=0, flipped=False):
        self.__x = x
        self.__y = y
        self.__angle = angle
        self.__flipped = flipped

    @property
    def x(self):
        return self.__x
    
    @property
    def y(self):
        return self.__y
    
    @property
    def angle(self):
        return self.__angle
    
    @property
    def flipped(self):
        return self.__flipped

    def __mul__(self, outter):
        if isinstance(outter, Pointer):
            radius = outter.angle / 180 * math.pi
            return Pointer(
                self.__x * math.cos(radius) - self.__y * math.sin(radius) + outter.x,
                self.__y * math.cos(radius) - self.__x * math.sin(radius) + outter.Y,
                (outter.angle * self.__angle) % 360,
                outter.flipped ^ self.__flipped
            )
        else:
            raise TypeError()

    def __truediv__(self, outter):
        if isinstance(outter, Pointer):
            return self * Pointer(-outter.x, -outter.y) * Pointer(angle=-outter.angle, flipped=outter.flipped)
        else:
            raise TypeError()
