import discord
from discord.ext import commands, tasks
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import json
import random
import os
import logging
import asyncio
from io import BytesIO
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from . import config

class BrainrotDrop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('brainrot_drop')
        os.makedirs('data', exist_ok=True)  

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.font_directory = os.path.join(current_dir, 'fonts')
            
            if not os.path.exists(self.font_directory):
                self.logger.warning(f"Fonts directory not found at {self.font_directory}")
                raise FileNotFoundError("Fonts directory not found")
                
            self.title_font_path = os.path.join(self.font_directory, 'Roboto-Bold.ttf')
            self.subtitle_font_path = os.path.join(self.font_directory, 'Roboto-Regular.ttf')
            self.description_font_path = os.path.join(self.font_directory, 'Roboto-Light.ttf')
            
            for font_path in [self.title_font_path, self.subtitle_font_path, self.description_font_path]:
                if not os.path.exists(font_path):
                    self.logger.warning(f"Font file not found: {font_path}")
                    raise FileNotFoundError(f"Font file not found: {font_path}")
            
            self.title_font_size = 40
            self.subtitle_font_size = 30
            self.description_font_size = 24
            self.hidden_card_font_size = 120
            
            self.title_font = config.load_font('bold', self.title_font_size)
            self.subtitle_font = config.load_font('regular', self.subtitle_font_size)
            self.description_font = config.load_font('light', self.description_font_size)
            self.hidden_card_font = config.load_font('bold', self.hidden_card_font_size)
            
            self.title_font_type = 'bold'
            self.subtitle_font_type = 'regular'
            self.description_font_type = 'light'
            
            self.logger.info("Fonts loaded successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to load custom fonts: {e}. Using default.")
            self.title_font = ImageFont.load_default()
            self.subtitle_font = ImageFont.load_default()
            self.description_font = ImageFont.load_default()
            self.hidden_card_font = ImageFont.load_default()
        
        self.number_emojis = ['1️⃣', '2️⃣', '3️⃣']
        self.drop_timeout = 30
        self.claim_cooldown = 600
        self.load_data()
        self.admin_users = self.load_admin_users()
        self.logger.info("BrainrotDrop cog initialized")
        self.drop_cooldowns = {}
        self.cleanup_cooldowns.start()

        self._cache = {}
        self._cache_timeout = 300

        self.default_image = None
        self.load_default_image()

        self.output_dir = 'output'
        os.makedirs(self.output_dir, exist_ok=True)

        self.claim_queue = asyncio.Queue()
        self.processing_claims = False
        self.claim_tasks = {}  # Store claim tasks by message ID

    @tasks.loop(minutes=5)
    async def cleanup_cooldowns(self):
        current_time = datetime.now()
        self.drop_cooldowns = {
            k: v for k, v in self.drop_cooldowns.items() 
            if (current_time - v).total_seconds() < 3600
        }

    def load_data(self):
        """Load both character and user data"""
        try:
            with open('data/characters.json', 'r', encoding='utf-8') as f:
                self.characters = json.load(f)['characters']
                self.logger.info(f"Loaded {len(self.characters)} characters")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading character data: {e}")
            self.characters = []

        try:
            with open('data/users.json', 'r', encoding='utf-8') as f:
                self.user_data = json.load(f)["users"]
                for user_id in self.user_data:
                    if "claimed_characters" in self.user_data[user_id] and isinstance(self.user_data[user_id]["claimed_characters"], list):
                        old_claims = self.user_data[user_id]["claimed_characters"]
                        new_claims = {}
                        for claim in old_claims:
                            char_id = str(claim["id"])
                            if char_id in new_claims:
                                new_claims[char_id] += 1
                            else:
                                new_claims[char_id] = 1
                        self.user_data[user_id]["claimed_characters"] = new_claims
                self.logger.info("User data loaded successfully")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading user data: {e}")
            self.user_data = {}
            self.save_user_data()

    def save_user_data(self):
        """Save user data to JSON file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/users.json', 'w', encoding='utf-8') as f:
                json.dump({"users": self.user_data}, f, indent=2)
            self.logger.info("User data saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving user data: {e}")

    def load_user_data(self):
        """Load user data from JSON file"""
        try:
            with open('data/users.json', 'r', encoding='utf-8') as f:
                return json.load(f)["users"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading user data: {e}")
            return {}

    def can_user_claim(self, user_id):
        """Check if user is allowed to claim based on cooldown"""
        user_id = str(user_id)
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "last_claim": None,
                "claimed_characters": {}
            }
            return True, None

        last_claim = self.user_data[user_id].get("last_claim")
        if not last_claim:
            return True, None

        try:
            last_claim_time = datetime.fromisoformat(last_claim)
            remaining_time = timedelta(seconds=self.claim_cooldown) - (datetime.now() - last_claim_time)
            can_claim = remaining_time.total_seconds() <= 0
            return can_claim, remaining_time if not can_claim else None
        except Exception as e:
            self.logger.error(f"Error checking claim cooldown for user {user_id}: {e}")
            return False, None

    def update_user_claim(self, user_id: int, character: dict) -> int:
        """Update user's claim timestamp and collection"""
        user_id = str(user_id)
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "last_claim": None,
                "claimed_characters": {}
            }

        self.user_data[user_id]["last_claim"] = datetime.now().isoformat()
        
        char_id = str(character["id"])
        if "claimed_characters" not in self.user_data[user_id]:
            self.user_data[user_id]["claimed_characters"] = {}
            
        if char_id in self.user_data[user_id]["claimed_characters"]:
            self.user_data[user_id]["claimed_characters"][char_id] += 1
        else:
            self.user_data[user_id]["claimed_characters"][char_id] = 1

        self.save_user_data()
        return self.user_data[user_id]["claimed_characters"][char_id]

    def create_card_frame(self, size, character_type):
        frame = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)
        
        colors = {
            'normal': ((192, 192, 192, 255), (128, 128, 128, 255)),
            'legendary': ((255, 215, 0, 255), (218, 165, 32, 255)),
            'loser': ((255, 0, 0, 255), (139, 0, 0, 255))
        }
        
        main_color, accent_color = colors.get(character_type, colors['normal'])
        
        border_width = 3 if size[0] <= 200 else 5
        draw.rectangle(
            [border_width//2, border_width//2, size[0]-1-border_width//2, size[1]-1-border_width//2],
            outline=main_color,
            width=border_width
        )
        
        glow = Image.new('RGBA', size, (0, 0, 0, 0))
        draw_glow = ImageDraw.Draw(glow)
        glow_border_width = 6 if size[0] <= 200 else 10
        draw_glow.rectangle(
            [glow_border_width//2, glow_border_width//2, size[0]-1-glow_border_width//2, size[1]-1-glow_border_width//2],
            outline=main_color,
            width=glow_border_width
        )
        glow = glow.filter(ImageFilter.GaussianBlur(radius=4 if size[0] <= 200 else 8))
        frame = Image.alpha_composite(glow, frame)
        
        return frame

    def load_default_image(self):
        """Load or create default placeholder image."""
        try:
            img_size = (400, 300)
            self.default_image = Image.new('RGBA', img_size, (40, 40, 40, 255))
            draw = ImageDraw.Draw(self.default_image)
            
            border = 20
            draw.rectangle(
                [border, border, img_size[0]-border, img_size[1]-border],
                outline=(200, 200, 200, 255),
                width=2
            )
            
            text = "No Image"
            bbox = draw.textbbox((0, 0), text, font=self.title_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (img_size[0] - text_width) // 2
            y = (img_size[1] - text_height) // 2
            
            draw.text(
                (x, y),
                text,
                font=self.title_font,
                fill=(200, 200, 200, 255)
            )
            
            self.default_image = self.apply_rounded_corners(self.default_image, radius=15)
            
        except Exception as e:
            self.logger.error(f"Failed to create default image: {e}")
            self.default_image = None

    async def generate_card(self, character, card_width=800, card_height=400):
        """Generate a character card and save to output directory."""
        try:
            if not character or not isinstance(character, dict):
                self.logger.error(f"Invalid character data: {character}")
                return None

            required_fields = ['id', 'name', 'type', 'image_url']
            if not all(field in character for field in required_fields):
                self.logger.error(f"Missing required fields in character data: {character}")
                return None

            self.logger.info(f"Attempting to generate card for character: {character['id']} - {character['name']}")
            self.logger.info(f"Image URL: {character['image_url']}")

            try:
                char_image = await self.load_character_image(character['image_url'])
                self.logger.info(f"Image loaded successfully for character {character['id']}")
            except Exception as e:
                self.logger.error(f"Failed to load image for character {character['id']}: {str(e)}", exc_info=True)
                return None

            try:
                card = Image.new('RGBA', (card_width, card_height), (0, 0, 0, 0))
                bg = self.create_subtle_gradient_background(card_width, card_height, character['type'])
                card.paste(bg, (0, 0), bg)

                padding = 30
                image_area = (padding, padding, card_width // 2 - padding, card_height - padding)
                
                char_width = image_area[2] - image_area[0]
                char_height = image_area[3] - image_area[1]
                
                char_image = char_image.convert('RGBA')
                char_image = ImageOps.fit(char_image, (char_width, char_height), Image.Resampling.LANCZOS)
                
                char_mask = Image.new('L', char_image.size, 255)
                
                card.paste(char_image, (image_area[0], image_area[1]), char_mask)

                draw = ImageDraw.Draw(card)
                text_area = (card_width // 2 + padding, padding, card_width - padding, card_height - padding)
                self.draw_modern_text(draw, text_area, character)

                card = self.apply_rounded_corners(card, 20)

                card = self.apply_gradient_border(card, 5, character['type'])
                
                if card:
                    output_path = os.path.join(self.output_dir, f'card_{character["id"]}.png')
                    try:
                        card.save(output_path, 'PNG')
                        self.logger.info(f"Card saved successfully to {output_path}")
                        return output_path
                    except Exception as e:
                        self.logger.error(f"Failed to save card to {output_path}: {str(e)}", exc_info=True)
                        return None
                else:
                    self.logger.error(f"Card generation failed for character {character['id']}")
                    return None
                
            except Exception as e:
                self.logger.error(f"Error during card generation for character {character['id']}: {str(e)}", exc_info=True)
                return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error generating card for {character.get('id', 'unknown')}: {str(e)}", exc_info=True)
            return None

    def get_background_color(self, character_type):
        """Return the base background color for gradient based on character type."""
        colors = {
            'normal': (54, 57, 63, 255),
            'legendary': (255, 215, 0, 255),
            'loser': (178, 34, 34, 255)
        }
        return colors.get(character_type, (54, 57, 63, 255))

    def get_gradient_colors(self, character_type):
        """Return top and bottom colors for gradient based on character type."""
        gradients = {
            'normal': ((114, 137, 218), (78, 93, 148)),
            'legendary': ((255, 223, 0), (218, 165, 32)),
            'loser': ((220, 20, 60), (178, 34, 34))
        }
        return gradients.get(character_type, ((54, 57, 63), (32, 34, 37)))

    def get_text_color(self, character_type):
        """Return text color based on character type."""
        colors = {
            'normal': (255, 255, 255),
            'legendary': (0, 0, 0),
            'loser': (255, 255, 255)
        }
        return colors.get(character_type, (255, 255, 255))

    def create_subtle_gradient_background(self, width, height, character_type):
        """Create a dark gradient background for all cards."""
        top_color = (45, 49, 66, 255)
        bottom_color = (28, 31, 42, 255)
        
        base = Image.new('RGBA', (width, height), top_color)
        gradient = Image.new('RGBA', (width, height), bottom_color)
        mask = Image.new('L', (width, height))
        
        for y in range(height):
            value = int(255 * (1.5 * y / height))
            value = min(255, max(0, value))
            for x in range(width):
                mask.putpixel((x, y), value)
        
        return Image.composite(gradient, base, mask)

    def get_subtle_gradient_colors(self, character_type):
        """Return lighter gradient colors based on character type."""
        gradients = {
            'normal': ((230, 240, 255), (200, 210, 230)),
            'legendary': ((255, 250, 205), (255, 239, 213)),
            'loser': ((255, 228, 225), (255, 182, 193))
        }
        return gradients.get(character_type, ((230, 240, 255), (200, 210, 230)))

    def apply_rounded_corners(self, image, radius):
        """Apply rounded corners to an image."""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), image.size], radius=radius, fill=255)
        
        output = Image.new('RGBA', image.size, (0, 0, 0, 0))
        output.paste(image, mask=mask)
        
        return output

    def draw_modern_text(self, draw, text_area, character):
        """Enhanced text drawing with better styling."""
        x1, y1, x2, y2 = text_area
        max_width = x2 - x1

        base_colors = {
            'title': (255, 255, 255, 255),
            'description': (220, 220, 220, 255),
        }
        
        type_colors = {
            'normal': {
                'bg': (114, 137, 218, 255),
                'text': (255, 255, 255, 255),
                'id': (180, 180, 180, 255)
            },
            'legendary': {
                'bg': (255, 215, 0, 255),
                'text': (0, 0, 0, 255),
                'id': (255, 215, 0, 255)
            },
            'loser': {
                'bg': (220, 20, 60, 255),
                'text': (255, 255, 255, 255),
                'id': (220, 20, 60, 255)
            }
        }
        
        color_scheme = type_colors.get(character['type'], type_colors['normal'])

        title_text = character['name']
        id_text = f"#{character['id']}"
        type_text = character['type'].capitalize()
        description = character.get('description', '')

        title_font = self.adjust_font_size(self.title_font_type, 48, title_text, max_width * 0.9)
        type_font = config.load_font(self.subtitle_font_type, 28)
        desc_font = self.adjust_description_font(description, max_width, y2 - y1)
        id_font = config.load_font(self.subtitle_font_type, 24)

        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_height = title_bbox[3] - title_bbox[1]
        
        type_bbox = draw.textbbox((0, 0), type_text, font=type_font)
        type_height = type_bbox[3] - type_bbox[1]
        
        wrapped_text = self.wrap_text(description, desc_font, max_width)
        desc_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=desc_font)
        desc_height = desc_bbox[3] - desc_bbox[1]

        total_height = title_height + type_height + desc_height + 60
        start_y = y1 + (y2 - y1 - total_height) // 2

        current_y = start_y
        shadow_offset = 2
        draw.text((x1+shadow_offset, current_y+shadow_offset), title_text, 
                  font=title_font, fill=(0, 0, 0, 80))
        draw.text((x1, current_y), title_text, 
                  font=title_font, fill=base_colors['title'])

        current_y += title_height + 25
        badge_padding = 12
        type_bbox = draw.textbbox((0, 0), type_text, font=type_font)
        badge_width = type_bbox[2] - type_bbox[0] + badge_padding * 3
        badge_height = type_bbox[3] - type_bbox[1] + badge_padding * 2

        badge_bg = Image.new('RGBA', (int(badge_width), int(badge_height)), color_scheme['bg'])
        
        badge_mask = Image.new('L', (int(badge_width), int(badge_height)), 0)
        badge_draw = ImageDraw.Draw(badge_mask)
        badge_draw.rounded_rectangle([(0, 0), (badge_width-1, badge_height-1)], 
                                   radius=badge_height//3, fill=255)

        badge_x = x1
        badge_y = current_y
        
        badge_bg.putalpha(badge_mask)
        draw._image.paste(badge_bg, (int(badge_x), int(badge_y)), badge_bg)

        type_x = badge_x + badge_padding
        type_y = badge_y + (badge_height - type_bbox[3] + type_bbox[1]) // 2
        draw.text((type_x, type_y), type_text, 
                  font=type_font, fill=color_scheme['text'])

        current_y += badge_height + 25
        draw.multiline_text((x1, current_y), wrapped_text, 
                           font=desc_font, fill=base_colors['description'],
                           spacing=6)

        id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
        id_width = id_bbox[2] - id_bbox[0]
        id_height = id_bbox[3] - id_bbox[1]
        id_x = x2 - id_width - 10
        id_y = y2 - id_height - 10
        
        draw.text((id_x+1, id_y+1), id_text, 
                  font=id_font, fill=(0, 0, 0, 80))
        draw.text((id_x, id_y), id_text, 
                  font=id_font, fill=color_scheme['id'])

    def apply_gradient_border(self, image, border_width, character_type):
        """Apply an enhanced gradient border with inner glow."""
        try:
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
                
            width, height = image.size
            new_width = width + 2 * border_width
            new_height = height + 2 * border_width

            colors = {
                'normal': ((114, 137, 218, 255), (78, 93, 148, 255)),
                'legendary': ((255, 215, 0, 255), (218, 165, 32, 255)),
                'loser': ((220, 20, 60, 255), (139, 0, 0, 255))
            }
            
            gradient_top, gradient_bottom = colors.get(character_type, colors['normal'])
            
            inner_glow = Image.new('RGBA', image.size, (0, 0, 0, 0))
            inner_draw = ImageDraw.Draw(inner_glow)
            glow_color = gradient_top[:3] + (100,)
            padding = 20
            inner_draw.rounded_rectangle(
                [padding, padding, width-padding, height-padding],
                radius=20,
                outline=glow_color,
                width=5
            )
            inner_glow = inner_glow.filter(ImageFilter.GaussianBlur(10))
            
            image = Image.alpha_composite(image, inner_glow)
            
            border_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(border_image)
            
            for y in range(new_height):
                ratio = y / new_height
                r = int(gradient_top[0] * (1 - ratio) + gradient_bottom[0] * ratio)
                g = int(gradient_top[1] * (1 - ratio) + gradient_bottom[1] * ratio)
                b = int(gradient_top[2] * (1 - ratio) + gradient_bottom[2] * ratio)
                draw.line([(0, y), (new_width, y)], fill=(r, g, b, 255))
                
            border_mask = Image.new('L', (new_width, new_height), 0)
            mask_draw = ImageDraw.Draw(border_mask)
            mask_draw.rounded_rectangle([0, 0, new_width-1, new_height-1], radius=25, fill=255)
            mask_draw.rounded_rectangle([border_width, border_width, 
                                       new_width-border_width-1, new_height-border_width-1], 
                                      radius=20, fill=0)
            
            border_image.putalpha(border_mask)
            
            final = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
            final = Image.alpha_composite(final, border_image)
            final.paste(image, (border_width, border_width), image)
            
            return final
            
        except Exception as e:
            self.logger.error(f"Error applying gradient border: {e}")
            return image

    def get_border_gradient_colors(self, character_type):
        """Return gradient colors for the border based on character type."""
        gradients = {
            'normal': ((180, 200, 230, 255), (160, 180, 210, 255)),
            'legendary': ((255, 248, 220, 255), (238, 232, 170, 255)),
            'loser': ((255, 192, 203, 255), (255, 160, 170, 255))
        }
        return gradients.get(character_type, ((180, 200, 230, 255), (160, 180, 210, 255)))

    def create_empty_image(self, size=(400, 300)):
        """Create a simple empty image with text."""
        img = Image.new('RGBA', size, (40, 40, 40, 255))
        draw = ImageDraw.Draw(img)
        
        border = 10
        draw.rectangle(
            [border, border, size[0]-border, size[1]-border],
            outline=(100, 100, 100, 255),
            width=2
        )
        
        text = "No Image Available"
        bbox = draw.textbbox((0, 0), text, font=self.title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        draw.text(
            (x+2, y+2),
            text,
            font=self.title_font,
            fill=(0, 0, 0, 128)
        )
        draw.text(
            (x, y),
            text,
            font=self.title_font,
            fill=(200, 200, 200, 255)
        )
        
        return img

    async def load_character_image(self, image_url):
        """Load character image from URL or return empty image if loading fails."""
        try:
            if not image_url or not isinstance(image_url, str):
                self.logger.warning(f"Empty or invalid image URL: {image_url}")
                return self.create_empty_image()

            image_url = image_url.strip()
            self.logger.info(f"Attempting to load image from URL: {image_url}")
            
            if 'placeholder' in image_url.lower():
                self.logger.info("Using empty image for placeholder")
                return self.create_empty_image()

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(image_url, timeout=10) as resp:
                        self.logger.info(f"Image request status: {resp.status}")
                        if resp.status == 200:
                            image_data = await resp.read()
                            try:
                                with BytesIO(image_data) as bio:
                                    image = Image.open(bio)
                                    self.logger.info(f"Image loaded successfully. Mode: {image.mode}, Size: {image.size}")
                                    return image.convert('RGBA')
                            except Exception as e:
                                self.logger.error(f"Failed to process image data: {str(e)}", exc_info=True)
                                return self.create_empty_image()
                        else:
                            self.logger.warning(f"Failed to fetch image (status {resp.status}): {image_url}")
                            return self.create_empty_image()
                except Exception as e:
                    self.logger.error(f"Network error loading image: {str(e)}", exc_info=True)
                    return self.create_empty_image()
        except Exception as e:
            self.logger.error(f"Unexpected error loading image: {str(e)}", exc_info=True)
            return self.create_empty_image()

    def adjust_font_size(self, font_type, initial_size, text, max_width):
        """Adjust font size to fit text within max_width using textbbox."""
        font_size = initial_size
        while font_size > 10:
            font = config.load_font(font_type, font_size)
            temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                break
            font_size -= 1
        return config.load_font(font_type, font_size)

    def adjust_description_font(self, text, max_width, max_height):
        """Adjust font size for description to fit within max_height."""
        font_size = self.description_font_size
        while font_size > 10:
            font = config.load_font(self.description_font_type, font_size)
            wrapped_text = self.wrap_text(text, font, max_width)
            
            temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            bbox = temp_draw.multiline_textbbox((0, 0), wrapped_text, font=font)
            text_height = bbox[3] - bbox[1]
            
            if text_height <= max_height:
                break
            font_size -= 1
        return config.load_font(self.description_font_type, font_size)

    def wrap_text(self, text, font, max_width):
        """Wrap text to fit within max_width using textbbox."""
        words = text.split()
        lines = []
        current_line = ''

        temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))

        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)

        return '\n'.join(lines)

    def create_hidden_card(self, size):
        """Create a hidden card that looks like a playing card back."""
        card_width, card_height = size
        
        card = Image.new('RGBA', size, (0, 0, 0, 255))
        draw = ImageDraw.Draw(card)
        
        border_width = 20
        draw.rectangle(
            [border_width, border_width, card_width - border_width, card_height - border_width],
            outline=(255, 255, 255, 255),
            width=3
        )
        
        draw.line(
            [(border_width, border_width), (card_width - border_width, card_height - border_width)],
            fill=(255, 255, 255, 255),
            width=3
        )
        draw.line(
            [(card_width - border_width, border_width), (border_width, card_height - border_width)],
            fill=(255, 255, 255, 255),
            width=3
        )
        
        card = self.apply_rounded_corners(card, radius=20)
        
        return card

    def create_radial_gradient(self, size, center_color, edge_color):
        """Create a radial gradient using numpy for better performance."""
        width, height = size
        gradient_array = []
        center_x, center_y = width / 2, height / 2
        max_distance = ((width/2)**2 + (height/2)**2)**0.5

        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        pixels = gradient.load()

        for y in range(height):
            for x in range(width):
                distance = ((x - center_x)**2 + (y - center_y)**2)**0.5
                ratio = min(distance / max_distance, 1.0)
                
                r = int(center_color[0] * (1 - ratio) + edge_color[0] * ratio)
                g = int(center_color[1] * (1 - ratio) + edge_color[1] * ratio)
                b = int(center_color[2] * (1 - ratio) + edge_color[2] * ratio)
                a = int(center_color[3] * (1 - ratio) + edge_color[3] * ratio)
                
                pixels[x, y] = (r, g, b, a)

        return gradient

    async def generate_hidden_card_image(self, card_width=800, card_height=400):
        """Generate a hidden card image for the drop."""
        size = (card_width, card_height)
        hidden_card = self.create_hidden_card(size)
        return hidden_card

    async def generate_drop_image(self, characters):
        """Generate and save drop image to output directory."""
        card_width, card_height = 350, 600
        spacing = 20
        total_width = (card_width * len(characters)) + (spacing * (len(characters) - 1))
        
        base_image = Image.new('RGBA', (total_width, card_height), (0, 0, 0, 0))
        
        for index, character in enumerate(characters):
            hidden_card = await self.generate_hidden_card_image(card_width, card_height)
            base_image.paste(hidden_card, (index * (card_width + spacing), 0), hidden_card)
        
        output_path = os.path.join(self.output_dir, 'drop.png')
        base_image.save(output_path, 'PNG')
        
        self.logger.info("Drop image saved successfully")
        return output_path

    def load_aura_points(self):
        """Load aura points data"""
        try:
            if not os.path.exists('aura_points.json'):
                return {}
            with open('aura_points.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading aura points: {e}")
            return {}

    def save_aura_points(self, data):
        """Save aura points data"""
        try:
            with open('aura_points.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving aura points: {e}")
            return False

    def update_user_aura(self, user_id: str, points: int):
        """Update user's aura points"""
        aura_data = self.load_aura_points()
        if str(user_id) not in aura_data:
            aura_data[str(user_id)] = 0
        aura_data[str(user_id)] += points
        return self.save_aura_points(aura_data), aura_data[str(user_id)]

    def apply_loser_penalty(self, user_id: str):
        """Apply aura point penalty for claiming a loser card"""
        penalty = random.randint(500, 1000)
        success, new_balance = self.update_user_aura(user_id, -penalty)
        return success, penalty, new_balance

    async def process_claim_queue(self, ctx, message, selected_characters, end_time):
        """Process claims from the queue"""
        claimed_characters = set()
        
        while datetime.now() < end_time:
            try:
                # Wait for the next claim with timeout
                timeout = (end_time - datetime.now()).total_seconds()
                if timeout <= 0:
                    break
                    
                try:
                    claim_data = await asyncio.wait_for(
                        self.claim_queue.get(),
                        timeout=timeout
                    )
                    
                    # Fix the unpacking of claim_data
                    reaction = claim_data['reaction']
                    user = claim_data['user']
                    
                    emoji = str(reaction.emoji)
                    emoji_index = self.number_emojis.index(emoji)

                    if emoji_index in claimed_characters:
                        await ctx.send(
                            f"{user.mention} That card has already been claimed!",
                            delete_after=5
                        )
                        continue

                    can_claim, remaining_time = self.can_user_claim(user.id)
                    if not can_claim:
                        minutes, seconds = divmod(remaining_time.total_seconds(), 60)
                        await ctx.send(
                            f"{user.mention} Cooldown: {int(minutes)}m {int(seconds)}s remaining",
                            delete_after=10
                        )
                        continue

                    character = selected_characters[emoji_index]
                    if character is None:
                        continue

                    card_path = await self.generate_card(character)
                    
                    if card_path and os.path.exists(card_path):
                        try:
                            penalty_text = ""
                            if character['type'] == 'loser':
                                success, penalty, new_balance = self.apply_loser_penalty(str(user.id))
                                if success:
                                    penalty_text = f"\nPenalty: -{penalty:,} points (New balance: {new_balance:,})"

                            new_count = self.update_user_claim(user.id, character)
                            await ctx.send(
                                f"{user.mention} claimed {character['name']} ({character['type']}) #{character['id']} [×{new_count}]{penalty_text}",
                                file=discord.File(card_path)
                            )
                            
                            os.remove(card_path)
                            claimed_characters.add(emoji_index)
                            selected_characters[emoji_index] = None

                        except Exception as e:
                            self.logger.error(f"Error sending claim message: {e}")
                            continue
                        finally:
                            # Mark task as done only once per iteration
                            self.claim_queue.task_done()

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing claim from queue: {e}")
                    continue

            except Exception as e:
                self.logger.error(f"Error in claim processing loop: {e}")
                continue

        # Clear any remaining items in the queue
        try:
            while not self.claim_queue.empty():
                await self.claim_queue.get()
                self.claim_queue.task_done()
        except Exception as e:
            self.logger.error(f"Error clearing claim queue: {e}")

    async def handle_reaction(self, reaction, user):
        """Handle incoming reactions"""
        if user.bot or str(reaction.emoji) not in self.number_emojis:
            return

        message_id = reaction.message.id
        if message_id not in self.claim_tasks:
            return

        await self.claim_queue.put({
            'reaction': reaction,
            'user': user
        })

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def drop(self, ctx):
        """Drop command with queued claim processing"""
        self.logger.info(f"'drop' command invoked by {ctx.author} ({ctx.author.id})")
        
        if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
            return
        if not ctx.channel.permissions_for(ctx.guild.me).attach_files:
            await ctx.send("I need permission to attach files to drop cards!")
            return

        try:
            probabilities = {'normal': 0.80, 'legendary': 0.15, 'loser': 0.05}
            selected_characters = []
            excluded_ids = []
            
            for _ in range(3):
                character = self.get_weighted_random_character(probabilities, excluded_ids)
                if character:
                    selected_characters.append(character)
                    excluded_ids.append(character['id'])
                else:
                    selected_characters.append({
                        'id': '0000',
                        'name': 'Unknown',
                        'type': 'normal',
                        'image_url': 'placeholder.png',
                        'description': 'Mystery character'
                    })

            drop_image_path = await self.generate_drop_image(selected_characters)
            
            message = await ctx.send(
                "New characters available! React with a number to claim one!",
                file=discord.File(drop_image_path)
            )

            for emoji in self.number_emojis:
                await message.add_reaction(emoji)

            end_time = datetime.now() + timedelta(seconds=self.drop_timeout)
            
            # Start the claim processing task
            claim_task = asyncio.create_task(
                self.process_claim_queue(ctx, message, selected_characters, end_time)
            )
            self.claim_tasks[message.id] = claim_task

            def reaction_check(reaction, user):
                return (
                    user != self.bot.user 
                    and reaction.message.id == message.id 
                    and str(reaction.emoji) in self.number_emojis
                )

            while datetime.now() < end_time:
                try:
                    timeout = (end_time - datetime.now()).total_seconds()
                    if timeout <= 0:
                        break

                    reaction, user = await self.bot.wait_for(
                        'reaction_add',
                        timeout=timeout,
                        check=reaction_check
                    )

                    # Remove the user's reaction
                    await message.remove_reaction(reaction, user)
                    
                    # Process the reaction
                    await self.claim_queue.put({
                        'reaction': reaction,
                        'user': user
                    })

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing reaction: {e}")
                    continue

            # Cleanup after timeout
            try:
                await claim_task
                del self.claim_tasks[message.id]
                await message.clear_reactions()
                await message.edit(content="Drop expired", attachments=[])
                if os.path.exists(drop_image_path):
                    os.remove(drop_image_path)
            except Exception as e:
                self.logger.error(f"Error cleaning up drop: {e}")

        except Exception as e:
            self.logger.error(f"Error in drop command: {e}")
            await self.handle_drop_failure(ctx, e)

    def validate_character(self, character: dict) -> bool:
        """Validate character data structure"""
        required_fields = ['id', 'name', 'type', 'image_url']
        return all(field in character for field in required_fields)

    def get_weighted_random_character(self, probabilities, excluded_ids=[]):
        """Get a random character based on type probabilities"""
        types = list(probabilities.keys())
        weights = list(probabilities.values())
        selected_type = random.choices(types, weights=weights, k=1)[0]
        
        characters_of_type = [
            c for c in self.characters 
            if c['type'] == selected_type 
            and c['id'] not in excluded_ids
            and self.validate_character(c)
        ]
        
        if not characters_of_type:
            self.logger.warning(f"No characters of type '{selected_type}' available for selection.")
            return None
        
        selected_character = random.choice(characters_of_type)
        self.logger.debug(f"Selected character: {selected_character['name']} (ID: {selected_character['id']})")
        return selected_character

    def load_admin_users(self) -> List[str]:
        """Load authorized admins from JSON file"""
        try:
            with open('authorized_users.json', 'r') as f:
                data = json.load(f)
                admins = data.get('authorized_user_ids', [])
                self.logger.info(f"Loaded admin users: {admins}")
                return admins
        except Exception as e:
            self.logger.error(f"Error loading authorized admins: {e}")
            return []

    async def cog_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, discord.Forbidden) and error.code == 60003:
            await ctx.send("❌ **2FA Required**\nThis action requires Two-Factor Authentication to be enabled on the server.")
            self.logger.warning(f"2FA required for command {ctx.command}")
        elif isinstance(error, commands.BotMissingPermissions):
            missing_perms = '\n'.join([f'• {perm.replace("_", " ").title()}' for perm in error.missing_permissions])
            await ctx.send(f"❌ I need the following permissions to work properly:\n{missing_perms}")

        elif isinstance(error, commands.MissingPermissions):
            missing_perms = '\n'.join([f'• {perm.replace("_", " ").title()}' for perm in error.missing_permissions])
            await ctx.send(f" You need the following permissions:\n{missing_perms}")

        elif isinstance(error, discord.Forbidden):
            if error.code == 60003:
                await ctx.send("❌ 2FA (Two-Factor Authentication) is required for this action.")
            else:
                await ctx.send(f"❌ I don't have permission to perform that action.\nError: {error.text}")

        elif isinstance(error, discord.HTTPException):
            if error.code == 50013:
                await ctx.send("❌ I don't have proper permissions to perform that action.")
            elif error.code == 50007:
                await ctx.send("❌ I cannot send messages to this user. They might have DMs disabled.")
            else:
                await ctx.send(f"❌ An HTTP error occurred: {error.text}")

        elif isinstance(error, commands.CheckFailure):
            await ctx.send("❌ You are not authorized to use these commands.")
            self.logger.warning(f"Unauthorized access attempt by {ctx.author} ({ctx.author.id})")

        else:
            self.logger.error(f"Error in command '{ctx.command}': {error}")
            error_msg = f"❌ An error occurred: {str(error)}"
            if len(error_msg) > 2000:
                error_msg = error_msg[:1997] + "..."
            await ctx.send(error_msg)

    async def handle_drop_failure(self, ctx, error):
        self.logger.error(f"Drop failed: {error}")
        await ctx.send("❌ Drop failed. Please try again later.")

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.cleanup_cooldowns.cancel()
        # Cancel any ongoing claim tasks
        for task in self.claim_tasks.values():
            task.cancel()
        self.claim_tasks.clear()
        self.save_user_data()
        self.logger.info("BrainrotDrop cog unloaded")

    def validate_image(self, image):
        """Validate that an image is usable."""
        try:
            if not isinstance(image, Image.Image):
                return False
                
            if image.size[0] <= 0 or image.size[1] <= 0:
                return False
                
            image.convert('RGBA')
            return True
        except Exception:
            return False

async def setup(bot):
    await bot.add_cog(BrainrotDrop(bot))