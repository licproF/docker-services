import os
import sys
import time
import requests
import logging
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont

image = '/tmp/image.png'
owner = int(os.getenv("owner"))
token = os.getenv("token")
api_key = os.getenv("api_key")
veid = os.getenv("veid")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

if os.path.exists(image):
    os.remove(image)

def bwh_info():
    try:
        response = requests.get(f'https://api.64clouds.com/v1/getLiveServiceInfo?veid={veid}&api_key={api_key}')
        LiveServiceInfo = response.json()

        img = Image.new('RGB', (600, 380), '#FFFFFF')
        d = ImageDraw.Draw(img)

        d.rounded_rectangle(
            [(5,5), (595,375)],
            fill= '#FFFFFF',
            outline='#e5e5e5',
            width=1,
            radius=4
        )

        title_bar = [(15,15), (585,45)]
        d.rounded_rectangle(
            title_bar,
            fill= '#f9f9f9',
            outline='#e5e5e5',
            width=1,
            radius=4
        )

        title_text = f'{LiveServiceInfo.get("live_hostname", "")}   [{(LiveServiceInfo.get("plan", "")).upper()}]   {(LiveServiceInfo.get("vm_type", "")).upper()}'
        title_box = d.textbbox((0, 0), title_text, font=ImageFont.truetype('SourceSans3-Bold.ttf', 18))

        title_text_w = title_box[2] - title_box[0]
        title_text_h = title_box[3] - title_box[1]

        x = title_bar[0][0] + (580 - title_text_w) / 2
        y = title_bar[0][1] + (25 - title_text_h) / 2

        d.text((x, y), title_text, fill='#000000', font=ImageFont.truetype('SourceSans3-Bold.ttf', 18))

        def draw_info_title(text, position, font, font_size, text_color):
            x = 15
            y = title_bar[1][1] + position
            bbox = d.textbbox((0, 0), text, font=ImageFont.truetype(font, font_size))
            y += (20 - (bbox[3] - bbox[1])) / 2
            d.text((x, y), text, fill=text_color, font=ImageFont.truetype(font, font_size))

        def draw_info(text, position, font, font_size, text_color):
            x = 190 
            y = title_bar[1][1] + position
            bbox = d.textbbox((0, 0), text, font=ImageFont.truetype('SourceSans3-Medium.ttf', 15))
            y += (20 - (bbox[3] - bbox[1])) / 2
            d.text((x, y), text, fill=text_color, font=ImageFont.truetype('SourceSans3-Medium.ttf', 15))

        def draw_bar(part, whole, position):
            img_percent = Image.new('RGB', (101, 11), color='white')
            draw = ImageDraw.Draw(img_percent)
            green_length = int(( part / whole ) * 100 / 100 * 100)
            draw.rectangle([0, 0, 100, 10], outline='#00a000')
            draw.rectangle([0, 0, green_length, 10], fill='#00a000')

            img_percent_x = 190 
            img_percent_y = title_bar[1][1] + position
            img.paste(img_percent, (img_percent_x, img_percent_y))

        def anonymize_ip(ip_address):
            parts = ip_address.split('.')
            return parts[0] + '.' + parts[1] + '.*.*'

        draw_info_title("Physical Location:", 10, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info_title("Public IP address:", 40, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info_title("Status:", 70, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info_title("RAM:", 110, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info_title("SWAP:", 150, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info_title("Disk usage (/):", 190, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info_title("Bandwidth usage:", 230, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info_title(f'Resets: {time.strftime("%Y-%m-%d", time.localtime(LiveServiceInfo.get("data_next_reset", 0)))}', 248, 'SourceSans3-Medium.ttf', 13, '#a0a0a0')
        draw_info_title("Operating system:", 270, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info_title("Hostname:", 300, 'SourceSans3-Medium.ttf', 15, '#000000')


        draw_info(f'{LiveServiceInfo.get("node_location", "")}    Node ID: {LiveServiceInfo.get("node_alias", "")}    VPS ID: {str(LiveServiceInfo.get("veid", ""))[:-4]}****', 10, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info(f'{anonymize_ip((LiveServiceInfo.get("ip_addresses", ""))[0])}', 40, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info(f'{LiveServiceInfo.get("ve_status", "")}, LA: {LiveServiceInfo.get("load_average", "")}', 70, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info(f'{round((LiveServiceInfo.get("plan_ram", 0) / 1024 - LiveServiceInfo.get("mem_available_kb", 0)) / 1024, 2)}/{round(LiveServiceInfo.get("plan_ram", 0) / 1024 / 1024)} MB', 120, 'SourceSans3-Medium.ttf', 13, '#a0a0a0')
        draw_info(f'{round((LiveServiceInfo.get("swap_total_kb", 0) - LiveServiceInfo.get("swap_available_kb", 0)) / 1024, 2)}/{round(LiveServiceInfo.get("swap_total_kb", 0) / 1024)} MB', 160, 'SourceSans3-Medium.ttf', 13, '#a0a0a0')
        draw_info(f'{round(LiveServiceInfo.get("ve_used_disk_space_b", 0) / 1024 / 1024 / 1024, 2)}/{LiveServiceInfo.get("ve_disk_quota_gb", 0)} GB', 200, 'SourceSans3-Medium.ttf', 13, '#a0a0a0')
        monthly_data_multiplier = LiveServiceInfo.get('monthly_data_multiplier', 1)
        draw_info(f'{round(LiveServiceInfo.get("data_counter", 0) * monthly_data_multiplier / 1024 / 1024 / 1024, 2)}/{round(LiveServiceInfo.get("plan_monthly_data", 0) / 1024 / 1024 / 1024, 2)} GB', 240, 'SourceSans3-Medium.ttf', 13, '#a0a0a0')
        draw_info(f'{LiveServiceInfo.get("os", "")}', 270, 'SourceSans3-Medium.ttf', 15, '#000000')
        draw_info(f'{LiveServiceInfo.get("hostname", "")}', 300, 'SourceSans3-Medium.ttf', 15, '#000000')

        draw_bar(LiveServiceInfo.get("plan_ram", 0) / 1024 - LiveServiceInfo.get("mem_available_kb", 0), LiveServiceInfo.get("plan_ram", 0) / 1024, 110)
        draw_bar(LiveServiceInfo.get("swap_total_kb", 0) - LiveServiceInfo.get("swap_available_kb", 0), LiveServiceInfo.get("swap_total_kb", 0), 150)
        draw_bar(LiveServiceInfo.get("ve_used_disk_space_b", 0), int(LiveServiceInfo.get("ve_disk_quota_gb", 0)) * 1024 * 1024 * 1024, 190)
        draw_bar(LiveServiceInfo.get("data_counter", 0) * monthly_data_multiplier, LiveServiceInfo.get("plan_monthly_data", 0), 230)

        img.save(image,'PNG')
    except:
        return

async def bwh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bwh_info()
    await update.message.reply_photo(image)

def main() -> None:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler(command="bwh", callback=bwh, filters=filters.User(owner)))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()