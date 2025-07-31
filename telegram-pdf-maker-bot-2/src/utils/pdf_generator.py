from PIL import Image
from typing import List
from ..handlers.image_processing import ImageProcessor

class PDFGenerator:
    def __init__(self):
        self.image_processor = ImageProcessor()
    
    def generate_pdf(
        self,
        image_paths: List[str],
        output_path: str,
        style: str = "original",
        quality: str = "high"
    ) -> str:
        processed_images = []
        
        for path in image_paths:
            img = self.image_processor.process_image_style(path, style)
            processed_images.append(img)
        
        processed_images[0].save(
            output_path,
            "PDF",
            save_all=True,
            append_images=processed_images[1:],
            quality=85 if quality == "high" else 65 if quality == "medium" else 45
        )
        
        return output_path