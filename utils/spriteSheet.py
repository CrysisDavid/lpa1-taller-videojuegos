import pygame
import xml.etree.ElementTree as ET

class SpriteSheet:
    def __init__(self, image_path, xml_path):
        try:
            self.sheet = pygame.image.load(image_path).convert_alpha()
        except pygame.error as e:
            print(f"Error loading image {image_path}: {e}")
            self.sheet = None
        except FileNotFoundError as e:
            print(f"Image file not found: {image_path}: {e}")
            self.sheet = None

        self.frames = {}

        if self.sheet is not None:
            self._parse_xml(xml_path)

    def _parse_xml(self, xml_path):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Error parsing XML file {xml_path}: {e}")
            return
        except FileNotFoundError as e:
            print(f"XML file not found: {xml_path}: {e}")
            return

        for subtexture in root.findall("SubTexture"):
            name = subtexture.get("name")
            if name is None:
                print(f"Warning: SubTexture without name in {xml_path}")
                continue

            try:
                x = int(subtexture.get("x", 0))
                y = int(subtexture.get("y", 0))
                w = int(subtexture.get("width", 0))
                h = int(subtexture.get("height", 0))
            except ValueError as e:
                print(f"Error parsing attributes for frame '{name}' in {xml_path}: {e}")
                continue

            if w <= 0 or h <= 0:
                print(f"Warning: Invalid dimensions for frame '{name}': w={w}, h={h}")
                continue

            rect = pygame.Rect(x, y, w, h)
            image = pygame.Surface((w, h), pygame.SRCALPHA)
            image.blit(self.sheet, (0, 0), rect)

            self.frames[name] = image

    def get(self, name):
        return self.frames.get(name)

    def get_all(self):
        return self.frames