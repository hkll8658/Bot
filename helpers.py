import uuid
import config

LANG = {}  # user_id: 'en' or 'hi'

def set_lang(user_id, lang):
    LANG[user_id] = lang

def generate_paytm_qr(amount):
    # Integrate your Paytm API here. For demo:
    paytm_id = str(uuid.uuid4())
    img_path = "paytm_qr_placeholder.png"  # Generate QR and save image
    return img_path, paytm_id

STORAGE = {
    "WallHack": {"Week": [], "Month": [], "Season": []},
    "ESP/AimBot": {"Day": [], "3 Day": [], "Week": [], "Month": [], "Season": []},
}
MODS = {
    # product: {duration: (file_id, file_name)}
}

def store_key(product, duration, key):
    if product not in STORAGE:
        STORAGE[product] = {}
    if duration not in STORAGE[product]:
        STORAGE[product][duration] = []
    STORAGE[product][duration].append(key)

def get_keys():
    return STORAGE

def delete_key(product, duration, key):
    if key in STORAGE.get(product, {}).get(duration, []):
        STORAGE[product][duration].remove(key)

def store_mod_file(product, duration, file_id, file_name):
    if product not in MODS:
        MODS[product] = {}
    MODS[product][duration] = (file_id, file_name)

def get_mod_file(product, duration):
    keys = STORAGE.get(product, {}).get(duration, [])
    mod_info = MODS.get(product, {}).get(duration)
    if not keys or not mod_info:
        return None, None, None
    key = keys[0]
    file_id, file_name = mod_info
    mod_caption = f"Mod/Loader: {product}\nKey: `{key}`\nFile: {file_name}"
    return file_id, key, mod_caption

def owner_notify(context, user, product, duration, price):
    owner_id = config.OWNER_ID
    msg = (
        f"User {user.full_name} ({user.username}) purchased {product} ({duration}) for ₹{price}.\n"
        f"Chat ID: {user.id}"
    )
    context.bot.send_message(owner_id, msg)

def get_invoice(user, purchase, key):
    return (
        f"*Invoice*\n\n"
        f"Name: {user.full_name}\n"
        f"Chat ID: `{user.id}`\n"
        f"Username: @{user.username}\n"
        f"Product: {purchase['product']}\n"
        f"Duration: {purchase['duration']}\n"
        f"Amount: ₹{purchase['price']}\n"
        f"Payment Mode: Paytm\n"
        f"Key: `{key}`\n"
    )

def is_owner(user_id):
    return user_id == config.OWNER_ID