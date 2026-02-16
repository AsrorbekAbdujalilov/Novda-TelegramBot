from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, ReplyKeyboardMarkup, ReplyKeyboardRemove, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from services import ApiService
from config import FRONTEND_URL
import logging
import datetime
import io

logger = logging.getLogger(__name__)

api = ApiService()

# States for ConversationHandler
# Login
LOGIN_USERNAME, LOGIN_PASSWORD = range(2)
# Register
REG_USERNAME, REG_PASSWORD, REG_FIRSTNAME, REG_LASTNAME, REG_PHONE, REG_REGION, REG_BIRTHDATE = range(2, 9)
# Worker Plant
PLANT_BUCKET_ID, PLANT_WAIT_LOC, PLANT_WAIT_PHOTO = range(9, 12)

# In-memory storage for user tokens
user_tokens = {} 

# --- Helper ---
def get_user_token(user_id):
    return user_tokens.get(user_id)

def check_auth(update: Update):
    user_id = update.effective_user.id
    return user_tokens.get(user_id)

# --- Start & Menu ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with the Mini App button and main menu."""
    try:
        user = update.effective_user
        logger.info(f"Start command from {user.id}")
        
        token = get_user_token(user.id)
        auth_status = "✅ Logged In" if token else "❌ Not Logged In"

        keyboard = []
        if not token:
            keyboard.append([InlineKeyboardButton("Login", callback_data="login"), InlineKeyboardButton("Register", callback_data="register")])
        else:
            # We add Logout and Profile
            keyboard.append([InlineKeyboardButton("Logout", callback_data="logout"), InlineKeyboardButton("Profile", callback_data="profile")])
        
        # Shop
        keyboard.append([InlineKeyboardButton("Products", callback_data="products"), InlineKeyboardButton("My Cart", callback_data="cart")])
        
        # Web App
        keyboard.append([InlineKeyboardButton("Open Novda App", web_app=WebAppInfo(url=FRONTEND_URL))])
        
        # Info
        keyboard.append([InlineKeyboardButton("Tips", callback_data="tips"), InlineKeyboardButton("Pricing", callback_data="pricing")])
        
        # Worker - we can't easily validte worker status without /me check every time.
        # We'll just add the button if logged in, ensuring they can access the feature if they have permissions.
        if token:
             keyboard.append([InlineKeyboardButton("Worker: Plant Tree", callback_data="plant_tree")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Hello {user.first_name}! Welcome to Novda Bot.\nStatus: {auth_status}\n\nUse the menu below:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in start: {e}", exc_info=True)
        await update.message.reply_text("Error starting bot.")

async def menu_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles main menu buttons."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "products":
        await show_products(update, context)
    elif data == "cart":
        await show_cart(update, context)
    elif data == "profile":
        await show_profile(update, context)
    elif data == "tips":
        await update.effective_message.reply_text("🌱 *Planting Tips*:\n1. Choose sunny locations.\n2. Water regularly.\n3. Protect from pests.\n4. Use organic fertilizer.", parse_mode='Markdown')
    elif data == "pricing":
         await update.effective_message.reply_text("💰 *Pricing*:\nSmall Tree: $10\nMedium Tree: $25\nBig Tree: $50\n\n_Prices subject to change._", parse_mode='Markdown')
    elif data == "logout":
        await logout_handler(update, context)

# --- Authentication ---

# Login
async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter your username:")
    return LOGIN_USERNAME

async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['login_username'] = update.message.text
    await update.message.reply_text("Please enter your password:")
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = context.user_data['login_username']
    password = update.message.text
    
    result = api.login(username, password)
    
    if result and 'access' in result:
        user_id = update.effective_user.id
        user_tokens[user_id] = result['access']
        await update.message.reply_text("Login successful!")
        await start(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Login failed. Try again with /login.")
        return ConversationHandler.END

async def logout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    token = user_tokens.get(user_id)
    if token:
        api.logout(token)
        if user_id in user_tokens:
            del user_tokens[user_id]
        await update.effective_message.reply_text("Logged out successfully.")
    else:
        await update.effective_message.reply_text("You are not logged in.")
    
    # We can trigger start to show login buttons, but message is enough.

# Registration
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration - Step 1/7\nEnter your desired username:")
    return REG_USERNAME

async def reg_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_username'] = update.message.text
    await update.message.reply_text("Step 2/7\nEnter your password:")
    return REG_PASSWORD

async def reg_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_password'] = update.message.text
    await update.message.reply_text("Step 3/7\nEnter your First Name:")
    return REG_FIRSTNAME

async def reg_firstname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_firstname'] = update.message.text
    await update.message.reply_text("Step 4/7\nEnter your Last Name:")
    return REG_LASTNAME

async def reg_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_lastname'] = update.message.text
    await update.message.reply_text("Step 5/7\nEnter your Phone Number:")
    return REG_PHONE

async def reg_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_phone'] = update.message.text
    await update.message.reply_text("Step 6/7\nEnter your Region (e.g. Tashkent, Samarkand):")
    return REG_REGION

async def reg_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_region'] = update.message.text
    await update.message.reply_text("Step 7/7\nEnter your Birth Date (YYYY-MM-DD):")
    return REG_BIRTHDATE

async def reg_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dob = update.message.text
    data = {
        "username": context.user_data['reg_username'],
        "password": context.user_data['reg_password'],
        "FirstName": context.user_data['reg_firstname'],
        "LastName": context.user_data['reg_lastname'],
        "phoneNumber": context.user_data['reg_phone'],
        "region": context.user_data['reg_region'], 
        "birthDate": dob,
        "email": "" 
    }
    
    res = api.register(data)
    if res and 'access' in res:
        user_id = update.effective_user.id
        user_tokens[user_id] = res['access']
        await update.message.reply_text("Registration Successful! You are now logged in.")
        await start(update, context)
    else:
        err_msg = "Registration Failed."
        if res and 'error' in res: err_msg += f" {res['error']}"
        elif res: err_msg += f" {res}"
        await update.message.reply_text(err_msg)
        
    return ConversationHandler.END


# --- Shop Handlers ---

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = api.get_products()
    target = update.effective_message
    
    if not products:
        await target.reply_text("No products found.")
        return

    for p in products[:5]:
        name = p.get('tree', {}).get('name_en', 'Tree')
        price = p.get('price', '0')
        desc = p.get('tree', {}).get('desc_en', '')
        
        msg = f"🌳 *{name}*\nPrice: ${price}\n{desc}"
        
        keyboard = [[InlineKeyboardButton("Add to Cart", callback_data=f"add_{p['id']}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await target.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)

async def add_to_cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    token = check_auth(update)
    if not token:
        await query.message.reply_text("Please login first.")
        return

    _, product_id = query.data.split('_')
    res = api.add_to_cart(token, product_id)
    if res:
        await query.message.reply_text("Added to cart! 🛒")
    else:
        await query.message.reply_text("Failed to add.")

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = check_auth(update)
    target = update.effective_message
    
    if not token:
        await target.reply_text("Please login first.")
        return

    items = api.get_my_trees(token)
    if not items:
        await target.reply_text("Your cart is empty.")
        return

    msg = "🛒 *Your Cart*\n\n"
    total_price = 0
    
    for item in items:
        p_name = item['product']['tree'].get('name_en', 'Tree')
        price = float(item['product'].get('price', 0))
        qty = item.get('count', 1)
        line_total = price * qty
        total_price += line_total
        
        msg += f"- {p_name} (x{qty}) - ${line_total}\n"

    msg += f"\n*Total: ${total_price}*"
    
    keyboard = [[InlineKeyboardButton("Checkout", callback_data="checkout")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await target.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)

async def checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    token = check_auth(update)
    if not token:
        await query.message.reply_text("Login required.")
        return
        
    res = api.checkout(token)
    if res:
        await query.message.reply_text("✅ Order placed successfully!")
    else:
        await query.message.reply_text("Checkout failed.")

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = check_auth(update)
    target = update.effective_message
    if not token:
        await target.reply_text("Login required.")
        return
        
    me = api.get_me(token)
    if me:
        name = me.get('name', 'User')
        region = me.get('region', 'Unknown')
        phone = me.get('phoneNumber', '')
        await target.reply_text(f"👤 *Profile*\nName: {name}\nPhone: {phone}\nRegion: {region}", parse_mode='Markdown')
    else:
        await target.reply_text("Could not load profile.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


# --- Worker Planting Flow ---
async def plant_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = check_auth(update)
    # We allow entering but later api call will fail if not worker content permissions
    if not token:
         await update.effective_message.reply_text("Login required.")
         return ConversationHandler.END

    await update.effective_message.reply_text("🌱 Worker: Planting Tree\nPlease enter the Bucket ID you are planting:")
    return PLANT_BUCKET_ID 

async def plant_bucket_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['plant_bucket_id'] = update.message.text
    await update.message.reply_text("Send me the GPS location of the tree (Attach Location).")
    return PLANT_WAIT_LOC

async def plant_location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.location:
        await update.message.reply_text("Please send a valid location attachment.")
        return PLANT_WAIT_LOC
    
    loc = update.message.location
    context.user_data['plant_lat'] = loc.latitude
    context.user_data['plant_lon'] = loc.longitude
    
    await update.message.reply_text("Now send a photo of the planted tree.")
    return PLANT_WAIT_PHOTO

async def plant_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
         await update.message.reply_text("Please send a photo.")
         return PLANT_WAIT_PHOTO
         
    photo_file = await update.message.photo[-1].get_file()
    
    f = io.BytesIO()
    await photo_file.download_to_memory(f)
    f.seek(0)
    
    token = get_user_token(update.effective_user.id)
    
    data = {
        "bucket": context.user_data['plant_bucket_id'],
        "latitude": context.user_data['plant_lat'],
        "lognitude": context.user_data['plant_lon'], 
        "plantingDate": datetime.datetime.now().isoformat()
    }
    
    files = {'images': ('planted.jpg', f, 'image/jpeg')}
    
    res = api.plant_tree(token, data, files)
    
    if res:
        await update.message.reply_text("Tree planting recorded successfully! 🌳✅")
    else:
        await update.message.reply_text("Failed to record planting. Check Bucket ID or permissions.")
        
    return ConversationHandler.END
