from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Bot configuration
#Add Yours
api_id = ""
api_hash = ""
bot_token = ""

# Initialize Pyrogram client
app = Client("banner_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Store user state
user_states = {}

# Function to create thumbnail
def create_thumbnail(data):
    try:
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

        # Create a blank image for the thumbnail
        thumbnail = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        thumbnail.paste(background_image, (0, 0))

        # Resize and create square-round shape for main image
        main_image = main_image.resize((500, 500))
        mask = Image.new("L", main_image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, 500, 500), radius=70, fill=255)
        main_image = Image.composite(main_image, Image.new("RGBA", main_image.size), mask)

        # Paste the main image onto the thumbnail
        thumbnail.paste(main_image, (640, 110), main_image)

        # Add text to the thumbnail
        draw = ImageDraw.Draw(thumbnail)
        font = ImageFont.truetype("/storage/emulated/0/Pahe/FenomenSans-SCNSemiBold.ttf", 40)

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
        output_path = "thumbnail.png"
        thumbnail.save(output_path)
        return output_path
    except Exception as e:
        return f"Error: {e}"


# Handler for /thumbnail command
@app.on_message(filters.command("thumbnail") & filters.private)
async def start_thumbnail_process(client, message):
    user_states[message.from_user.id] = {"step": "main_image"}
    await message.reply_text("Please send the **main image** for the thumbnail.")


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
            await message.reply_text("Please send a valid image.")
            return

        main_image = await message.download()
        state["main_image"] = main_image
        state["step"] = "background_image"
        await message.reply_text("Please send the **background image** for the thumbnail.")

    # Background image
    elif state["step"] == "background_image":
        if not message.photo:
            await message.reply_text("Please send a valid image.")
            return

        background_image = await message.download()
        state["background_image"] = background_image
        state["step"] = "title"
        await message.reply_text("What is the **title** of the thumbnail?")

    # Title
    elif state["step"] == "title":
        state["title"] = message.text
        state["step"] = "media_type"
        await message.reply_text("What is the **media type** (e.g., Donghua, Anime, etc.)?")

    # Media type
    elif state["step"] == "media_type":
        state["media_type"] = message.text
        state["step"] = "season"
        await message.reply_text("What is the **season**?")

    # Season
    elif state["step"] == "season":
        state["season"] = message.text
        state["step"] = "episode"
        await message.reply_text("What is the **episode number**?")

    # Episode
    elif state["step"] == "episode":
        state["episode"] = message.text
        state["step"] = "score"
        await message.reply_text("What is the **score** (e.g., 8.89)?")

    # Score
    elif state["step"] == "score":
        state["score"] = message.text
        state["step"] = "rating"
        await message.reply_text("What is the **rating** (e.g., 89%)?")

    # Rating
    elif state["step"] == "rating":
        state["rating"] = message.text

        # Generate thumbnail
        thumbnail_path = create_thumbnail(state)

        if isinstance(thumbnail_path, str) and thumbnail_path.endswith(".png"):
            await message.reply_photo(thumbnail_path, caption="Here is your thumbnail!")
        else:
            await message.reply_text(f"Failed to create thumbnail: {thumbnail_path}")

        # Clear user state
        del user_states[user_id]


# Run the bot
if __name__ == "__main__":
    app.run()
