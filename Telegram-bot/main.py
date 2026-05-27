from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
    )

# Import telegram en Update is de context window
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
import os
# Telegram.ext = de extensie module | bevat tools om je bot te bouwen
# ApplicationBuilder = bouwt de bot app | CommandHandler = Luistert naar commands zoals /btc of /start | ContextTypes = geeft toegang tot context van de chat
import requests  # request = HTTP requests naar URLs | Communicatie tussen apps en websites
load_dotenv()
TOKEN = os.getenv('TOKEN')



STAD = 0
METHODE = 1
user_data = {}
METHODES = {"hanafi": 13, "shafi": 4, "maliki": 8, "hanbali": 4}
# keyboard = lijst van rijen met knoppen
keyboard = [
    [KeyboardButton("💰 BTC Prijs"), KeyboardButton("🕌 Namaz Tijden")],
    [KeyboardButton("📍 Stel Stad In"), KeyboardButton("🕋 Stel Madhab In")]
]
# resize past de grote van het scherm aan
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def setmethod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        methode = context.args[0].lower()
        if methode in METHODES:
            user_data[update.effective_user.id] = user_data.get(
                update.effective_user.id, {}
            )
            user_data[update.effective_user.id]["methode"] = METHODES[methode]
            await update.message.reply_text(f"Madhab opgeslagen: {methode}")
        else:
            await update.message.reply_text("Kies: hanafi, shafi, maliki, hanbali")
    else:
        await update.message.reply_text("Gebruik: /setmethod hanafi")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # async = red je bot vn vastlopen | update: Update = Bericht dat binnen komt | Context: ContextTypes.DEFAULT_TYPE = extra info van de chat

    await update.message.reply_text(
        "Selam! Ik ben je persoonlijke assistent voor BTC info en Namaz. Gebruikt /btc of /namaz om te starten.",
        reply_markup=reply_markup
    )  # await = wacht totdat 'dit' klaar is voordat je doorgaat | .reply_text() = stuur bericht terug naar gebruiker

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tekst = update.message.text

    if tekst == "💰 BTC Prijs":
        await btc(update, context)
    elif tekst == "🕌 Namaz Tijden":
        await namaz(update, context)
    elif tekst == "📍 Stel Stad In":
        await update.message.reply_text("Gebruik: /setlocation Nijmegen")
    elif tekst == "🕋 Stel Madhab In":
        await update.message.reply_text("Gebruik: /setmethod hanafi")

async def setlocation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        stad = " ".join(context.args)
        user_data[update.effective_user.id] = {"stad": stad}
        await update.message.reply_text(f"Stad opgeslagen: {stad}")
    else:
        await update.message.reply_text("Gebruik: /setlocation Nijmegen")


async def stuur_gebedstijden(update: Update, stad: str):
    user_id = update.effective_user.id
    methode = user_data.get(user_id, {}).get("methode", 13)
    try:
        response = requests.get(
            f"https://api.aladhan.com/v1/timingsByCity?city={stad}&country=NL&method=13"
        )
        data = response.json()
        tijden = data["data"]["timings"]
        bericht = (
            f"Gebedstijden voor {stad}:\n"
            f"Fajr: {tijden['Fajr']}\n"
            f"Dhuhr: {tijden['Dhuhr']}\n"
            f"Asr: {tijden['Asr']}\n"
            f"Maghrib: {tijden['Maghrib']}\n"
            f"Isha: {tijden['Isha']}"
        )
        await update.message.reply_text(bericht)
    except Exception:
        await update.message.reply_text("Stad niet gevonden.")


async def namaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data and "stad" in user_data[user_id]:
        stad = user_data[user_id]["stad"]
        await stuur_gebedstijden(update, stad)
        return ConversationHandler.END
    else:
        await update.message.reply_text("In welke stad ben je?")
        return STAD


async def get_namaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stad = update.message.text
    user_data[update.effective_user.id] = {"stad": stad}
    await stuur_gebedstijden(update, stad)
    return ConversationHandler.END


async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):

    response = requests.get("https://api.coinbase.com/v2/prices/BTC-EUR/spot")
    if response.status_code != 200 or not response.text:
        await update.message.reply_text("BTC prijs ophalen mislukt.")
        return

    data = response.json()
    prijs = data["data"]["amount"]
    await update.message.reply_text(f"BTC prijs: €{prijs}")
    # simpel taal: Response = reactie die de bot geeft nadat gebruiker /btc typt
    #


app = ApplicationBuilder().token(TOKEN).build()
# Applicationbuilder = starten van bot builder
# .token(TOKEN) = token geven aan bot zonder token te hoeven overschrijven
# .build() = "bouw de app"
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("btc", btc))
app.add_handler(CommandHandler("setlocation", setlocation))
app.add_handler(CommandHandler("setmethod", setmethod))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
# add_handler = voeg een luisteraar toe aan jouw bot
# CommandHandler("") = wat de bot gaat doen | in dit geval bij /start voert de bot de command start uit
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("namaz", namaz)],
    states={STAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_namaz)]},
    fallbacks=[],
)
app.add_handler(conv_handler)
app.run_polling()


