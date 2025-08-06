import base64
import io

import fitz
from PIL import Image
from typing import List, Dict, Any

from classes.settings import Settings


class MessageManager:
    
    @staticmethod
    def process_uploaded_files(uploaded_files:list, settings:Settings) -> List[Dict[str, Any]]:
        """Handles uploaded files and returns structured infos"""

        files_info = []
        
        if not uploaded_files:
            return files_info
            
        for file in uploaded_files:
            if file.type.startswith('image/'):
                files_info.append(MessageManager._process_image(file, settings))
            elif file.type == 'application/pdf':
                # _process_pdf returns a list of images processed from the PDF
                pdf_images = MessageManager._process_pdf(file, settings)
                files_info.extend(pdf_images)
                
        return files_info
    
    @staticmethod
    def _resize_image(image, settings:Settings):
        """Resizes an image if needed"""

        image_max_size = settings.params["image_max_size"]

        if max(image.size) > image_max_size:
            image.thumbnail((image_max_size, image_max_size), Image.Resampling.LANCZOS)
        return image
    
    @staticmethod
    def _encode_image(image):
        """Converts a PIL image in base64"""

        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG', optimize=True)
        return base64.b64encode(img_buffer.getvalue()).decode()
    
    @staticmethod
    def _process_image(file, settings:Settings) -> Dict[str, Any]:
        """Resizes and encodes an image"""

        image = Image.open(file)
        image = MessageManager._resize_image(image, settings)
        encoded_image = MessageManager._encode_image(image)
        
        return {
            "type": "image",
            "name": file.name,
            "data": encoded_image
        }
    
    @staticmethod
    def _process_pdf(file, settings:Settings) -> List[Dict[str, Any]]:
        """Converts a PDF file in images using PyMuPDF"""

        dpi = settings.params["dpi"]

        pdf_bytes = file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        pdf_images = []
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            # Convert to image with 150 DPI
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))
            image = MessageManager._resize_image(image, settings)
            img_base64 = MessageManager._encode_image(image)
            
            pdf_images.append({
                "type": "image",
                "name": f"{file.name} - Page {page_num+1}",
                "data": img_base64
            })
        
        pdf_document.close()
        return pdf_images
    
    @staticmethod
    def create_agent_message(prompt: str, files_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Creates a structured message for the agent, with text and images"""

        # Checks if the message contains images
        has_images = any(f["type"] == "image" for f in files_info)
        
        if not has_images:
            return {"input": prompt}
        
        # Structured format for images
        content = [{"type": "text", "text": prompt}]
        
        # Add all images
        for file_info in files_info:
            if file_info["type"] == "image":
                print(f"file info data: {file_info['name']}")
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{file_info['data']}"
                    }
                })
        
        return {"input": content}
    
    @staticmethod
    def get_files_summary(files_info: List[Dict[str, Any]]) -> str:
        """Returns a list of joined files"""
        
        if not files_info:
            return ""
        return f"Joined files: {', '.join([f['name'] for f in files_info])}"