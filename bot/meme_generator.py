"""
Meme Generator
Creates memes using PIL with various templates and text overlay
"""

import logging
import os
import tempfile
from typing import Optional, List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
import io
import random

logger = logging.getLogger(__name__)

class MemeGenerator:
    """Meme generation handler"""
    
    def __init__(self, config):
        self.config = config
        self.temp_dir = tempfile.gettempdir()
        
        # Default meme dimensions
        self.default_width = 800
        self.default_height = 600
        
        # Text styling
        self.font_size = 48
        self.stroke_width = 3
        self.text_color = (255, 255, 255)  # White
        self.stroke_color = (0, 0, 0)     # Black
        
        # Load meme templates
        self.templates = self.load_meme_templates()
        
        logger.info("🎨 Meme generator initialized")
    
    def load_meme_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load meme templates configuration"""
        # Since we can't use image files, we'll use colored backgrounds with different layouts
        templates = {
            'classic': {
                'name': 'Classic Meme',
                'width': 800,
                'height': 600,
                'background_color': (255, 255, 255),
                'text_areas': [
                    {'position': 'top', 'y_offset': 50},
                    {'position': 'bottom', 'y_offset': 50}
                ]
            },
            'drake': {
                'name': 'Drake Pointing',
                'width': 600,
                'height': 600,
                'background_color': (240, 240, 240),
                'text_areas': [
                    {'position': 'right_top', 'x_offset': 300, 'y_offset': 150},
                    {'position': 'right_bottom', 'x_offset': 300, 'y_offset': 450}
                ]
            },
            'distracted': {
                'name': 'Distracted Boyfriend',
                'width': 800,
                'height': 500,
                'background_color': (135, 206, 235),  # Sky blue
                'text_areas': [
                    {'position': 'left', 'x_offset': 100, 'y_offset': 50},
                    {'position': 'center', 'x_offset': 400, 'y_offset': 50},
                    {'position': 'right', 'x_offset': 650, 'y_offset': 50}
                ]
            },
            'expanding_brain': {
                'name': 'Expanding Brain',
                'width': 600,
                'height': 800,
                'background_color': (255, 248, 220),  # Cornsilk
                'text_areas': [
                    {'position': 'quarter_1', 'x_offset': 300, 'y_offset': 100},
                    {'position': 'quarter_2', 'x_offset': 300, 'y_offset': 300},
                    {'position': 'quarter_3', 'x_offset': 300, 'y_offset': 500},
                    {'position': 'quarter_4', 'x_offset': 300, 'y_offset': 700}
                ]
            },
            'simple': {
                'name': 'Simple Text',
                'width': 800,
                'height': 400,
                'background_color': (64, 64, 64),  # Dark gray
                'text_areas': [
                    {'position': 'center', 'x_offset': 400, 'y_offset': 200}
                ]
            }
        }
        
        return templates
    
    async def create_meme(self, top_text: str = "", bottom_text: str = "", template: str = "classic") -> Optional[str]:
        """Create a meme with specified text"""
        try:
            # Select template
            if template not in self.templates:
                template = "classic"
            
            template_config = self.templates[template]
            
            logger.info(f"🎨 Creating meme with template: {template}")
            
            # Create base image
            image = self.create_base_image(template_config)
            
            # Add text based on template
            if template == "classic":
                if top_text:
                    image = self.add_text_to_image(image, top_text, 'top', template_config)
                if bottom_text:
                    image = self.add_text_to_image(image, bottom_text, 'bottom', template_config)
            elif template == "drake":
                if top_text:
                    image = self.add_text_to_image(image, top_text, 'right_top', template_config)
                if bottom_text:
                    image = self.add_text_to_image(image, bottom_text, 'right_bottom', template_config)
            elif template == "simple":
                text = top_text or bottom_text
                if text:
                    image = self.add_text_to_image(image, text, 'center', template_config)
            
            # Add visual elements to make it look more like a meme
            image = self.add_meme_styling(image, template_config)
            
            # Save meme
            meme_path = await self.save_meme(image, template)
            
            if meme_path:
                logger.info(f"✅ Meme created successfully: {meme_path}")
                return meme_path
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Meme creation error: {e}")
            return None
    
    def create_base_image(self, template_config: Dict[str, Any]) -> Image.Image:
        """Create base image for meme"""
        width = template_config['width']
        height = template_config['height']
        bg_color = template_config['background_color']
        
        # Create image with background color
        image = Image.new('RGB', (width, height), bg_color)
        
        return image
    
    def add_text_to_image(self, image: Image.Image, text: str, position: str, template_config: Dict[str, Any]) -> Image.Image:
        """Add text to image at specified position"""
        try:
            draw = ImageDraw.Draw(image)
            
            # Try to load a font, fallback to default if not available
            try:
                # Try to use a built-in font
                font = ImageFont.load_default()
                # Scale up the default font
                font_size = self.font_size
            except Exception:
                font = ImageFont.load_default()
                font_size = 40  # Fallback size
            
            # Calculate text position
            text_x, text_y = self.calculate_text_position(image, text, position, template_config, font)
            
            # Wrap text if needed
            wrapped_text = self.wrap_text(text, font, image.width - 40)  # 40px margin
            
            # Draw text with outline for better readability
            for line_num, line in enumerate(wrapped_text):
                line_y = text_y + (line_num * font_size * 1.2)
                
                # Draw text outline (stroke)
                for adj_x in range(-self.stroke_width, self.stroke_width + 1):
                    for adj_y in range(-self.stroke_width, self.stroke_width + 1):
                        draw.text((text_x + adj_x, line_y + adj_y), line, font=font, fill=self.stroke_color)
                
                # Draw main text
                draw.text((text_x, line_y), line, font=font, fill=self.text_color)
            
            return image
            
        except Exception as e:
            logger.error(f"❌ Text addition error: {e}")
            return image
    
    def calculate_text_position(self, image: Image.Image, text: str, position: str, template_config: Dict[str, Any], font) -> Tuple[int, int]:
        """Calculate text position based on template"""
        width, height = image.size
        
        # Get text dimensions
        text_bbox = font.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Calculate position based on template
        if position == 'top':
            x = (width - text_width) // 2
            y = 50
        elif position == 'bottom':
            x = (width - text_width) // 2
            y = height - text_height - 50
        elif position == 'center':
            x = (width - text_width) // 2
            y = (height - text_height) // 2
        elif position == 'right_top':
            x = width // 2 + 50
            y = height // 4
        elif position == 'right_bottom':
            x = width // 2 + 50
            y = 3 * height // 4
        else:
            # Default to center
            x = (width - text_width) // 2
            y = (height - text_height) // 2
        
        return max(0, x), max(0, y)
    
    def wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Wrap text to fit within specified width"""
        try:
            words = text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                text_bbox = font.getbbox(test_line)
                test_width = text_bbox[2] - text_bbox[0]
                
                if test_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        # Word is too long, add it anyway
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return lines
            
        except Exception as e:
            logger.error(f"❌ Text wrapping error: {e}")
            return [text]  # Return original text as single line
    
    def add_meme_styling(self, image: Image.Image, template_config: Dict[str, Any]) -> Image.Image:
        """Add styling elements to make it look more meme-like"""
        try:
            draw = ImageDraw.Draw(image)
            width, height = image.size
            
            # Add subtle border
            border_color = (128, 128, 128)
            border_width = 3
            
            # Top border
            draw.rectangle([0, 0, width, border_width], fill=border_color)
            # Bottom border
            draw.rectangle([0, height - border_width, width, height], fill=border_color)
            # Left border
            draw.rectangle([0, 0, border_width, height], fill=border_color)
            # Right border
            draw.rectangle([width - border_width, 0, width, height], fill=border_color)
            
            # Add some visual elements based on template
            template_name = template_config.get('name', '').lower()
            
            if 'drake' in template_name:
                # Add simple shapes to represent Drake meme structure
                # Left panels (darker)
                draw.rectangle([0, 0, width//2, height//2], fill=(200, 200, 200))
                draw.rectangle([0, height//2, width//2, height], fill=(180, 180, 180))
                
                # Divider line
                draw.line([width//2, 0, width//2, height], fill=(100, 100, 100), width=5)
                draw.line([0, height//2, width, height//2], fill=(100, 100, 100), width=5)
            
            elif 'expanding' in template_name:
                # Add brain-like sections
                section_height = height // 4
                for i in range(4):
                    y = i * section_height
                    brightness = 255 - (i * 30)  # Get brighter with each section
                    section_color = (brightness, brightness, brightness)
                    draw.rectangle([0, y, width//2, y + section_height], fill=section_color)
                    
                    # Divider lines
                    if i < 3:
                        draw.line([0, y + section_height, width, y + section_height], fill=(100, 100, 100), width=3)
            
            return image
            
        except Exception as e:
            logger.error(f"❌ Meme styling error: {e}")
            return image
    
    async def save_meme(self, image: Image.Image, template: str) -> Optional[str]:
        """Save meme to temporary file"""
        try:
            # Generate unique filename
            timestamp = int(os.urandom(4).hex(), 16)
            filename = f"meme_{template}_{timestamp}.png"
            filepath = os.path.join(self.temp_dir, filename)
            
            # Save image
            image.save(filepath, 'PNG')
            
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Meme save error: {e}")
            return None
    
    async def create_random_meme(self, text: str) -> Optional[str]:
        """Create meme with random template"""
        try:
            # Select random template
            template = random.choice(list(self.templates.keys()))
            
            # Split text for top/bottom if it contains separator
            if '|' in text:
                parts = text.split('|', 1)
                top_text = parts[0].strip()
                bottom_text = parts[1].strip()
            else:
                # For single text, use it as top text for most templates
                if template in ['simple', 'center']:
                    top_text = text
                    bottom_text = ""
                else:
                    top_text = text
                    bottom_text = ""
            
            return await self.create_meme(top_text, bottom_text, template)
            
        except Exception as e:
            logger.error(f"❌ Random meme creation error: {e}")
            return None
    
    def get_available_templates(self) -> List[str]:
        """Get list of available meme templates"""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific template"""
        return self.templates.get(template_name)
    
    async def create_text_meme(self, text: str, style: str = "classic") -> Optional[str]:
        """Create simple text-based meme"""
        try:
            styles = {
                'classic': {'bg': (255, 255, 255), 'text': (0, 0, 0)},
                'dark': {'bg': (0, 0, 0), 'text': (255, 255, 255)},
                'blue': {'bg': (0, 100, 200), 'text': (255, 255, 255)},
                'red': {'bg': (200, 0, 0), 'text': (255, 255, 255)},
                'green': {'bg': (0, 150, 0), 'text': (255, 255, 255)}
            }
            
            style_config = styles.get(style, styles['classic'])
            
            # Create simple text meme
            width, height = 800, 400
            image = Image.new('RGB', (width, height), style_config['bg'])
            draw = ImageDraw.Draw(image)
            
            # Use default font
            font = ImageFont.load_default()
            
            # Wrap and center text
            wrapped_lines = self.wrap_text(text, font, width - 40)
            
            # Calculate starting Y position to center all lines
            line_height = 40
            total_text_height = len(wrapped_lines) * line_height
            start_y = (height - total_text_height) // 2
            
            # Draw each line
            for i, line in enumerate(wrapped_lines):
                # Center each line horizontally
                text_bbox = font.getbbox(line)
                text_width = text_bbox[2] - text_bbox[0]
                x = (width - text_width) // 2
                y = start_y + (i * line_height)
                
                # Add text with outline
                for adj in [-2, -1, 0, 1, 2]:
                    for adj_y in [-2, -1, 0, 1, 2]:
                        if adj != 0 or adj_y != 0:
                            draw.text((x + adj, y + adj_y), line, font=font, fill=(0, 0, 0))
                
                draw.text((x, y), line, font=font, fill=style_config['text'])
            
            # Save meme
            return await self.save_meme(image, f"text_{style}")
            
        except Exception as e:
            logger.error(f"❌ Text meme creation error: {e}")
            return None
    
    async def cleanup_old_memes(self, max_age_hours: int = 24):
        """Clean up old meme files"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.temp_dir):
                if filename.startswith('meme_') and filename.endswith('.png'):
                    filepath = os.path.join(self.temp_dir, filename)
                    file_age = current_time - os.path.getctime(filepath)
                    
                    if file_age > max_age_seconds:
                        try:
                            os.remove(filepath)
                            logger.info(f"🧹 Cleaned up old meme: {filename}")
                        except OSError:
                            pass  # File might be in use
                            
        except Exception as e:
            logger.error(f"❌ Meme cleanup error: {e}")
