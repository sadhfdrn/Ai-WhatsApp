"""
Meme Templates Configuration
Defines various meme templates with layouts and positioning
"""

import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class MemeTemplates:
    """Meme template definitions and utilities"""
    
    def __init__(self):
        self.templates = self._load_templates()
        logger.info(f"🎨 Loaded {len(self.templates)} meme templates")
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load all meme template configurations"""
        return {
            # Classic top/bottom text meme
            'classic': {
                'name': 'Classic Meme',
                'description': 'Traditional top and bottom text format',
                'width': 800,
                'height': 600,
                'background_color': (255, 255, 255),
                'text_areas': [
                    {
                        'id': 'top',
                        'position': 'top',
                        'x': 400,  # Center X
                        'y': 80,   # Top margin
                        'max_width': 760,
                        'alignment': 'center',
                        'font_size': 48,
                        'font_weight': 'bold',
                        'text_color': (255, 255, 255),
                        'stroke_color': (0, 0, 0),
                        'stroke_width': 3
                    },
                    {
                        'id': 'bottom',
                        'position': 'bottom',
                        'x': 400,  # Center X
                        'y': 520,  # Bottom margin
                        'max_width': 760,
                        'alignment': 'center',
                        'font_size': 48,
                        'font_weight': 'bold',
                        'text_color': (255, 255, 255),
                        'stroke_color': (0, 0, 0),
                        'stroke_width': 3
                    }
                ],
                'usage': 'Perfect for traditional memes. Format: "Top text|Bottom text"'
            },
            
            # Drake pointing meme style
            'drake': {
                'name': 'Drake Pointing',
                'description': 'Two-panel format with pointing gesture implied',
                'width': 600,
                'height': 600,
                'background_color': (240, 240, 240),
                'panels': [
                    {'x': 0, 'y': 0, 'width': 300, 'height': 300, 'color': (220, 220, 220)},
                    {'x': 0, 'y': 300, 'width': 300, 'height': 300, 'color': (200, 200, 200)}
                ],
                'text_areas': [
                    {
                        'id': 'reject',
                        'position': 'right_top',
                        'x': 450,  # Right panel center
                        'y': 150,  # Top panel center
                        'max_width': 280,
                        'alignment': 'center',
                        'font_size': 32,
                        'text_color': (0, 0, 0),
                        'stroke_color': (255, 255, 255),
                        'stroke_width': 2
                    },
                    {
                        'id': 'accept',
                        'position': 'right_bottom',
                        'x': 450,  # Right panel center
                        'y': 450,  # Bottom panel center
                        'max_width': 280,
                        'alignment': 'center',
                        'font_size': 32,
                        'text_color': (0, 0, 0),
                        'stroke_color': (255, 255, 255),
                        'stroke_width': 2
                    }
                ],
                'usage': 'Two choices format. First text = reject, Second text = accept'
            },
            
            # Distracted boyfriend style
            'distracted': {
                'name': 'Distracted Boyfriend',
                'description': 'Three-character meme template',
                'width': 800,
                'height': 500,
                'background_color': (135, 206, 235),  # Sky blue
                'text_areas': [
                    {
                        'id': 'girlfriend',
                        'position': 'left',
                        'x': 120,
                        'y': 100,
                        'max_width': 150,
                        'alignment': 'center',
                        'font_size': 24,
                        'text_color': (255, 255, 255),
                        'stroke_color': (0, 0, 0),
                        'stroke_width': 2
                    },
                    {
                        'id': 'boyfriend',
                        'position': 'center',
                        'x': 400,
                        'y': 100,
                        'max_width': 150,
                        'alignment': 'center',
                        'font_size': 24,
                        'text_color': (255, 255, 255),
                        'stroke_color': (0, 0, 0),
                        'stroke_width': 2
                    },
                    {
                        'id': 'other_girl',
                        'position': 'right',
                        'x': 680,
                        'y': 100,
                        'max_width': 150,
                        'alignment': 'center',
                        'font_size': 24,
                        'text_color': (255, 255, 255),
                        'stroke_color': (0, 0, 0),
                        'stroke_width': 2
                    }
                ],
                'usage': 'Three-part story. Format: "Girlfriend|Boyfriend|Other Girl"'
            },
            
            # Expanding brain meme
            'expanding_brain': {
                'name': 'Expanding Brain',
                'description': 'Four levels of enlightenment',
                'width': 600,
                'height': 800,
                'background_color': (255, 248, 220),  # Cornsilk
                'panels': [
                    {'x': 0, 'y': 0, 'width': 300, 'height': 200, 'color': (200, 200, 200)},
                    {'x': 0, 'y': 200, 'width': 300, 'height': 200, 'color': (220, 220, 220)},
                    {'x': 0, 'y': 400, 'width': 300, 'height': 200, 'color': (240, 240, 240)},
                    {'x': 0, 'y': 600, 'width': 300, 'height': 200, 'color': (255, 255, 255)}
                ],
                'text_areas': [
                    {
                        'id': 'level1',
                        'position': 'right_quarter_1',
                        'x': 450,
                        'y': 100,
                        'max_width': 280,
                        'alignment': 'center',
                        'font_size': 20,
                        'text_color': (0, 0, 0),
                        'stroke_width': 1
                    },
                    {
                        'id': 'level2',
                        'position': 'right_quarter_2',
                        'x': 450,
                        'y': 300,
                        'max_width': 280,
                        'alignment': 'center',
                        'font_size': 22,
                        'text_color': (0, 0, 0),
                        'stroke_width': 1
                    },
                    {
                        'id': 'level3',
                        'position': 'right_quarter_3',
                        'x': 450,
                        'y': 500,
                        'max_width': 280,
                        'alignment': 'center',
                        'font_size': 24,
                        'text_color': (0, 0, 0),
                        'stroke_width': 1
                    },
                    {
                        'id': 'level4',
                        'position': 'right_quarter_4',
                        'x': 450,
                        'y': 700,
                        'max_width': 280,
                        'alignment': 'center',
                        'font_size': 26,
                        'text_color': (0, 0, 0),
                        'stroke_width': 1
                    }
                ],
                'usage': 'Four levels of intelligence. Separate with "|" for each level'
            },
            
            # Simple text meme
            'simple': {
                'name': 'Simple Text',
                'description': 'Clean text on colored background',
                'width': 800,
                'height': 400,
                'background_color': (64, 64, 64),  # Dark gray
                'text_areas': [
                    {
                        'id': 'main',
                        'position': 'center',
                        'x': 400,
                        'y': 200,
                        'max_width': 760,
                        'alignment': 'center',
                        'font_size': 42,
                        'text_color': (255, 255, 255),
                        'stroke_color': (0, 0, 0),
                        'stroke_width': 2
                    }
                ],
                'usage': 'Simple centered text for quotes or statements'
            },
            
            # Two buttons meme
            'two_buttons': {
                'name': 'Two Buttons',
                'description': 'Difficult choice between two options',
                'width': 600,
                'height': 400,
                'background_color': (200, 200, 255),
                'panels': [
                    {'x': 50, 'y': 150, 'width': 200, 'height': 80, 'color': (255, 0, 0)},
                    {'x': 350, 'y': 150, 'width': 200, 'height': 80, 'color': (0, 0, 255)}
                ],
                'text_areas': [
                    {
                        'id': 'button1',
                        'position': 'left_button',
                        'x': 150,
                        'y': 190,
                        'max_width': 180,
                        'alignment': 'center',
                        'font_size': 18,
                        'text_color': (255, 255, 255),
                        'stroke_width': 1
                    },
                    {
                        'id': 'button2',
                        'position': 'right_button',
                        'x': 450,
                        'y': 190,
                        'max_width': 180,
                        'alignment': 'center',
                        'font_size': 18,
                        'text_color': (255, 255, 255),
                        'stroke_width': 1
                    }
                ],
                'usage': 'Two difficult choices. Format: "Option 1|Option 2"'
            },
            
            # Blank template for custom layouts
            'blank': {
                'name': 'Blank Canvas',
                'description': 'Blank template for custom text placement',
                'width': 800,
                'height': 600,
                'background_color': (255, 255, 255),
                'text_areas': [
                    {
                        'id': 'custom',
                        'position': 'center',
                        'x': 400,
                        'y': 300,
                        'max_width': 760,
                        'alignment': 'center',
                        'font_size': 36,
                        'text_color': (0, 0, 0),
                        'stroke_color': (255, 255, 255),
                        'stroke_width': 2
                    }
                ],
                'usage': 'Blank canvas for any text'
            },
            
            # Quote format
            'quote': {
                'name': 'Quote Format',
                'description': 'Formatted quote with attribution',
                'width': 600,
                'height': 400,
                'background_color': (248, 248, 248),
                'text_areas': [
                    {
                        'id': 'quote',
                        'position': 'center_top',
                        'x': 300,
                        'y': 150,
                        'max_width': 550,
                        'alignment': 'center',
                        'font_size': 28,
                        'text_color': (50, 50, 50),
                        'stroke_width': 0,
                        'style': 'italic'
                    },
                    {
                        'id': 'author',
                        'position': 'center_bottom',
                        'x': 300,
                        'y': 300,
                        'max_width': 400,
                        'alignment': 'center',
                        'font_size': 20,
                        'text_color': (100, 100, 100),
                        'stroke_width': 0,
                        'style': 'bold'
                    }
                ],
                'usage': 'Quote format. Format: "Quote text|Author name"'
            }
        }
    
    def get_template(self, name: str) -> Dict[str, Any]:
        """Get template configuration by name"""
        return self.templates.get(name.lower(), self.templates['classic'])
    
    def get_template_names(self) -> List[str]:
        """Get list of available template names"""
        return list(self.templates.keys())
    
    def get_template_info(self, name: str) -> str:
        """Get template usage information"""
        template = self.get_template(name)
        return template.get('usage', 'Standard meme template')
    
    def get_random_template(self) -> str:
        """Get random template name"""
        import random
        return random.choice(self.get_template_names())
    
    def search_templates(self, keyword: str) -> List[str]:
        """Search templates by keyword"""
        keyword = keyword.lower()
        matching = []
        
        for name, config in self.templates.items():
            if (keyword in name.lower() or 
                keyword in config.get('description', '').lower() or
                keyword in config.get('usage', '').lower()):
                matching.append(name)
        
        return matching
    
    def get_template_preview(self, name: str) -> Dict[str, Any]:
        """Get template preview information"""
        template = self.get_template(name)
        
        return {
            'name': template.get('name', name.title()),
            'description': template.get('description', ''),
            'dimensions': f"{template.get('width', 800)}x{template.get('height', 600)}",
            'text_areas': len(template.get('text_areas', [])),
            'usage': template.get('usage', ''),
            'background': template.get('background_color', (255, 255, 255))
        }
    
    def validate_template(self, name: str) -> Tuple[bool, str]:
        """Validate template configuration"""
        if name not in self.templates:
            return False, f"Template '{name}' not found"
        
        template = self.templates[name]
        
        # Check required fields
        required_fields = ['width', 'height', 'background_color', 'text_areas']
        for field in required_fields:
            if field not in template:
                return False, f"Template '{name}' missing required field: {field}"
        
        # Validate text areas
        text_areas = template.get('text_areas', [])
        if not text_areas:
            return False, f"Template '{name}' has no text areas defined"
        
        for i, area in enumerate(text_areas):
            required_area_fields = ['id', 'x', 'y', 'max_width', 'font_size']
            for field in required_area_fields:
                if field not in area:
                    return False, f"Text area {i} in template '{name}' missing field: {field}"
        
        return True, "Template is valid"
    
    def get_color_variations(self, base_template: str) -> Dict[str, Dict[str, Any]]:
        """Get color variations of a template"""
        if base_template not in self.templates:
            return {}
        
        base = self.templates[base_template].copy()
        variations = {}
        
        color_schemes = {
            'dark': {'bg': (32, 32, 32), 'text': (255, 255, 255), 'stroke': (0, 0, 0)},
            'blue': {'bg': (30, 60, 120), 'text': (255, 255, 255), 'stroke': (0, 0, 0)},
            'green': {'bg': (40, 100, 40), 'text': (255, 255, 255), 'stroke': (0, 0, 0)},
            'red': {'bg': (120, 30, 30), 'text': (255, 255, 255), 'stroke': (0, 0, 0)},
            'purple': {'bg': (80, 30, 120), 'text': (255, 255, 255), 'stroke': (0, 0, 0)}
        }
        
        for scheme_name, colors in color_schemes.items():
            variation = base.copy()
            variation['name'] = f"{base['name']} ({scheme_name.title()})"
            variation['background_color'] = colors['bg']
            
            # Update text areas with new colors
            new_text_areas = []
            for area in variation['text_areas']:
                new_area = area.copy()
                new_area['text_color'] = colors['text']
                if 'stroke_color' in new_area:
                    new_area['stroke_color'] = colors['stroke']
                new_text_areas.append(new_area)
            
            variation['text_areas'] = new_text_areas
            variations[f"{base_template}_{scheme_name}"] = variation
        
        return variations
    
    def create_custom_template(self, name: str, width: int, height: int, 
                             background_color: Tuple[int, int, int],
                             text_areas: List[Dict[str, Any]]) -> bool:
        """Create a custom template"""
        try:
            custom_template = {
                'name': name,
                'description': 'Custom user-created template',
                'width': width,
                'height': height,
                'background_color': background_color,
                'text_areas': text_areas,
                'usage': 'Custom template created by user'
            }
            
            # Validate the custom template
            valid, message = self.validate_template_data(custom_template)
            if not valid:
                logger.error(f"❌ Custom template validation failed: {message}")
                return False
            
            # Add to templates
            template_key = f"custom_{name.lower().replace(' ', '_')}"
            self.templates[template_key] = custom_template
            
            logger.info(f"✅ Custom template '{name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating custom template: {e}")
            return False
    
    def validate_template_data(self, template_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate template data structure"""
        try:
            # Check dimensions
            width = template_data.get('width', 0)
            height = template_data.get('height', 0)
            
            if width <= 0 or height <= 0:
                return False, "Invalid dimensions"
            
            if width > 2000 or height > 2000:
                return False, "Dimensions too large (max 2000x2000)"
            
            # Check background color
            bg_color = template_data.get('background_color')
            if not isinstance(bg_color, (list, tuple)) or len(bg_color) != 3:
                return False, "Invalid background color format"
            
            # Check text areas
            text_areas = template_data.get('text_areas', [])
            if not text_areas:
                return False, "No text areas defined"
            
            for area in text_areas:
                if not isinstance(area.get('x'), int) or not isinstance(area.get('y'), int):
                    return False, "Invalid text area coordinates"
                
                if area.get('x', 0) > width or area.get('y', 0) > height:
                    return False, "Text area coordinates outside template bounds"
            
            return True, "Valid template data"
            
        except Exception as e:
            return False, f"Validation error: {e}"
