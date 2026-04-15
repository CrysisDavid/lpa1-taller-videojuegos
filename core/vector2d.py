from typing import Union


class Vector2D:
    """A simple 2D vector class for vector operations.
    
    Attributes:
        x (float): The x component of the vector.
        y (float): The y component of the vector.
    """
    
    def __init__(self, x: float, y: float):
        """Initialize a vector with x and y.
        Parameters:
            x (float): The x component of the vector.
            y (float): The y component of the vector.
        """
        self.x = x
        self.y = y

    def __add__(self, other:'Vector2D') -> 'Vector2D':
        """Add two vectors together.
        Args:
            other (Vector2D): The vector to add.
        Returns:
            Vector2D: The result of the addition.
        Raises:
            TypeError: If the other object is not a Vector2D instance.
        """
        if not isinstance(other, Vector2D):
            raise TypeError("Operand must be an instance of Vector2D")
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other:'Vector2D') -> 'Vector2D':
        """Subtract one vector from another.
        Args:
            other (Vector2D): The vector to subtract.
        Returns:
            Vector2D: The result of the subtraction."""
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: Union[int,float]) -> 'Vector2D':
        """Multiply a vector by a scalar.
        Args:
            scalar: (float): The scalar to multiply by.
        Returns:
            Vector2D: The result of the multiplication.
        Raises:
            TypeError: If the scalar is not a number.
        """
        if not isinstance(scalar, (int, float)):
            raise TypeError("Operand must be a number")
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __rmatmul__(self, scalar: Union[int,float]) -> 'Vector2D':
        """Right-hand multiplication of a vector by a scalar.
        Args:
            scalar (float): The scalar to multiply by.
        """
        return self.__mul__( scalar)
        

    def __truediv__(self, scalar: Union[int,float]) -> 'Vector2D':
        """Divide a vector by a scalar.
        Args:
            scalar (float): The scalar to divide by.
        Returns:
            Vector2D: The result of the division."""
        return Vector2D(self.x / scalar, self.y / scalar)
    
    def __neg__(self, scalar: Union[int, float]) -> 'Vector2D':
        """Negate a vector.
        Args:
            scalar (float): The scalar to negate by.
        Returns:
            Vector2D: The result of the negation."""
        pass #TODO: implement this method

    def __repr__(self):
        return f"Vector2D({self.x}, {self.y})"
    
    def magnitude(self) -> float:
        """Calculate the magnitude of the vector.
        Returns:
            float: The magnitude of the vector.
        """
        return (self.x ** 2 + self.y ** 2) ** 0.5
    
    def normalize(self) -> 'Vector2D':
        """Normalize the vector to have a magnitude of 1.
        Returns:
            Vector2D: The normalized vector.
        Raises:
            ValueError: If the vector has a magnitude of 0.
        """
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize a zero vector")
        return self / mag
    
    def dot(self, other:'Vector2D') -> float:
        """Calculate the dot product of two vectors.
        Args:
            other (Vector2D): The other vector to calculate the dot product with.
        Returns:
            float: The dot product of the two vectors.
        Raises:
            TypeError: If the other object is not a Vector2D instance.
        """
        if not isinstance(other, Vector2D):
            raise TypeError("Operand must be an instance of Vector2D")
        return self.x * other.x + self.y * other.y
    
    def distance_to(self, other:'Vector2D') -> float:
        """Calculate the distance between two vectors.
        Args:
            other (Vector2D): The other vector to calculate the distance to.
        Returns:
            float: The distance between the two vectors.
        Raises:
            TypeError: If the other object is not a Vector2D instance.
        """
        if not isinstance(other, Vector2D):
            raise TypeError("Operand must be an instance of Vector2D")
        return (self - other).magnitude()
    
    def lerp(self, other:'Vector2D', t: float) -> 'Vector2D':
        """Linearly interpolate between two vectors.
        Args:
            other (Vector2D): The other vector to interpolate with.
            t (float): The interpolation factor (0.0 to 1.0).
        Returns:
            Vector2D: The result of the interpolation.
        Raises:
            TypeError: If the other object is not a Vector2D instance or if t is not a number.
            ValueError: If t is not between 0.0 and 1.0.
        """
        if not isinstance(other, Vector2D):
            raise TypeError("Operand must be an instance of Vector2D")
        if not isinstance(t, (int, float)):
            raise TypeError("Interpolation factor must be a number")
        if not (0.0 <= t <= 1.0):
            raise ValueError("Interpolation factor must be between 0.0 and 1.0")
        return self * (1 - t) + other * t
    
    def to_tuple(self) -> tuple:
        """Convert the vector to a tuple.
        Returns:
            tuple: A tuple containing the x and y components of the vector.
        """
        return (self.x, self.y)
    
    def from_tuple(cls, tup: tuple) -> 'Vector2D':
        """Create a Vector2D from a tuple.
        Args:
            tup (tuple): A tuple containing the x and y components of the vector.
        Returns:
            Vector2D: A new Vector2D instance created from the tuple.
        Raises:
            TypeError: If the input is not a tuple or if it does not contain exactly two elements.
        """
        if not isinstance(tup, tuple):
            raise TypeError("Input must be a tuple")
        if len(tup) != 2:
            raise TypeError("Tuple must contain exactly two elements")
        return cls(tup[0], tup[1])