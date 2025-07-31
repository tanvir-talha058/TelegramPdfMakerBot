from PIL import Image, ImageEnhance
import cv2

class ImageProcessor:
    @staticmethod
    def process_image_style(image_path: str, style: str) -> Image.Image:
        img = Image.open(image_path).convert("RGB")
        
        if style == "grayscale":
            return img.convert("L").convert("RGB")
        elif style == "black_white":
            img_cv = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            _, thresh = cv2.threshold(img_cv, 150, 255, cv2.THRESH_BINARY)
            return Image.fromarray(thresh).convert("RGB")
        elif style == "enhanced":
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            enhancer = ImageEnhance.Brightness(img)
            return enhancer.enhance(1.2)
        
        return img  # original style