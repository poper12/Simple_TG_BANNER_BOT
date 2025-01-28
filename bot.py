import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Bot configuration
api_id = ""
api_hash = ""
bot_token = ""
forwarding_channel = "" 
# Initialize Pyrogram client
app = Client("banner_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Store user state
user_states = {}

# Timeout duration in seconds
TIMEOUT_DURATION = 60

# Function to create banner
def create_banner(data):
    try:
        user_id = data["user_id"]
        main_image_path = data["main_image"]
        background_image_path = data["background_image"]
        title = data["title"]
        media_type = data["media_type"]
        season = data["season"]
        episode = data["episode"]
        score = data["score"]
        rating = data["rating"]

        # Load images
        main_image = Image.open(main_image_path).convert("RGBA")
        background_image = Image.open(background_image_path).convert("RGBA")

        # Resize background and apply blur
        background_image = background_image.resize((1280, 720))
        background_image = background_image.filter(ImageFilter.GaussianBlur(8))

        # Create a blank image for the banner
        banner = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        banner.paste(background_image, (0, 0))

        # Resize and create square-round shape for main image
        main_image = main_image.resize((500, 500))
        mask = Image.new("L", main_image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, 500, 500), radius=70, fill=255)
        main_image = Image.composite(main_image, Image.new("RGBA", main_image.size), mask)

        # Paste the main image onto the banner
        banner.paste(main_image, (640, 110), main_image)

        # Add text to the banner
        draw = ImageDraw.Draw(banner)
        font = ImageFont.truetype("FenomenSans-SCNSemiBold.ttf", 40)

        # Define text colors
        text_color = (0, 0, 0)
        shadow_color = (50, 50, 50)
        outline_color = (255, 255, 255)

        # Text lines
        text_lines = [
            f"{title}",
            f"Type: {media_type}",
            f"Season: {season}",
            f"Episode: {episode}",
            f"Score: {score}",
            f"Rating: {rating}",
        ]

        y_offset = (720 - len(text_lines) * 50) // 2 - 50

        for line in text_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            x_position = (1280 - width) // 2 - 350

            # Draw shadow
            draw.text((x_position + 4, y_offset + 4), line, font=font, fill=shadow_color)

            # Draw white outline
            outline_width = 2
            for x_offset in [-outline_width, 0, outline_width]:
                for y_offset_outline in [-outline_width, 0, outline_width]:
                    draw.text(
                        (x_position + x_offset, y_offset + y_offset_outline),
                        line,
                        font=font,
                        fill=outline_color,
                    )

            # Draw main text
            draw.text((x_position, y_offset), line, font=font, fill=text_color)
            y_offset += height + 40

        # Save the final image
        output_path = f"banner_{user_id}.png"
        banner.save(output_path)
        return output_path
    except Exception as e:
        return f"Error: {e}"


# Clean up user data and files
async def cleanup_user_data(user_id):
    if user_id in user_states:
        user_data = user_states[user_id]
        for file in ["main_image", "background_image"]:
            if file in user_data and os.path.exists(user_data[file]):
                os.remove(user_data[file])
        del user_states[user_id]


# /start command handler
@app.on_message(filters.command("start") & filters.private)
async def welcome_user(client, message):
    welcome_text = (
        f"<blockquote><b>Welcome to the Banner Bot!\n\n"
        f"I'm just a bot created by [RAHAT](https://t.me/r4h4t_69).\n\n"
        f"You can use me to create custom banners.\n\n"
        f"To get started, use the /banner command.</b></blockquote>"
    )
    await message.reply_text(welcome_text, disable_web_page_preview=True)


# Handler for /banner command
@app.on_message(filters.command("banner") & filters.private)
async def start_banner_process(client, message):
    user_states[message.from_user.id] = {"step": "main_image", "user_id": message.from_user.id}
    await message.reply_text(f"<blockquote>Please send the **main image** for the banner.</blockquote>")
    await asyncio.sleep(TIMEOUT_DURATION)
    if message.from_user.id in user_states and user_states[message.from_user.id]["step"] == "main_image":
        await cleanup_user_data(message.from_user.id)
        await message.reply_text(f"<blockquote>Timeout! Please start again with /banner.</blockquote>")


# Handle subsequent inputs
@app.on_message(filters.private)
async def handle_inputs(client, message):
    user_id = message.from_user.id

    # Check if the user is in an active state
    if user_id not in user_states:
        return

    state = user_states[user_id]

    # Main image
    if state["step"] == "main_image":
        if not message.photo:
            await message.reply_text(f"<blockquote>Please send a valid image.</blockquote>")
            return

        main_image = await message.download()
        state["main_image"] = main_image
        state["step"] = "background_image"
        await message.reply_text(f"<blockquote>Please send the **background image** for the banner.</blockquote>")
        await asyncio.sleep(TIMEOUT_DURATION)
        if user_id in user_states and user_states[user_id]["step"] == "background_image":
            await cleanup_user_data(user_id)
            await message.reply_text(f"<blockquote>Timeout! Please start again with /banner.</blockquote>")
    # Add remaining steps with similar timeout logic...

# Run the bot
if __name__ == "__main__":
    app.run()
